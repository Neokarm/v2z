import typer
import config
import json
import logging
import zcompute

app = typer.Typer()


def _get_symp_cli():
    return zcompute.Symp(config.SYMPIP,
                         config.SYMPTENANT,
                         config.SYMPUSER,
                         config.SYMPPASS,
                         config.SYMPPROJECT)


@app.command()
def get_storage_pool(pool_name=""):
    if not pool_name:
        pool_name = config.SYMPPOOLNAME
        logging.info(f"Pool name from config: {pool_name}")

    symp_cli = _get_symp_cli()
    storage_pool = symp_cli.get_storage_pool(pool_name)['id']

    logging.debug(f"storage pool: {storage_pool}")
    typer.echo(storage_pool)
    return storage_pool


@app.command()
def upload_image_to_zcompute(file_path: str, image_name: str,
                             storage_pool_name=""):
    if file_path.__contains__(" "):
        typer.secho("Source path cannot contain spaces", fg=typer.colors.RED)
        return False
    image_prefix = 'v2v_'

    storage_pool_id = get_storage_pool(storage_pool_name)
    symp_cli = _get_symp_cli()
    image = symp_cli.upload_image(file_path,
                                  image_prefix + image_name,
                                  storage_pool_id=storage_pool_id)

    logging.debug(f"image: {image}")
    typer.echo(image)
    return image


@app.command()
def upload_volume_to_zcompute(file_path: str, volume_name: str,
                              storage_pool_name=""):
    if file_path.__contains__(" "):
        typer.secho("Source path cannot contain spaces", fg=typer.colors.RED)
        return False
    volume_prefix = 'v2v_'

    storage_pool_id = get_storage_pool(storage_pool_name)
    symp_cli = _get_symp_cli()
    volume = symp_cli.upload_volume(file_path,
                                    volume_prefix + volume_name,
                                    storage_pool_id=storage_pool_id)

    logging.debug(f"volume: {volume}")
    typer.echo(volume)
    return volume


@app.command()
def create_vm_from_disks(name: str, cpu: int, ram_gb: int, boot_disk_path: str,
                         other_disk_paths: list[str] = [], uefi: bool = False,
                         storage_pool_name=""):
    boot_disk = upload_volume_to_zcompute(boot_disk_path,
                                          f"{name}-boot",
                                          storage_pool_name=storage_pool_name)
    if other_disk_paths:
        other_disks = list()
        for other_disk_path in other_disk_paths:
            index = len(other_disks) + 1
            other_disk = \
                upload_volume_to_zcompute(other_disk_path,
                                          f"{name}-disk{index}",
                                          storage_pool_name=storage_pool_name)
            other_disks.append(other_disk)

    boot_disk_id = json.loads(boot_disk)['id']
    other_disk_ids = list()
    for other_disk in other_disks:
        other_disk_ids.append(json.loads(other_disk)['id'])

    vm = create_vm(name, cpu, ram_gb, boot_disk_id,
                   other_disk_ids=other_disk_ids, uefi=uefi)
    typer.echo(vm)
    return vm


@app.command()
def create_vm(name: str, cpu: int, ram_gb: int, boot_disk_id: str,
              other_disk_ids: list[str] = [], uefi: bool = False):
    vm_prefix = 'v2v_'

    symp_cli = _get_symp_cli()
    vm = symp_cli.create_vm(vm_prefix + name, boot_disk_id, cpu, ram_gb,
                            other_disk_ids, uefi=uefi)

    logging.debug(f"vm: {vm}")
    typer.echo(vm)
    return vm


@app.command()
def create_volume(name: str, size_gb: int, storage_pool_name: str = ""):
    storage_pool_id = get_storage_pool(storage_pool_name)

    symp_cli = _get_symp_cli()
    volume = symp_cli.create_volume(name,
                                    size_gb,
                                    storage_pool_id=storage_pool_id)

    logging.debug(f"volume: {volume}")
    typer.echo(volume)
    return volume


@app.command()
def detach_volume(volume_id: str, vm_id: str):
    symp_cli = _get_symp_cli()
    output = symp_cli.detach_volume(volume_id, vm_id)
    if output:
        logging.debug(f"Detached {volume_id} from {vm_id}")
    else:
        logging.error("Failed to detach {volume_id} from {vm_id}")


@app.command()
def attach_volume(volume_id: str, vm_id: str):
    symp_cli = _get_symp_cli()
    output = symp_cli.attach_volume(volume_id, vm_id)
    if output:
        logging.debug(f"Attached {volume_id} to {vm_id}")
    else:
        logging.error("Failed to attach {volume_id} to {vm_id}")


@app.command()
def attach_volume_local(volume_id: str, vm_id: str) -> str:
    symp_cli = _get_symp_cli()
    block_device = symp_cli.attach_volume_local(volume_id, vm_id)

    logging.debug(f"block device: {block_device}")
    typer.echo(block_device)
    return block_device


@app.command()
def get_this_vm(tag: str = ""):
    if not tag:
        tag = config.TAG
    symp_cli = _get_symp_cli()
    vm = symp_cli.get_vm_by_tag(tag)

    logging.debug(f"vm: {vm}")
    typer.echo(vm)
    return vm


if __name__ == "__main__":
    app()
