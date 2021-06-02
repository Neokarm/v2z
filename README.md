# v2v-tools
Collection of tools for zCompute v2v migration scenarios. Including Hyper-V and VMware.

## Setup
1. Clone this repo
1. Run `./setup.sh`
1. Run `./symp-update -c <zCompute-Cluster-IP> -k`
1. Test SYMP `symp -q -k --url <zCompute-cluster-url> -u <Username> -p <Password> -d <Account>` 