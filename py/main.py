import logging
import logging.config
import config
import typer

import cli.autopilot
import cli.v2v
import cli.vmware
import cli.zcompute


logging_config = {
    "version": 1,
    "root": {
        "handlers": ["file"],
        "level": "DEBUG"
    },
    "handlers": {
        "console": {
            "formatter": "just_message",
            "class": "logging.StreamHandler",
            "level": "WARNING"
        },
        "file": {
            "formatter": "simple",
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "filename": config.LOG
        }
    },
    "formatters": {
        "simple": {
            "format": "%(asctime)s : %(levelname)s : Log : %(message)s :"
                      " %(module)s : %(funcName)s : %(lineno)d",
            "datefmt": "%d-%m-%Y %I:%M:%S"
        },
        "just_message": {
            "format": "%(asctime)s : %(levelname)s : %(message)s",
            "datefmt": "%d-%m-%Y %I:%M:%S"
        }
    }
}
logging.getLogger(__name__)
logging.config.dictConfig(logging_config)


app = typer.Typer()
app.add_typer(cli.vmware.app, name="vmware")
app.add_typer(cli.zcompute.app, name="zcompute")
app.add_typer(cli.v2v.app, name="v2v")
app.add_typer(cli.autopilot.app, name="autopilot")


# @app.command()
# def curl_vmdk():
#     vms = vsphere_powershell.get_folder_vms(config.VMFOLDER)
#     for vm in vms:
#         vmware.vsphere.curl_vmdk_file

# def main():
#     typer.echo(f"zCompute v2v utility")

if __name__ == "__main__":
    app()
