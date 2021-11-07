# v2v-tools
Collection of tools for zCompute v2v migration scenarios. Including Hyper-V and VMware.

Running the tool
`cd py`
`./main.py`

Installing auto completion:
`./main.py --install-completion`
Log out and in again in terminal for change to apply.

## Setup
1. Clone this repo to an importer machine (hosted on zcompute)
1. *Make sure you are root user, or able to use sudo before installation*
1. Run `./setup.sh`
1. Test SYMP CLI `symp -q -k --url <zCompute-cluster-url> -u <Username> -p <Password> -d <Account>`
1. Mount a volume for temporary data i.e. `/data` \
For Vmware, volume needs to contain the size of the vm boot disk. \
For Hyper-V, volume needs to contain the size of the vm boot disk and the size of the non-boot disks.
1. Setup config
```bash 
cd py
cp config.py.example config.py
vi config.py
```
http/s communication must be available from the importer machine to `ZCOMPUTE_IP`

For Vmware, set all parameters. \
http/s communication must be available from the importer machine to `ESX_HOST` and `VSPHERE_HOST`

For Hyper-V, set only `ZCOMPUTE_` parameters

### Vmware
#### Autopilot
1. After setting up configuration, we should select a vm for migration and make sure it's off (A clone of the vm on vmware would be fine too)
1. Test by running `./main.py vmware get-vm --name <your_vm>`
1. Migrate by running `./main.py migrate-vsphere-via-block-device <your_vm> <temp_dir>`
1. Power on the vm on zcompute 
#### Manual step-by-step
WIP


### Hyper-V
#### Autopilot
1. After setting up configuration, all the vms vhd/x files need to be copied or provided via mount to the importer machine
1. Migrate by running `./main.py migrate-vhdx-via-block-device`

#### Manual step-by-step
WIP