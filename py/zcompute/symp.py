import logging
import os
import time
import subprocess
import json

SYMP_LOCATION = '/usr/bin/symp'


class Symp(object):
    def __init__(self, cluster_ip, account_name,
                 user_name, password, project_name):
        self._cluster_ip = cluster_ip
        self._account_name = account_name
        self._user_name = user_name
        self._password = password
        self._project_name = project_name

    def _run_symp_command(self, command):
        cluster_url = 'http://' + self._cluster_ip

        full_command = [SYMP_LOCATION, '-q', '-k',
                        '--url', cluster_url,
                        '-u', self._user_name,
                        '-p', self._password,
                        '-d', self._account_name,
                        '--project', self._project_name]
        full_command.extend(command.split(' '))
        logging.debug(f"Running {full_command}")
        result = subprocess.run(
            full_command, stdout=subprocess.PIPE)
        if result.returncode:
            error = result.stderr
            logging.error(error)
        else:
            output = result.stdout.decode("ascii")
            logging.debug(f"Command output: {output}")
            return output

    def create_volume(self, name, size_gb, storage_pool_id=""):
        log_output = f"Creating volume {name} of size {size_gb} GB"
        if storage_pool_id:
            log_output += f" storage_pool: {storage_pool_id}"
        logging.info(log_output)

        command = f"volume create {name} --size {size_gb} -f json"
        if storage_pool_id:
            command += f" --storage-pool {storage_pool_id}"
        output = self._run_symp_command(command)
        return json.loads(output)

    def upload_image(self, file_path, image_name, storage_pool_id=""):
        log_output = f"Uploading {file_path} as image {image_name}"
        if storage_pool_id:
            log_output += f" storage_pool: {storage_pool_id}"
        logging.info(log_output)
        command = (f"machine-images create-machine-image-from-file"
                   f"-f json {file_path} {image_name}")
        if storage_pool_id:
            command += f" --storage-pool {storage_pool_id}"
        output = self._run_symp_command(command)
        return output

    def upload_volume(self, file_path, volume_name, storage_pool_id=""):
        log_output = f"Uploading {file_path} as volume {volume_name}"
        if storage_pool_id:
            log_output += f" storage_pool: {storage_pool_id}"
        logging.info(log_output)
        command = f"volume create-and-upload -f json {file_path} {volume_name}"
        if storage_pool_id:
            command += f" --storage-pool {storage_pool_id}"
        output = self._run_symp_command(command)
        return output

    def create_vm(self, name, boot_volume_id, cpu, ram_gb,
                  additional_volume_ids: list = [], uefi: bool = False):
        log_output = (f"Creating VM: {name}, boot volume: {boot_volume_id},"
                      f"CPU: {cpu}, RAM: {ram_gb}GB")
        if additional_volume_ids:
            log_output += f" other volumes: {additional_volume_ids}"
        logging.info(log_output)

        volume_parameters = (f"--boot-volumes id={boot_volume_id}"
                             f":disk_bus=virtio:device_type=disk")

        if additional_volume_ids:
            additional_volume_parameters = " --volumes-to-attach"
            for additional_volume in additional_volume_ids:
                additional_volume_parameters += f" {additional_volume}"
            volume_parameters += additional_volume_parameters

        if uefi:
            hardware_type = " --hw-firmware-type uefi "
        else:
            hardware_type = ""

        ram_mb = int(ram_gb * 1024)

        command = (f"vm create {name} -f json --vcpu {cpu} --ram {ram_mb} "
                   f"{hardware_type}{volume_parameters}")
        output = self._run_symp_command(command)
        return output

    def _list_storage_pools(self):
        logging.debug("Getting storage pools")
        command = "storage pool list -f json"
        output = self._run_symp_command(command)
        return json.loads(output)

    def get_storage_pool(self, storage_pool_name):
        logging.debug(f"Getting storage pool {storage_pool_name}")
        storage_pools = self._list_storage_pools()
        this_pool = next(filter(lambda pool: pool['name'] == storage_pool_name,
                                storage_pools))
        return this_pool

    def get_vm_by_tag(self, tag: str):
        logging.debug(f"Getting vm with tag: {tag}")
        command = f"vm list --tag-key {tag} -f json"
        output = self._run_symp_command(command)
        json_output = json.loads(output)
        if len(json_output) > 1:
            logging.error("More than one vm found")
        else:
            return json_output[0]

    def attach_volume(self, volume_id: str, vm_id: str):
        logging.debug(f"Attaching {volume_id} to {vm_id}")
        command = f"vm volumes attach -f json {vm_id} {volume_id}"
        output = self._run_symp_command(command)
        return output

    def detach_volume(self, volume_id: str, vm_id: str):
        logging.debug(f"Detaching {volume_id} from {vm_id}")
        command = f"vm volumes detach -f json {vm_id} {volume_id}"
        output = self._run_symp_command(command)
        return output

    def attach_volume_local(self, volume_id: str, this_vm_id: str):
        local_devices_before = self._lsblk()
        result = self.attach_volume(volume_id, this_vm_id)
        if result:
            tries = 0
            max_tries = 45
            new_device = None
            while max_tries > tries and not new_device:
                local_devices_after = self._lsblk()
                device_diff = \
                    local_devices_after.difference(local_devices_before)
                if device_diff:
                    new_device = device_diff.pop()
                else:
                    tries += 1
                    time.sleep(1)
            if new_device:
                new_device = os.path.join("/dev/", new_device)
                logging.info(f"Detected new device {new_device}")
                self._allow_write(new_device)
                return new_device
            else:
                logging.error("Failed to detect new device")
        else:
            logging.error("Failed attaching volume")

    def _lsblk(self) -> set:
        lsblk_command = ["lsblk", "--output", "NAME", "-d", "-n", "-e", "11"]
        result = subprocess.run(lsblk_command, stdout=subprocess.PIPE)
        if result.returncode:
            logging.error(f"Failed to list local block devices, "
                          f"return code {result.returncode}")
        else:
            logging.info(f"Local devices: {result.stdout}")
            return set(result.stdout.decode("utf-8").split('\n'))

    def _allow_write(self, block_device: str):
        logging.debug(f"Allowing write for everyone "
                      f"to block device {block_device}")
        chmod_command = ["sudo", "chmod", "a+rw", "--recursive", block_device]
        result = subprocess.run(chmod_command)
        if result.returncode:
            logging.error(f"Failed to modify permissions "
                          f"for block device {block_device}")