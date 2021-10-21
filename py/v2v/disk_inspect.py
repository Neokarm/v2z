import os
import magic
import logging
import math


def is_vmdk_boot_disk(file_path: str) -> bool:
    boot_disk_string = 'active'
    logging.info(f"Checking if file {file_path} is boot disk")

    file_type_data = str(magic.from_file(file_path))
    logging.debug(f"File magic output: {file_type_data}")

    is_boot_disk = boot_disk_string in file_type_data
    logging.info(f"File {file_path} is_boot_disk: {is_boot_disk}")

    return is_boot_disk


def get_file_size_gb(file_path: str) -> int:
    size_in_bytes = os.path.getsize(file_path)
    size_in_gb = math.ceil(float(size_in_bytes) / 1024 / 1024 / 1024)
    return size_in_gb
