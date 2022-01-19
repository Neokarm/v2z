import logging
import subprocess
import os


def run_and_log_command(command_args: list, env: dict = {}):
    """Run a command with live logging and live stdout

    Args:
        command_args (list): :ist of arguments for subprocess
        env (dict, optional): Extra environment variables. Defaults to {}.
    """
    logging.debug(f"Running {command_args}")
    if env:
        logging.debug(f"Extra environment variables: {env}")
    process = subprocess.Popen(command_args,
                               env=dict(**os.environ, **env),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    while process.stdout.readable():
        line = process.stdout.readline()
        if not line:
            break
        line_str = line.strip().decode("utf-8")
        print(line_str)
        logging.info(f"output: {line_str}")

    if process.returncode:
        logging.error(f"Command return code {process.returncode}")
    else:
        logging.info("Command successfully finished")

    return process.returncode
