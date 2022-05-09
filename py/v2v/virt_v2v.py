import logging
import os
import run_command

import v2v.disk_inspect


def vmdk_to_raw(vmdk_path: str,
                output_path: str,
                temp_location: str = "") -> str:
    if not v2v.disk_inspect.is_vmdk_boot_disk(vmdk_path) \
       and not vmdk_path.startswith("/dev/"):
        logging.info(f"File {vmdk_path} is not a boot disk, which can be"
                     "treated as raw and left as is")
        return vmdk_path
    virt_v2v_return_code = virt_v2v(vmdk_path,
                                    output_path,
                                    temp_dir=temp_location)

    if not virt_v2v_return_code:
        if vmdk_path.startswith("/dev/"):
            output_file_name = vmdk_path.replace('/dev/', '') + '-sda'
        else:
            output_file_name = os.path.basename(vmdk_path).replace('.vmdk',
                                                                   '-sda')
        output_file_path = os.path.join(output_path, output_file_name)
        logging.info(f"File {vmdk_path} converted, "
                     f"output path: {output_file_path}")
        return output_file_path
    else:
        return ""


def vhd_to_raw(vhd_path: str,
               output_path: str,
               temp_location: str = "") -> str:
    logging.debug(f"Converting vhd/x {vhd_path} to {output_path}")
    virt_v2v_return_code = virt_v2v(vhd_path,
                                    output_path,
                                    temp_dir=temp_location,
                                    output_raw=True)

    if not virt_v2v_return_code:
        output_file_name = "{}{}".format(os.path.basename(vhd_path),
                                         '-sda')
        output_file_path = os.path.join(output_path, output_file_name)
        logging.info(f"File {vhd_path} converted,"
                     f"output path: {output_file_path}")
        return output_file_path
    else:
        return ""


def ova_to_raw(ova_path: str,
               output_path: str,
               temp_location: str = "") -> str:
    logging.debug(f"Converting ova {ova_path} to {output_path}")

    clean_ova_name = os.path.basename(ova_path).replace(' ', '-').replace('(', '').replace(')', '')
    output_dir_name = clean_ova_name.replace('.ova', '') + '-output'
    output_dir = os.path.join(output_path, output_dir_name)
    if not os.path.isdir(output_dir):
        os.mkdir(path=output_dir)

    virt_v2v_return_code = virt_v2v(ova_path,
                                    output_dir,
                                    temp_dir=temp_location,
                                    output_raw=True,
                                    input_format="ova")
    if not virt_v2v_return_code:
        output_files = [file for file in os.listdir(output_dir) if '-sd' in file]
        message = "output files: \n{}".format("\n".join(output_files))
        logging.info(message)

        output_files_paths = [os.path.join(output_dir, file) for file in output_files]
        return output_files_paths
    else:
        return []


def virt_v2v(source_disk_path: str,
             output_dir: str,
             temp_dir: str = "",
             output_raw: bool = False,
             input_format="disk") -> bool:
    v2v_env = dict()
    v2v_env['LIBGUESTFS_BACKEND_SETTINGS'] = "force_tcg"
    if not temp_dir:
        v2v_env['LIBGUESTFS_CACHEDIR'] = output_dir
    else:
        v2v_env['LIBGUESTFS_CACHEDIR'] = temp_dir
    v2v_env["LIBGUESTFS_BACKEND"] = "direct"
    logging.debug(f"virt-v2v environment variables: {v2v_env}")

    virt_v2v_command = ['virt-v2v',
                        '-i', input_format,
                        source_disk_path,
                        '-o', 'local',
                        '-os', output_dir]
    if output_raw:
        virt_v2v_command.extend(['-of', 'raw'])

    logging.debug(f"virt-v2v command: {virt_v2v_command}")

    return_code = run_command.run_and_log_command(virt_v2v_command,
                                                  v2v_env)
    return return_code


def non_boot_vhd_to_raw(vhd_path: str, output_path: str):
    output_name = os.path.basename(vhd_path) + ".raw"
    output_file_path = os.path.join(output_path, output_name)
    qemu_img_command = ['qemu-img', 'convert', '-p', '-O', 'raw',
                        vhd_path, output_file_path]
    logging.info(f"qemu-img command: {qemu_img_command}")
    return_code = run_command.run_and_log_command(qemu_img_command,
                                                  )
    if return_code:
        logging.error(f"Failed to convert {vhd_path}")
        return ""
    return output_file_path


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
