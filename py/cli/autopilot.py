import typer
import config
import cli.vmware
import cli.zcompute
import cli.v2v

app = typer.Typer()


@app.command()
def migrate_vsphere_to_api(vm_name: str,
                           temp_dir: str,
                           storage_pool_name=""):
    """Migrate a vm from vsphere to zCompute, end to end.
       Uses API of the compute cluster

    Args:
        vm_name (str): Name of the new vm in zCompute
        temp_dir (str): A directory to write temp files,
                        has to contain the size of the boot disk
        storage_pool_name (str, optional):
            Name of the storage pool to use in zCompute. Defaults to "".
    """
    vm = cli.vmware.get_vm(name=vm_name)
    vm_disks = cli.vmware.get_vm_disks(vm_name)
    index = 0
    for disk in vm_disks:
        disk['local_vmdk_path'] = cli.vmware.curl_vmdk(disk['datastore'],
                                                       disk['vmdk_path'],
                                                       temp_dir)
        disk['index'] = index
        index += 1

    for disk in vm_disks:
        disk['converted_path'] = \
            cli.v2v.convert_vmdk(disk['local_vmdk_path'],
                                 temp_dir)

    boot_disk_path = vm_disks[0]['converted_path']
    other_disks = [disk['converted_path'] for disk in vm_disks[1:None]]
    vm = cli.zcompute.create_vm_from_disks(vm_name,
                                           vm['cpu'],
                                           vm['memory_gb'],
                                           boot_disk_path,
                                           other_disks,
                                           storage_pool_name)


@app.command()
def migrate_vsphere_to_block_device(vm_name: str,
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
    vm = cli.vmware.get_vm(name=vm_name)
    vm_disks = cli.vmware.get_vm_disks(vm_name)
    this_vm_id = cli.zcompute.get_this_vm(config.TAG)['id']
    index = 0
    for disk in vm_disks:
        disk['index'] = index
        disk['zcompute_volume'] = \
            cli.zcompute.create_volume(vm_name + str(index),
                                       int(disk['capacity_gb']),
                                       storage_pool_name=storage_pool_name)
        disk['local_block_device'] = \
            cli.zcompute.attach_volume_local(disk['zcompute_volume']['id'],
                                             this_vm_id)
        disk['local_vmdk_path'] = \
            cli.vmware.curl_vmdk(disk['datastore'],
                                 disk['vmdk_path'],
                                 disk['local_block_device'])
        index += 1

    vm_boot_disk = vm_disks[0]
    vm_boot_disk['converted_path'] = \
        cli.v2v.convert_vmdk(vm_boot_disk['local_vmdk_path'],
                             temp_dir)

    cli.v2v.dd_disk(vm_boot_disk['converted_path'],
                    vm_boot_disk['local_block_device'])

    for disk in vm_disks:
        cli.zcompute.detach_volume(disk['zcompute_volume']['id'],
                                   this_vm_id)

    boot_volume = vm_disks[0]['zcompute_volume']['id']
    other_volumes = [disk['zcompute_volume']['id']
                     for disk in vm_disks[1:None]]

    vm = cli.zcompute.create_vm(vm_name,
                                vm['cpu'],
                                int(vm['memory_gb']),
                                boot_volume,
                                other_volumes,
                                storage_pool_name)


if __name__ == "__main__":
    app()
