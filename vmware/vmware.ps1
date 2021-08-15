#!/usr/bin/env pwsh

. ./config.ps1
. ./logger.ps1

function Connect-VMWVsphere($vspherehost, $vsphereuser, $vspherepassword) {
    Write-Log "Connecting to vsphere $vspherehost"
    try {
        Connect-VIServer -Server $vspherehost -User $vsphereuser -Password $vspherepassword | Write-Log
    }
    catch {
        Write-Log "Failed to connect to vsphere $vspherehost"
        return $false
    }
    return $true
}
function Get-VMWFolderVMS($folder) {
    Write-Log "Getting vms in folder $folder"
    try {
        $vms = Get-Folder $folder | Get-VM | Select-Object Name, NumCpu, MemoryGB
    }
    catch {
        Write-Log "Failed to get vms"
    }
    Write-Log $vms
    return $vms
}
function Get-VMWVMDisks($vm) {
    Write-Log "Getting disks for vm $vm"
    try {
        $disks = Get-HardDisk -VM $vm.Name | Select-Object Name, Parent, CapacityGB, FileName
    }
    catch {
        Write-Log "Failed to get vm disks"
    }
    Write-Log $disks
    return $disks
}

function Get-VMWDiskDatastore($disk) {
    # Filename        : [datastore_1] w10pro-test1/w10pro-test1.vmdk
    return $disk.Filename.split(']')[0].replace('[','')
}
function Get-VMWDiskVMDK($disk) {
    # Filename        : [datastore_1] w10pro-test1/w10pro-test1.vmdk
    return $disk.Filename.split(']')[1].replace(' ','').replace('.vmdk', '-flat.vmdk')
}
function Copy-DiskFromVmware($disk, $target_device) {
    $datastore = Get-VMWDiskDatastore $disk
    $vmdk_path = Get-VMWDiskVMDK $disk
    # $uri = "https://${ESXHOST}/folder/${vmdk_path}?dcPath=ha-datacenter`&dsName=${datastore}"
    $uri = "https://${ESXHOST}/folder/${vmdk_path}?dcPath=ha-datacenter&dsName=${datastore}"
    $password = ConvertTo-SecureString $ESXPASSWORD -AsPlainText -Force
    $ESX_CRED = New-Object System.Management.Automation.PSCredential -ArgumentList ($ESXUSER, $password)
    # Invoke-WebRequest -SkipCertificateCheck -TransferEncoding gzip -Uri $uri -Credential $ESX_CRED -OutFile "/dev/${target_device}" | Write-Log
    # $curl_command = "curl -u ${ESXUSER}:${ESXPASSWORD} ${uri} --insecure --compressed > ./vmdkkks/dev/${target_device}"
    $curl_command = "curl"
    $arguments = "-u ${ESXUSER}:${ESXPASSWORD} ${uri} --insecure --compressed -o /dev/${target_device}"
    Write-Log "Curl command: $curl_command $arguments"
    Start-Process -FilePath 'curl' -ArgumentList $arguments -Wait | Write-Log
    # Invoke-Expression $curl_command | Write-Log
    #curl -u root:Str@to2014 https://10.16.1.105/folder/Cloud_Mgmt_Tool_Fedora23/Cloud_Mg?dcPath=ha-datacenter\&dsName=VPSA_it_prod_datastore1_yaffo -SkipCertificateCheck --insecure --compressed > /dev/vdg
    #curl -u root:Str@to2014 https://10.16.1.105/folder/Win10x64pro/Win10x64pro-flat.vmdk?dcPath=ha-datacenter\&dsName=VPSA_it_prod_datastore1_yaffo --insecure --compressed > /dev/vdd
    #PS /home/centos/v2v-tools/vmware> $disk  

    # StorageFormat   : Thin
    # Persistence     : Persistent
    # DiskType        : Flat
    # Filename        : [it_prod_datastore1_HRZ] w10pro-test1/w10pro-test1.vmdk
    # CapacityKB      : 41943040
    # CapacityGB      : 40
    # ParentId        : VirtualMachine-vm-300
    # Parent          : w10pro-test1
    # Uid             : /VIServer=vcenter.local\administrator@10.16.0.17:443/VirtualMachine=VirtualMachine-vm-300/HardDisk=2000/
    # ConnectionState : 
    # ExtensionData   : VMware.Vim.VirtualDisk
    # Id              : VirtualMachine-vm-300/2000
    # Name            : Hard disk 1
}
