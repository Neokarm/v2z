# v2z
Collection of tools for zCompute v2v migration scenarios. Including Hyper-V and VMware.

## Setup
1. Clone this repo
1. *Make sure you are root user, or able to use sudo before installation*
1. Run `./setup.sh`
1. Run `./symp-update -c <zCompute-Cluster-IP> -k`
1. Test SYMP `symp -q -k --url <zCompute-cluster-url> -u <Username> -p <Password> -d <Account>`

### Vmware
1. Move to the vmware directory `cd vmware`
1. Copy the config file `cp config.example config`
1. Fill in the details in the `config` file
1. Make sure there is a `/data` path in the machine with enough space for the vm disk
1. run `sudo ./migrate_vms`
