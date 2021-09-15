import typer
import logging
import v2v

app = typer.Typer()


@app.command()
def convert_vmdk(vmdk_path: str, output_path: str, is_nfs: bool = False):

    output_file_path = v2v.virt_v2v.vmdk_to_raw(vmdk_path, output_path,
                                                is_nfs=is_nfs)
    logging.debug(f"raw file path: {output_file_path}")
    typer.echo(output_file_path)
    return (output_file_path)


@app.command()
def convert_vhd(vhd_path: str, output_path: str, is_nfs: bool = False):

    output_file_path = v2v.virt_v2v.vhd_to_raw(vhd_path, output_path,
                                               is_nfs=is_nfs)
    logging.debug(f"raw file path: {output_file_path}")
    typer.echo(output_file_path)
    return (output_file_path)


@app.command()
def dd_disk(raw_file: str, block_device: str):
    v2v.virt_v2v.dd_disk(raw_file, block_device)


if __name__ == "__main__":
    app()
