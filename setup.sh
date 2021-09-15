#!/bin/bash 

function installRPMs(){
    echo "Installing RPMs"

    sudo yum update -y
    sudo yum install -y epel-release
    sudo yum install -y $(cat rpm-packages.txt)
}
function installPip(){
    curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py
    sudo python2 get-pip.py
    rm get-pip.py
    python3 -m ensurepip --upgrade
}
function installPipPackages(){
    sudo pip2 install --ignore-installed PyYAML
    sudo pip2 install setuptools --upgrade
    sudo pip2 install python-neutronclient==3.1.0
    sudo python3 -m pip install typer python-magic
}
function installPowerShell(){
    curl https://packages.microsoft.com/config/rhel/7/prod.repo | sudo tee /etc/yum.repos.d/microsoft.repo
    sudo yum install -y powershell
    sudo pwsh -command 'Set-PSRepository PSGallery -InstallationPolicy Trusted'
    sudo pwsh -command 'Install-Module -Name VMware.PowerCLI -Scope AllUsers'
    sudo pwsh -command 'Set-PowerCLIConfiguration -Scope AllUsers -ParticipateInCEIP $true -Confirm:$false'
    sudo pwsh -command 'Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Scope AllUsers -Confirm:$false'
}
function installVirtV2V(){
    sudo wget https://fedorapeople.org/groups/virt/virtio-win/virtio-win.repo -O /etc/yum.repos.d/virtio-win.repo
    sudo yum install -y virtio-win
    sudo systemctl start libvirtd
}
installRPMs
installPip
installPipPackages
installPowerShell
installVirtV2V