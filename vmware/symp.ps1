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
        Write-Log "Command $symp_command failed $result with exit code $LASTEXITCODE"
        throw $result
    }
    else {
        Write-Log "Command $symp_command returned $result"
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

function Attach-SYMPVolumes($vm_id, $volume_ids) {
    Write-Log "Attaching Volumes: $volume_ids to VM ID $vm_id"
    $lsblk_command = "lsblk --output NAME -d -n -e 11"
    $local_volumes_pre_attach = Invoke-Expression $lsblk_command
    Write-Log "Local volumes $local_volumes_pre_attach"

    foreach ($volume_id in $volume_ids) {
        $command = "vm volumes attach $vm_id $volume_id"
        Invoke-SYMPCommand $command
    }
    sleep 45
    $local_volumes_post_attach = Invoke-Expression $lsblk_command
    $new_local_volumes = $local_volumes_post_attach | Where-Object { $local_volumes_pre_attach -NotContains $_ }
    Write-Log "New local volumes $new_local_volumes"

    return $new_local_volumes
}