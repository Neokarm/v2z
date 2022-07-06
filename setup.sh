#!/bin/bash 

function installRPMs(){
    echo "Installing RPMs"

    sudo yum update -y
    # sudo yum install -y epel-release
    sudo yum install -y $(cat rpm-packages.txt)
}
function installPython3(){
    VERSION='3.9.5'
    sudo yum install -y openssl-devel bzip2-devel libffi-devel
    sudo yum groupinstall -y "Development Tools"
    wget "https://www.python.org/ftp/python/${VERSION}/Python-${VERSION}.tgz"
    tar -xzf "Python-${VERSION}.tgz"
    cd "Python-${VERSION}"
    ./configure --enable-optimizations
    make altinstall
}
function installPip(){
    echo "Installing pip"
    python3 -m ensurepip --upgrade
}
function installPipPackages(){
    echo "Installing pip packages"
    python3 -m pip install typer python-magic ipdb retry
}
function installPowerShell(){
    echo "Installing PowerShell"
    curl https://packages.microsoft.com/config/rhel/7/prod.repo | sudo tee /etc/yum.repos.d/microsoft.repo
    sudo yum install -y powershell
    sudo pwsh -command 'Set-PSRepository PSGallery -InstallationPolicy Trusted'
    sudo pwsh -command 'Install-Module -Name VMware.PowerCLI -Scope AllUsers'
    sudo pwsh -command 'Set-PowerCLIConfiguration -Scope AllUsers -ParticipateInCEIP $true -Confirm:$false'
    sudo pwsh -command 'Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Scope AllUsers -Confirm:$false'
}
function installVirtV2V(){
    echo "Installing virt-v2v"
    sudo wget https://fedorapeople.org/groups/virt/virtio-win/virtio-win.repo -O /etc/yum.repos.d/virtio-win.repo
    sudo yum install -y virtio-win
    sudo systemctl start libvirtd
}
function installAWS(){
    echo "Installing AWS"
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf awscliv2.zip aws
}

installRPMs
installPython3
installPip
installPipPackages
installPowerShell
installVirtV2V
installAWS