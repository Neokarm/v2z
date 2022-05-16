import logging
import math
import os

import config
import typer

import zcompute
import cli.v2v

app = typer.Typer()


def _get_symp_cli(project=None):
    project = config.ZCOMPUTE_PROJECT if project is None else project
    return zcompute.Symp(config.ZCOMPUTE_IP,
                         config.ZCOMPUTE_ACCOUNT,
                         config.ZCOMPUTE_USER,
                         config.ZCOMPUTE_PASS,
                         project,
                         https=config.SSL,
                         port=config.PORT,
                         mfa_secret=config.ZCOMPUTE_MFA_SECRET)


@app.command()
def get_storage_pool(pool_name="", output_return=True) -> dict:
    """Get storage pool by name

    Args:
        pool_name (str, optional): storage pool name.
                                   Defaults to config.py ZCOMPUTE_STORAGE_POOL.
        output_return (boolean, optional): return value as output

    Returns:
        dict: Storage pool
    """
    if not pool_name:
        pool_name = config.ZCOMPUTE_STORAGE_POOL
        logging.info(f"Pool name from config: {pool_name}")

    symp_cli = _get_symp_cli()
    try:
        storage_pool = symp_cli.get_storage_pool(pool_name)['id']
    except:
        logging.exception("Failed to get storage pool, probably SYMP misconfiguration")
        return None
    logging.debug(f"storage pool: {storage_pool}")
    if output_return:
        typer.echo(storage_pool)
    return storage_pool


@app.command()
def upload_volume_to_zcompute(file_path: str, volume_name: str,
                              storage_pool_name="", output_return=True) -> dict:
    """Uploads a file as a volume through zCompute API

    Args:
        file_path (str): Path of the volume file (raw)
        volume_name (str): New name of the volume
        storage_pool_name (str, optional): storage pool name.
                                           Defaults to config.py ZCOMPUTE_STORAGE_POOL.
        output_return (boolean, optional): return value as output

    Returns:
        dict: Volume
    """
    if file_path.__contains__(" "):
        typer.secho("Source path cannot contain spaces", fg=typer.colors.RED)
        return False

    volume_size = math.ceil(os.stat(file_path).st_size / (1024*1024*1024))
    volume = create_volume(volume_name,
                           int(volume_size),
                           storage_pool_name=storage_pool_name,
                           output_return=False)

    this_vm_id = get_this_vm(config.ZCOMPUTE_IMPORTER_TAG, output_return=False)['id']
    local_block_device = attach_volume_local(volume['id'], this_vm_id, output_return=False)

    cli.v2v.dd_disk(file_path, local_block_device)

    detach_volume(volume['id'], this_vm_id)

    logging.debug(f"volume: {volume}")
    if output_return:
        typer.echo(volume)
    return volume


@app.command()
def create_vm_from_disks(name: str, cpu: int, ram_gb: int, boot_disk_path: str,
                         storage_pool_name="",
                         output_return=True,
                         other_disk_paths: list[str] = []) -> dict:
    """Create a vm from disk files in zCompute

    Args:
        name (str): new vm name
        cpu (int): CPU cores
        ram_gb (int): Gigabytes of RAM
        boot_disk_path (str): Path of the boot disk file
        other_disk_paths (list[str], optional): Paths to any additional disks.
                                                Defaults to [].
        storage_pool_name (str, optional): storage pool name.
                                           Defaults to config.py ZCOMPUTE_STORAGE_POOL.
        output_return (boolean, optional): return value as output

    Returns:
        dict: VM
    """
    boot_disk = upload_volume_to_zcompute(boot_disk_path,
                                          f"{name}-boot",
                                          storage_pool_name=storage_pool_name,
                                          output_return=False)
    other_disks = list()
    if other_disk_paths:
        for other_disk_path in other_disk_paths:
            index = len(other_disks) + 1
            other_disk = \
                upload_volume_to_zcompute(other_disk_path,
                                          f"{name}-disk{index}",
                                          storage_pool_name=storage_pool_name,
                                          output_return=False)
            other_disks.append(other_disk)

    boot_disk_id = boot_disk['id']
    other_disk_ids = list()
    for other_disk in other_disks:
        other_disk_ids.append(other_disk['id'])

    vm = create_vm(name, cpu, ram_gb, boot_disk_id,
                   other_disk_ids=other_disk_ids,
                   output_return=False)
    if output_return:
        typer.echo(vm)
    return vm


@app.command()
def create_vm(name: str, cpu: int, ram_gb: int, boot_disk_id: str,
              other_disk_ids: list[str] = [],
              output_return=False) -> dict:
    """Create VM from existing volumes

    Args:
        name (str): new vm name
        cpu (int): CPU cores
        ram_gb (int): Gigabytes of RAM
        boot_disk_id (str): ID of boot disk in zCompute
        other_disk_ids (list[str], optional): IDs of any additional disks.
                                              Defaults to [].
        output_return (boolean, optional): return value as output

    Returns:
        dict: VM
    """
    logging.debug(f"Creating: {name} {cpu}x{ram_gb} disks: {boot_disk_id} {other_disk_ids}")
    symp_cli = _get_symp_cli()
    vm = symp_cli.create_vm(name, boot_disk_id, cpu, ram_gb, other_disk_ids)

    logging.debug(f"vm: {vm}")
    if output_return:
        typer.echo(vm)
    return vm


@app.command()
def create_volume(name: str,
                  size_gb: int,
                  storage_pool_name: str = "",
                  output_return=False) -> dict:
    """Create empty volume in zCompute

    Args:
        name (str): new name of the volume
        size_gb (int): Gigabytes of size
        storage_pool_name (str, optional): storage pool name.
                                           Defaults to config.py ZCOMPUTE_STORAGE_POOL.
        output_return (boolean, optional): return value as output

    Returns:
        dict: Volume
    """
    storage_pool_id = get_storage_pool(storage_pool_name, output_return=False)

    symp_cli = _get_symp_cli()
    volume = symp_cli.create_volume(name,
                                    size_gb,
                                    storage_pool_id=storage_pool_id)

    logging.debug(f"volume: {volume}")
    if output_return:
        typer.echo(volume)
    return volume


@app.command()
def detach_volume(volume_id: str, vm_id: str):
    """Detach zCompute volume from a vm

    Args:
        volume_id (str): ID of volume
        vm_id (str): ID of VM
    """
    symp_cli = _get_symp_cli()
    output = symp_cli.detach_volume(volume_id, vm_id)
    if output:
        logging.debug(f"Detached {volume_id} from {vm_id}")
    else:
        logging.error("Failed to detach {volume_id} from {vm_id}")


@app.command()
def attach_volume(volume_id: str, vm_id: str):
    """Attach zCompute volume to a VM

    Args:
        volume_id (str): ID of volume
        vm_id (str): ID of VM
    """
    symp_cli = _get_symp_cli()
    output = symp_cli.attach_volume(volume_id, vm_id)
    if output:
        logging.debug(f"Attached {volume_id} to {vm_id}")
    else:
        logging.error("Failed to attach {volume_id} to {vm_id}")


@app.command()
def attach_volume_local(volume_id: str, vm_id: str, output_return=True) -> str:
    """Attach a volume to this vm and get the block device

    Args:
        volume_id (str): ID of volume
        vm_id (str): ID of this vm
        output_return (boolean, optional): return value as output

    Returns:
        str: The block device (/dev/vd_)
    """
    symp_cli = _get_symp_cli()
    block_device = symp_cli.attach_volume_local(volume_id, vm_id)

    logging.debug(f"block device: {block_device}")
    if output_return:
        typer.echo(block_device)
    return block_device


@app.command()
def get_this_vm(tag: str = "", output_return=True) -> dict:
    """Get the vm running v2v using a tag

    Args:
        tag (str, optional): tag of the VM running this tool.
                             Defaults to config.py ZCOMPUTE_IMPORTER_TAG.
        output_return (boolean, optional): return value as output

    Returns:
        dict: vm
    """
    if not tag:
        tag = config.ZCOMPUTE_IMPORTER_TAG
    symp_cli = _get_symp_cli()
    vm = symp_cli.get_vm_by_tag(tag)

    logging.debug(f"vm: {vm}")
    if output_return:
        typer.echo(vm)
    return vm


@app.command()
def validate_zcompute(storage_pool_name=''):
    """Preflight check for zcompute SYMP CLI
       Validates access to storage pool
       Validates ability to receive this VM to self-attach block devices

    Args:
        storage_pool_name (str, optional): _description_. Defaults to ''.

    Returns:
        string: this vm ID
    """
    storage_pool_id = cli.zcompute.get_storage_pool(storage_pool_name, output_return=False)
    if not storage_pool_id:
        logging.fatal("Failed to get storage pool, probably a ZCOMPUTE_ config.py misconfiguration")
        return None
    else:
        return get_this_vm(output_return=False)


if __name__ == "__main__":
    app()
