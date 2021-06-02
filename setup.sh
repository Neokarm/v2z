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
installRPMs
installPip
installPipPackages