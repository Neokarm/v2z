import logging
import os
import subprocess
import json

PWSH_VMWARE_MODULE_PATH = './vmware/ps/vmware.psm1'


class PowerShellVsphere(object):
    def __init__(self,
                 vsphere_host: str,
                 vsphere_user: str,
                 vsphere_password: str):
        self._vsphere_host = vsphere_host
        self._vsphere_user = vsphere_user
        self._vsphere_password = vsphere_password

    def _run_vsphere_ps_command(self, command: str):
        host = self._vsphere_host
        user = self._vsphere_user
        password = self._vsphere_password

        import_command = f'Import-Module {PWSH_VMWARE_MODULE_PATH}; '
        connect_command = f'Connect-VMWVsphere {host} {user} {password}; '
        full_command = import_command + connect_command + command + ';'
        logging.info(f"Powershell command: {full_command}")
        output = subprocess.run(['pwsh', '-c', full_command],
                                stdout=subprocess.PIPE).stdout
        logging.debug(f"Command output: {output}")
        json_output = json.loads(output.decode("ascii"))
        logging.info(f"Json output: {json_output}")
        return json_output

    def get_vms(self,
                folder_name: str = ""):
        """Get vmware vms

        Args:
            folder_name (str, optional): folder to look for vms.
                                         Requires vsphere 6+ (5.5 fails)
                                         Defaults to "".

        Returns:
            list: list of vms
        """
        command = f"Get-VMWVMS {folder_name}"
        return self._run_vsphere_ps_command(command)

    def get_vm(self, vm_name: str):
        """Get a single vmware vm

        Args:
            vm_name (str): Name of the vm
        """
        command = f"Get-VMWVM {vm_name}"
        return self._run_vsphere_ps_command(command)

    def get_vm_disks(self, vm_name: str):
        command = f"Get-VMWVMDisks {vm_name}"
        return self._run_vsphere_ps_command(command)


def curl_vmdk_file(datastore: str,
                   vmdk_path: str,
                   output_path: str,
                   esx_host: str,
                   esx_user: str,
                   esx_password: str):
    file_extension = ".vmdk"
    uri = (f"https://{esx_host}/folder/{vmdk_path}"
           f"?dcPath=ha-datacenter&dsName={datastore}")
    curl_command = ['curl',
                    '-u', f"{esx_user}:{esx_password}",
                    uri,
                    '--insecure',
                    '--compressed']
    logging.info(f"curl command: {curl_command}")

    if os.path.isdir(output_path):
        output_path = os.path.join(output_path, os.path.basename(vmdk_path))

    output_path = output_path.replace(' ', '_')
    if file_extension not in output_path and \
       not output_path.startswith("/dev/"):
        output_path = output_path + file_extension
    logging.info(f"Output path is: {output_path}")
    try:
        output_file = open(output_path, "wb", buffering=0)
    except:
        logging.exception("Failed to open path to download vmdk")
    else:
        subprocess.run(curl_command, stdout=output_file)

    return output_path
