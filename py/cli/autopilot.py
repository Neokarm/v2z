import logging
import typer
import config
import cli.vmware
import cli.zcompute
import cli.v2v
import v2v.disk_inspect
from linux_tools.chmod import read_write_everyone

app = typer.Typer()

v2v_prefix = "v2v_"


@app.command(no_args_is_help=True)
def migrate_vhdx_via_block_device(vm_name: str, cpu: int, ram_gb: int,
                                  boot_vhd_path: str,
                                  temp_dir: str,
                                  uefi: bool = False,
                                  storage_pool_name="",
                                  other_vhd_paths: list[str] = []):
    read_write_everyone(temp_dir)
    new_vm_name = v2v_prefix + vm_name

    this_vm_id = cli.zcompute.get_this_vm(config.ZCOMPUTE_IMPORTER_TAG,
                                          output_return=False)['id']
    logging.debug("Initializing disks dict")
    disks = list()
    disks.append({
        'local_vhd_path': boot_vhd_path,
        'capacity_gb': v2v.disk_inspect.get_file_size_gb(boot_vhd_path)})

    for vhd_path in other_vhd_paths:
        disks.append({
            'local_vhd_path': vhd_path,
            'capacity_gb': v2v.disk_inspect.get_file_size_gb(vhd_path)})
    logging.debug(f"Disks dict: {disks}")

    converted_path = cli.v2v.convert_vhd(boot_vhd_path, temp_dir,
                                         output_return=False)
    if not converted_path:
        typer.Abort("Failed virt-v2v conversion")
    else:
        disks[0]['converted_path'] = converted_path

    for disk in disks[1:None]:
        disk['converted_path'] = cli.v2v.convert_vhd(disk['local_vhd_path'],
                                                     temp_dir,
                                                     boot_disk=False,
                                                     output_return=False)

    index = 0
    for disk in disks:
        disk['index'] = index
        disk['zcompute_volume'] = \
            cli.zcompute.create_volume(new_vm_name + str(index),
                                       int(disk['capacity_gb']),
                                       storage_pool_name=storage_pool_name)
        index += 1

    for disk in disks:
        disk['local_block_device'] = \
            cli.zcompute.attach_volume_local(disk['zcompute_volume']['id'],
                                             this_vm_id,
                                             output_return=False)

        cli.v2v.dd_disk(disk['converted_path'],
                        disk['local_block_device'])

        cli.zcompute.detach_volume(disk['zcompute_volume']['id'],
                                   this_vm_id)

    boot_volume = disks[0]['zcompute_volume']['id']
    other_volumes = [disk['zcompute_volume']['id']
                     for disk in disks[1:None]]

    new_vm = cli.zcompute.create_vm(new_vm_name,
                                    cpu,
                                    int(ram_gb),
                                    boot_volume,
                                    other_volumes,
                                    storage_pool_name,
                                    output_return=False)
    return new_vm
    typer.echo(f"Created new VM: {new_vm}")


@app.command(no_args_is_help=True)
def migrate_vsphere_via_api(vm_name: str,
                            temp_dir: str,
                            storage_pool_name=""):
    """Migrate a vm from vsphere to zCompute, end to end.
       Uses API of the compute cluster
       Use migrate-vsphere-via-block-device command to have
       a faster experience

    Args:
        vm_name (str): Name of the new vm in zCompute
        temp_dir (str): A directory to write temp files,
                        has to contain the size of the boot disk
        storage_pool_name (str, optional):
            Name of the storage pool to use in zCompute. Defaults to "".
    """
    read_write_everyone(temp_dir)
    new_vm_name = v2v_prefix + vm_name
    vm = cli.vmware.get_vm(name=vm_name, output_return=False)
    vm_disks = cli.vmware.get_vm_disks(vm_name, output_return=False)
    index = 0
    for disk in vm_disks:
        disk['local_vmdk_path'] = cli.vmware.curl_vmdk(disk['datastore'],
                                                       disk['vmdk_path'],
                                                       temp_dir,
                                                       output_return=False)
        disk['index'] = index
        index += 1

    for disk in vm_disks:
        disk['converted_path'] = \
            cli.v2v.convert_vmdk(disk['local_vmdk_path'],
                                 temp_dir,
                                 output_return=False)

    boot_disk_path = vm_disks[0]['converted_path']
    other_disks = [disk['converted_path'] for disk in vm_disks[1:None]]
    new_vm = cli.zcompute.create_vm_from_disks(new_vm_name,
                                               vm['cpu'],
                                               vm['memory_gb'],
                                               boot_disk_path,
                                               other_disks,
                                               storage_pool_name,
                                               output_return=False)

    return new_vm
    typer.echo(f"Created new VM: {new_vm}")

# TODO: Allow migration of folder as a batch


@app.command(no_args_is_help=True)
def migrate_vsphere_via_block_device(vm_name: str,
                                     temp_dir: str,
                                     storage_pool_name=""):
    """Migrate a vm from vsphere to zCompute, end to end.
       Uses mounting of block device to this machine.
       This means the machine has to be located on the v2v
       target compute cluster.

    Args:
        vm_name (str): Name of the new vm in zCompute
        temp_dir (str): A directory to write temp files,
                        has to contain the size of the boot disk
        storage_pool_name (str, optional):
            Name of the storage pool to use in zCompute. Defaults to "".
    """
    # TODO: check if temp_dir has enough space for the VM
    read_write_everyone(temp_dir)
    new_vm_name = v2v_prefix + vm_name
    vm = cli.vmware.get_vm(name=vm_name, output_return=False)
    if vm['power_state'] != 0:
        logging.exception("VM cannot be migrated because power state doesn't "
                          "seem to be off")
        typer.Abort("")
    else:
        vm_disks = cli.vmware.get_vm_disks(vm_name, output_return=False)
        this_vm_id = cli.zcompute.get_this_vm(config.ZCOMPUTE_IMPORTER_TAG,
                                              output_return=False)['id']
        index = 0
        for disk in vm_disks:
            disk['index'] = index
            disk['zcompute_volume'] = \
                cli.zcompute.create_volume(new_vm_name + str(index),
                                           int(disk['capacity_gb']),
                                           storage_pool_name=storage_pool_name,
                                           output_return=False)
            disk['local_block_device'] = \
                cli.zcompute.attach_volume_local(disk['zcompute_volume']['id'],
                                                 this_vm_id,
                                                 output_return=False)
            disk['local_vmdk_path'] = \
                cli.vmware.curl_vmdk(disk['datastore'],
                                     disk['vmdk_path'],
                                     disk['local_block_device'],
                                     output_return=False)
            index += 1

        vm_boot_disk = vm_disks[0]
        vm_boot_disk['converted_path'] = \
            cli.v2v.convert_vmdk(vm_boot_disk['local_vmdk_path'],
                                 temp_dir,
                                 output_return=False)

        cli.v2v.dd_disk(vm_boot_disk['converted_path'],
                        vm_boot_disk['local_block_device'])

        for disk in vm_disks:
            cli.zcompute.detach_volume(disk['zcompute_volume']['id'],
                                       this_vm_id)

        boot_volume = vm_disks[0]['zcompute_volume']['id']
        other_volumes = [disk['zcompute_volume']['id']
                         for disk in vm_disks[1:None]]

        new_vm = cli.zcompute.create_vm(new_vm_name,
                                        vm['cpu'],
                                        int(vm['memory_gb']),
                                        boot_volume,
                                        other_volumes,
                                        storage_pool_name,
                                        output_return=False)

        return new_vm
        typer.echo(f"Created new VM: {new_vm}")


if __name__ == "__main__":
    app()
