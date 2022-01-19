import typer
import logging
import v2v

app = typer.Typer()


@app.command()
def convert_vmdk(vmdk_path: str, output_path: str,
                 output_return=True) -> str:
    """Converts vmdk file located on the filesystem to raw,
       using virt-v2v command

    Args:
        vmdk_path (str): Path of the vmdk file
        output_path (str): Output directory of the process
        output_return (boolean, optional): return value as output

    Returns:
        str: Path to the output raw file
    """

    output_file_path = v2v.vmdk_to_raw(vmdk_path, output_path)
    logging.debug(f"raw file path: {output_file_path}")
    if output_return:
        typer.echo(output_file_path)
    return (output_file_path)


@app.command()
def convert_vhd(vhd_path: str, output_path: str, boot_disk: bool = True,
                output_return=True) -> str:
    """Converts vhd/vhdx file located on the filesystem to raw,
       using virt-v2v command

    Args:
        vhd_path (str): Path of the vhd/vhdx file
        output_path (str): Output directory of the process
        boot_disk (bool): If the disk is boot disk, should be converted
                          with virt-v2v
        output_return (boolean, optional): return value as output

    Returns:
        str: Path to the output raw file
    """
    if boot_disk:
        output_file_path = v2v.vhd_to_raw(vhd_path, output_path)
    else:
        output_file_path = v2v.non_boot_vhd_to_raw(vhd_path, output_path)
    logging.debug(f"raw file path: {output_file_path}")
    if output_return:
        typer.echo(output_file_path)
    return (output_file_path)


@app.command()
def dd_disk(raw_file: str, block_device: str):
    """Uses the `dd` command to copy a raw disk into a block device

    Args:
        raw_file (str): Path to the input file
        block_device (str): Path to the output file
    """
    v2v.dd_disk(raw_file, block_device)


if __name__ == "__main__":
    app()
