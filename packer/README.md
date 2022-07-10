# Packer

Build VM-Toolbox image using the packer.
> Important: run on a machine with KVM installed
1. Make a copy of `.auto.pkrvars.template.hcl` and rename it as `.auto.pkrvars.hcl`, after that update the relevant parameters:
	- `private_keypair_path` - Path to a private ssh key to access the packer builder (must have `.pub` file in the same folder)
1. Initiate packer
	```
	packer init .
	```
1. Build the image
	```
	packer build .
	```
1. Upload the image to the relevant S3 bucket.