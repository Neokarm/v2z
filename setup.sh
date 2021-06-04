#!/bin/bash 

function installRPMs(){
    echo "Installing RPMs"

    sudo yum update -y
    sudo yum install -y epel-release
    sudo yum install -y $(cat rpm-packages.txt)
}
function installPip(){
    curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py
    python get-pip.py
    rm get-pip.py
}
function installPipPackages(){
    pip install setuptools --upgrade
    pip install python-neutronclient==3.1.0
}
function installPowerShell(){
    curl https://packages.microsoft.com/config/rhel/7/prod.repo | sudo tee /etc/yum.repos.d/microsoft.repo
    sudo yum install -y powershell
    pwsh -command 'Set-PSRepository PSGallery -InstallationPolicy Trusted'
    pwsh -command 'Install-Module -Name VMware.PowerCLI -Scope CurrentUser'
    pwsh -command 'Set-PowerCLIConfiguration -Scope User -ParticipateInCEIP $true -Confirm:$false'
    pwsh -command 'Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Scope User -Confirm:$false'
}
installRPMs
installPip
installPipPackages