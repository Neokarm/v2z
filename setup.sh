#!/bin/bash 

function installRPMs(){
    echo "Installing RPMs"

    sudo yum update -y
    # sudo yum install -y epel-release
    sudo yum install -y $(cat rpm-packages.txt)
}
function installPip(){
    echo "Installing pip"
    # curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py
    # sudo python2 get-pip.py
    # rm get-pip.py
    python3 -m ensurepip --upgrade
}
function installPipPackages(){
    echo "Installing pip packages"
    # sudo pip2 install --ignore-installed PyYAML
    # sudo pip2 install setuptools --upgrade
    # sudo pip2 install python-neutronclient==3.1.0
    python3 -m pip install typer python-magic
}
function installDocker(){
    echo "Installing docker"
    sudo dnf -y install dnf-plugins-core

    sudo dnf config-manager \
        --add-repo \
        https://download.docker.com/linux/fedora/docker-ce.repo
    
    sudo dnf install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
    sudo systemctl enable docker.service
    sudo systemctl enable containerd.service
    sudo systemctl start docker.service
    newgrp docker
}
function installSYMP(){
    echo "Installing SYMP"
    sudo cp symp /usr/bin/symp
    
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
installSYMP
installPip
installPipPackages
installPowerShell
installVirtV2V
installDocker
installAWS