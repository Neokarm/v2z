#!/usr/bin/env pwsh

. ./config.ps1
. ./logger.ps1

$SYMP_FILE = '/usr/bin/symp'
$SYMP_ARGS = "-q -k --url https://$SYMPIP -u $SYMPUSER -p $SYMPPASS -d $SYMPTENANT --project $SYMPPROJECT "

function Invoke-SYMPCommand($command) {
    $symp_command = "$SYMP_FILE $SYMP_ARGS $command"
    Write-Log "Running $symp_command"
    # Clear-Variable LASTEXITCODE -Force
    # $symp_process = Start-Process -FilePath $SYMP_FILE -ArgumentList "$SYMP_ARGS $command" -
    $result = Invoke-Expression $symp_command
    if ($LASTEXITCODE) {
        Write-Log "Command $symp_command failed `n$result `nwith exit code $LASTEXITCODE"
        throw $result
    }
    else {
        Write-Log "Command $symp_command returned `n$result"
        return $result
    }
}

function Get-SYMPStoragePools() {
    Write-Log "Get SYMP pools"
    $command = "storage pool list -c name -c id -f json"

    $symp_storage_pools = Invoke-SYMPCommand $command | ConvertFrom-Json

    if (-not $symp_storage_pools) {
        Write-Log "No pools were found"
    }
    else {
        Write-Log "Got pools: $symp_storage_pools"
    }
    return $symp_storage_pools
}

function New-SYMPVolume($symp_storage_pool_name, $vm_name, $disk_name, $disk_GB) {
    $symp_storage_pools = Get-SYMPStoragePools
    $symp_storage_pool = $symp_storage_pools | Where-Object name -eq $symp_storage_pool_name
    if (-not $symp_storage_pool) {
        Write-Log "Pool $symp_storage_pool_name not found."
        return $null
    }
    else {
        Write-Log "Selected pool $symp_storage_pool_name with ID $($symp_storage_pool.id)"
        $volume_name = "$vm_name-$disk_name"
        $volume_size = $disk_GB
        $command = "volume create -c id -f json --size $volume_size --storage-pool $($symp_storage_pool.id) '$volume_name'"
        $new_symp_volume = Invoke-SYMPCommand $command | ConvertFrom-Json
        $symp_volume_id = $new_symp_volume.id
        if ($symp_volume_id) {
            Write-Log "Created volume $volume_name ID: $symp_volume_id of size $volume_size"
        }
        return $symp_volume_id
    }

}
function Get-SYMPVMID($symp_tag) {
    $command = "vm list --tag-key $symp_tag -c tags -c name -c id -f json" 
    $symp_vm = Invoke-SYMPCommand $command | ConvertFrom-Json
    Write-Log "Symp vm is $($symp_vm.name) ID $($symp_vm.id)"
    return $symp_vm.id
}

function Attach-SYMPVolume($vm_id, $volume_id) {
    Write-Log "Attaching Volume: $volume_id to VM ID $vm_id"
    $command = "vm volumes attach -f json $vm_id $volume_id"
    $result = Invoke-SYMPCommand $command
    if ($result) {
        return $true
    }
    else {
        Write-Log "Failed to attach SYMP volume"
        return $false
    }
}
function Detach-SYMPVolume($vm_id, $volume_id) {
    Write-Log "Detaching Volume: $volume_id from $vm_id"
    $command = "vm volumes detach -f json -c id -c name $vm_id $volume_id"
    $result = Invoke-SYMPCommand $command
    if ($result) {
        return $true
    }
    else {
        Write-Log "Failed to detach SYMP volume"
        return $false
    }
}

function AttachWait-SYMPVolumeLocal($this_vm_id, $volume_id) {
    $lsblk_command = "lsblk --output NAME -d -n -e 11"
    $local_devices_pre_attach = Invoke-Expression $lsblk_command
    Write-Log "Local devices $local_devices_pre_attach"
    $result = Attach-SYMPVolume $this_vm_id $volume_id
    if ($result) {
        $tries = 0
        $max_tries = 45
        do {
            $local_devices_post_attach = Invoke-Expression $lsblk_command
            $new_device = $local_devices_post_attach | Where-Object { $local_devices_pre_attach -NotContains $_ }
            sleep 1
            $tries++
            Write-Log "Detecting new attached volume (try $tries of $max_tries)"
        } while (-not $new_device -and $tries -lt $max_tries)
        
        if ($new_device) {
            Write-Log "Detected new device $new_device"
            return $new_device
        }
        else {
            Write-Log "Failed to detect new device"
            return $null
        }
    }
    else {
        return $null
    }
}
function New-SYMPVM($name, $boot_volume_id, $cpu, $ram_gb) {
    Write-Log "Creating VM: $name Boot Volume: $boot_volume_id, CPU: $cpu, RAM_GB: $ram_gb"
    $boot_volume_parameter = "--boot-volumes id=${boot_volume_id}:disk_bus=virtio:device_type=disk"
    $command = "vm create -f json -c id --vcpu $cpu --ram $ram_gb $boot_volume_parameter $name"
    $vm = Invoke-SYMPCommand $command | ConvertFrom-Json
    if (-not $vm) {
        Write-Log "Failed to create VM: $name"
    }
    else {
        Write-Log "Created VM: $vm"
    }

    return $vm.id
}