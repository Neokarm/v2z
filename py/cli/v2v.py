import typer
import logging
import v2v

app = typer.Typer()


@app.command()
def convert_vmdk(vmdk_path: str, output_path: str) -> str:
    """Converts vmdk file located on the filesystem to raw,
       using virt-v2v command

    Args:
        vmdk_path (str): Path of the vmdk file
        output_path (str): Output directory of the process

    Returns:
        str: Path to the output raw file
    """

    output_file_path = v2v.virt_v2v.vmdk_to_raw(vmdk_path, output_path)
    logging.debug(f"raw file path: {output_file_path}")
    typer.echo(output_file_path)
    return (output_file_path)


@app.command()
def convert_vhd(vhd_path: str, output_path: str) -> str:
    """Convers vhd/vhdx file located on the filesystem to raw,
       using virt-v2v command

    Args:
        vhd_path (str): Path of the vhd/vhdx file
        output_path (str): Output directory of the process

    Returns:
        str: Path to the output raw file
    """

    output_file_path = v2v.virt_v2v.vhd_to_raw(vhd_path, output_path,
                                               is_nfs=is_nfs)
    logging.debug(f"raw file path: {output_file_path}")
    typer.echo(output_file_path)
    return (output_file_path)


@app.command()
def dd_disk(raw_file: str, block_device: str):
    """Uses the `dd` command to copy a raw disk into a block device

    Args:
        raw_file (str): Path to the input file
        block_device (str): Path to the output file
    """
    v2v.virt_v2v.dd_disk(raw_file, block_device)


if __name__ == "__main__":
    app()
