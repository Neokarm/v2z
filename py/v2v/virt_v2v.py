import logging
import subprocess
import os
import v2v.disk_inspect
import run_command


def vmdk_to_raw(vmdk_path: str,
                output_path: str,
                temp_location: str = "",
                is_nfs: bool = False) -> str:
    if not v2v.disk_inspect.is_vmdk_boot_disk(vmdk_path) \
       and not vmdk_path.startswith("/dev/"):
        logging.info(f"File {vmdk_path} is not a boot disk, which can be"
                     "treated as raw and left as is")
        return vmdk_path

    v2v_env = dict()
    v2v_env['LIBGUESTFS_BACKEND_SETTINGS'] = "force_tcg"
    if not temp_location:
        v2v_env['LIBGUESTFS_CACHEDIR'] = output_path
    else:
        v2v_env['LIBGUESTFS_CACHEDIR'] = temp_location
    # if is_nfs:
    v2v_env["LIBGUESTFS_BACKEND"] = "direct"
    logging.debug(f"virt-v2v environment variables: {v2v_env}")

    virt_v2v_command = ['virt-v2v',
                        '-i', 'disk', vmdk_path,
                        '-o', 'local',
                        '-os', output_path]
    logging.debug(f"virt-v2v command: {virt_v2v_command}")

    result = subprocess.run(virt_v2v_command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            env=dict(**os.environ, **v2v_env))
    result_text = result.stdout
    logging.debug(f"virt-v2v result: {result_text}")

    if vmdk_path.startswith("/dev/"):
        output_file_name = vmdk_path.replace('/dev/', '') + '-sda'
    else:
        output_file_name = os.path.basename(vmdk_path).replace('.vmdk',
                                                               '-sda')
    output_file_path = os.path.join(output_path, output_file_name)
    logging.info(f"File {vmdk_path} converted,"
                 f"output path: {output_file_path}")
    return output_file_path


def vhd_to_raw(vhd_path: str,
               output_path: str,
               temp_location: str = "",
               is_nfs: bool = False):
    logging.debug(f"Converting vhd/x {vhd_path} to {output_path}")
    v2v_env = dict()
    v2v_env['LIBGUESTFS_BACKEND_SETTINGS'] = "force_tcg"
    if not temp_location:
        v2v_env['LIBGUESTFS_CACHEDIR'] = output_path
    else:
        v2v_env['LIBGUESTFS_CACHEDIR'] = temp_location
    if is_nfs:
        v2v_env["LIBGUESTFS_BACKEND"] = "direct"

    virt_v2v_command = ['virt-v2v',
                        '-i', 'disk', vhd_path,
                        '-o', 'local',
                        '-of', 'raw',
                        '-os', output_path]

    return_code = run_command.run_and_log_command(virt_v2v_command,
                                                  env=v2v_env)

    if return_code:
        return return_code
    else:
        output_file_name = os.path.basename(vhd_path).replace('.vhdx',
                                                              '-sda')
        output_file_name = output_file_name.replace('.vhd',
                                                    '-sda')
        output_file_path = os.path.join(output_path, output_file_name)
        logging.info(f"File {vhd_path} converted,"
                     f"output path: {output_file_path}")
        return output_file_path


def non_boot_vhd_to_raw(vhd_path: str, output_path: str):
    output_name = os.path.basename(vhd_path)
    output_file_path = os.path.join(output_path, output_name)
    qemu_img_command = ['qemu-img', 'convert', '-p', '-O', 'raw',
                        vhd_path, f"{output_file_path}.raw"]
    logging.info(f"qemu-img command: {qemu_img_command}")
    result = subprocess.run(qemu_img_command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    if not result.returncode:
        logging.error(f"Failed to convert {vhd_path}")
    result_text = result.stdout
    logging.info(f"qemu-img result: {result_text}")


def dd_disk(raw_file: str, block_device: str):
    logging.debug(f"Copying {raw_file} into {block_device}")
    dd_command = ["dd", f"if={raw_file}", "bs=128M", f"of={block_device}",
                  "status=progress"]
    return_code = run_command.run_and_log_command(dd_command)
    if return_code:
        logging.error(f"dd command failed with return code {return_code}")
    else:
        logging.debug("dd command finished")


def create_device_link(block_device: str, destination_path: str):
    logging.debug(f"Creating symlink from {block_device} "
                  f"to {destination_path}")
    os.symlink(block_device, destination_path)
