#!/usr/bin/python3
import logging
import logging.config
import typer

import cli.autopilot
import cli.v2v
import cli.vmware
import cli.zcompute

logging.config.fileConfig("logging.conf",
                          disable_existing_loggers=False)

app = typer.Typer(no_args_is_help=True)
app.add_typer(cli.vmware.app, name="vmware", no_args_is_help=True)
app.add_typer(cli.zcompute.app, name="zcompute", no_args_is_help=True)
app.add_typer(cli.v2v.app, name="v2v", no_args_is_help=True)
app.add_typer(cli.autopilot.app, name="autopilot", no_args_is_help=True)

if __name__ == "__main__":
    app()
