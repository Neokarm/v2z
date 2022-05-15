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
    if not cli.zcompute.validate_zcompute(storage_pool_name):
        typer.Abort("Failed validation")
    read_write_everyone(temp_dir)
    new_vm_name = v2v_prefix + vm_name

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

    vm_boot_disk = disks[0]
    other_disks = disks[1:None]

    converted_path = cli.v2v.convert_vhd(vm_boot_disk['local_vhd_path'], temp_dir,
                                         output_return=False)
    if not converted_path:
        typer.Abort("Failed virt-v2v conversion")
    else:
        vm_boot_disk['converted_path'] = converted_path

    for disk in other_disks:
        disk['converted_path'] = cli.v2v.convert_vhd(disk['local_vhd_path'],
                                                     temp_dir,
                                                     boot_disk=False,
                                                     output_return=False)

    converted_other_disks = [disk['converted_path']
                             for disk in other_disks]
    new_vm = cli.zcompute.create_vm_from_disks(new_vm_name, cpu, int(ram_gb),
                                               vm_boot_disk['converted_path'], storage_pool_name,
                                               other_disks=converted_other_disks,
                                               output_return=False)

    return new_vm


@app.command(no_args_is_help=True)
def migrate_vmdk_via_block_device(vm_name: str, cpu: int, ram_gb: int,
                                  boot_vmdk_path: str,
                                  temp_dir: str,
                                  storage_pool_name="",
                                  other_vmdk_paths: list[str] = []):
    """This is usually for vmdk through NFS attach scenario

    Args:
        vm_name (str): name of new vm in zcompute
        cpu (int): CPU units
        ram_gb (int): RAM GB
        boot_vmdk_path (str): path to boot vmdk, will be converted to qemu-kvm
        temp_dir (str): directory for conversions, needs to have space for all the vm
        other_vmdk_paths (list[str], optional): path for non-boot disks, will be imported as-is. Defaults to [].
        storage_pool_name (str, optional): storage pool name. Defaults to "".

    Returns:
        dict: new vm
    """
    if not cli.zcompute.validate_zcompute(storage_pool_name):
        typer.Abort("Failed validation")
    read_write_everyone(temp_dir)
    new_vm_name = v2v_prefix + vm_name

    vm_boot_disk = {
        'local_vmdk_path': boot_vmdk_path,
        'capacity_gb': v2v.disk_inspect.get_file_size_gb(boot_vmdk_path)}

    converted_path = cli.v2v.convert_vmdk(vm_boot_disk['local_vmdk_path'], temp_dir,
                                          output_return=False)
    if not converted_path:
        typer.Abort("Failed virt-v2v conversion")
    else:
        vm_boot_disk['converted_path'] = converted_path

    new_vm = cli.zcompute.create_vm_from_disks(new_vm_name, cpu, int(ram_gb),
                                               vm_boot_disk['converted_path'], storage_pool_name,
                                               other_disks=other_vmdk_paths,
                                               output_return=False)

    return new_vm


@app.command(no_args_is_help=True)
def migrate_ova_via_block_device(vm_name: str, cpu: int, ram_gb: int,
                                 ova_path: str,
                                 temp_dir: str,
                                 uefi: bool = False,
                                 storage_pool_name=""):
    """_summary_

    Args:
        vm_name (str): vm name to create
        cpu (int): CPU cores
        ram_gb (int): RAM GB
        ova_path (str): Path to OVA file
        temp_dir (str): Dir to keep converted image
        storage_pool_name (str, optional): alternate name for storage pool. Defaults to ''.

    Returns:
        string: new vm created
    """
    if not cli.zcompute.validate_zcompute(storage_pool_name):
        typer.Abort("Failed validation")
    read_write_everyone(temp_dir)

    converted_disks = cli.v2v.convert_ova(ova_path, temp_dir,
                                          output_return=False)

    if not converted_disks:
        typer.Abort("Failed virt-v2v conversion")

    converted_disks.sort()
    new_vm = cli.zcompute.create_vm_from_disks(vm_name, cpu, ram_gb,
                                               converted_disks[0], other_disk_paths=converted_disks[1:],
                                               storage_pool_name=storage_pool_name, output_return=False)
    return new_vm


@app.command(no_args_is_help=True)
def migrate_vsphere_via_block_device(vm_name: str,
                                     temp_dir: str,
                                     storage_pool_name="",
                                     uefi: bool = False):
    """Migrate a vm from vsphere to zCompute, end to end.
       Uses mounting of block device to this machine.
       This means the machine has to be located on the v2v
       target compute cluster.

    Args:
        vm_name (str): Name of the new vm in zCompute
        temp_dir (str): A directory to write temp files,
                        has to contain the size of the boot disk
        storage_pool_name (str, optional):
            Name of the storage pool to use in zCompute. Defaults to ''.
    """
    if not cli.zcompute.validate_zcompute(storage_pool_name):
        typer.Abort("Failed validation")
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
        vm_boot_disk = vm_disks[0]
        other_disks = vm_disks[1:None]
        vm_boot_disk['local_vmdk_path'] = \
            cli.vmware.curl_vmdk(vm_boot_disk['datastore'],
                                 vm_boot_disk['vmdk_path'],
                                 "{}-boot.vmdk".format(new_vm_name),
                                 output_return=False)

        index = 1
        for disk in other_disks:
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

        vm_boot_disk['converted_path'] = \
            cli.v2v.convert_vmdk(vm_boot_disk['local_vmdk_path'],
                                 temp_dir,
                                 output_return=False)

        if not vm_boot_disk['converted_path']:
            typer.Abort("Failed virt-v2v conversion")
        new_vm = cli.zcompute.create_vm_from_disks(new_vm_name, vm['cpu'], int(vm['memory_gb']),
                                                   vm_boot_disk['converted_path'], storage_pool_name,
                                                   output_return=False)

        for disk in other_disks:
            volume_id = disk['zcompute_volume']['id']
            cli.zcompute.detach_volume(volume_id, this_vm_id)
            cli.zcompute.attach_volume(volume_id, new_vm['id'])

        return new_vm


if __name__ == "__main__":
    app()
