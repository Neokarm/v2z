function Connect-VMWVsphere($vspherehost, $vsphereuser, $vspherepassword) {
    Connect-VIServer -Server $vspherehost -User $vsphereuser -Password $vspherepassword | Out-Null
}

$get_vm_columns = "Name", "NumCpu", "CoresPerSocket", "MemoryGB", "ProvisionedSpaceGB", "PowerState"
function Get-VMWVMS($folder) {
    if ($null -eq $folder) {
        $vms = Get-VM | Select-Object $get_vm_columns
    }
    else {
        $vms = Get-Folder $folder | Get-VM | Select-Object $get_vm_columns
    }
    
    $vms_output = New-Object -TypeName System.Collections.ArrayList
    foreach ($vm in $vms) {
        $output_vm = [PSCustomObject]@{
            name = $vm.Name
            cpu = $vm.NumCpu
            cores_per_socket = $vm.CoresPerSocket
            memory_gb = $vm.MemoryGB
            total_disk_gb = $vm.ProvisionedSpaceGB
            power_state = $vm.PowerState
        }

        $vms_output.Add($output_vm) | Out-Null
    }
    $json = ConvertTo-Json -InputObject $vms_output -WarningAction SilentlyContinue -Compress
    return $json
}

function Get-VMWVM($name) {
    $vm = Get-VM $name | Select-Object $get_vm_columns
    $output_vm = [PSCustomObject]@{
        name = $vm.Name
        cpu = $vm.NumCpu
        cores_per_socket = $vm.CoresPerSocket
        memory_gb = $vm.MemoryGB
        total_disk_gb = $vm.ProvisionedSpaceGB
        power_state = $vm.PowerState
    }
    $json = ConvertTo-Json -InputObject $output_vm -WarningAction SilentlyContinue -Compress
    return $json
}

$get_hard_disks_colums = "Name", "Parent", "CapacityGB"
function Get-VMWVMDisks($vm) {
    $disks = Get-HardDisk -VM $vm | Select-Object $get_hard_disks_colums
    $disks_output = New-Object -TypeName System.Collections.ArrayList
    foreach ($disk in $disks) {
        $output_disk = [PSCustomObject]@{  
            name = $disk.Name
            vm = $disk.Parent.Name
            capacity_gb = $disk.CapacityGB
            datastore = Get-VMWDiskDatastore($disk)
            vmdk_path = Get-VMWDiskVMDK($disk)
        }

        $disks_output.Add($output_disk) | Out-Null
    }   
    $json = ConvertTo-Json -InputObject $disks_output -WarningAction SilentlyContinue -Compress
    return $json
}

function Get-VMWDiskDatastore($disk) {
    # Filename        : [datastore_1] w10pro-test1/w10pro-test1.vmdk
    return $disk.Filename.split(']')[0].replace('[','')
}

function Get-VMWDiskVMDK($disk) {
    # Filename        : [datastore_1] w10pro-test1/w10pro-test1.vmdk
    return $disk.Filename.split(']')[1].replace(' ','').replace('.vmdk', '-flat.vmdk')
}

Export-ModuleMember -Function Connect-VMWVsphere, Get-VMWVMS, Get-VMWVM, Get-VMWVMDisks