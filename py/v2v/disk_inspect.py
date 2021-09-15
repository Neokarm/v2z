import magic
import logging


def is_vmdk_boot_disk(file_path: str) -> bool:
    boot_disk_string = 'active'
    logging.info(f"Checking if file {file_path} is boot disk")

    file_type_data = str(magic.from_file(file_path))
    logging.debug(f"File magic output: {file_type_data}")

    is_boot_disk = boot_disk_string in file_type_data
    logging.info(f"File {file_path} is_boot_disk: {is_boot_disk}")

    return is_boot_disk
