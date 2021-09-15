import typer
import config
import logging
import vmware

app = typer.Typer()


@app.command()
def get_vm(name: str = "", folder_name: str = ""):
    """Get vms

    Args:
        name (str, optional): Get vm by name. Defaults to "".
        folder_name (str, optional): Get vms by folder. Defaults to "".

    Returns:
        list[{
                name: str,
                cpu: int,
                memory_gb: int,
                total_disk_gb: int,
                power_state: str
            }]: VM(s) from vmware
    """
    vsphere_powershell = vmware.PowerShellVsphere(config.VIHOST,
                                                  config.VIUSER,
                                                  config.VIPASSWORD)
    if name:
        vm = vsphere_powershell.get_vm(name)
        logging.debug(f"VM: {vm}")
        typer.echo(vm)
        return vm
    else:
        vms = vsphere_powershell.get_vms(folder_name)
        logging.debug(f"{folder_name} VMs: {vms}")
        typer.echo(vms)
        return vms


@app.command()
def get_vm_disks(vm_name: str):
    vsphere_powershell = vmware.PowerShellVsphere(config.VIHOST,
                                                  config.VIUSER,
                                                  config.VIPASSWORD)
    disks = vsphere_powershell.get_vm_disks(vm_name)
    logging.debug(f"Disks of {vm_name}: {disks}")
    typer.echo(disks)
    return disks


@app.command()
def curl_vmdk(datastore: str, vmdk_path: str, output_path: str):
    output_path = vmware.curl_vmdk_file(datastore,
                                        vmdk_path,
                                        output_path,
                                        config.ESXHOST,
                                        config.ESXUSER,
                                        config.ESXPASSWORD)
    logging.debug(f"vmdk path: {output_path}")
    typer.echo(output_path)
    return output_path


if __name__ == "__main__":
    app()
