import subprocess
import logging


def read_write_everyone(path: str):
    logging.debug(f"Allowing write for everyone "
                  f"to block device {path}")
    chmod_command = ["sudo", "chmod", "a+rw", "--recursive", path]
    result = subprocess.run(chmod_command)
    if result.returncode:
        logging.error(f"Failed to modify permissions "
                      f"for block device {path}")
