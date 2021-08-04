#!/usr/bin/env pwsh

. ./config.ps1
. ./logger.ps1
. ./symp.ps1

$dir = $PWD
function Exit-Script () {
    Write-Log "Exiting script"
    Exit
}

function Convert-Disk($source_path, $source_file, $target_path, $target_file, $temp_directory) {
    Remove-Item -Path "$temp_directory/$source_file-sda"
    Invoke-Expression "ntfsfix -d $source_path/$sourcefile"
    Invoke-Expression "export LIBGUESTFS_BACKEND_SETTINGS=force_tcg ; export LIBGUESTFS_CACHEDIR=$temp_directory ;  virt-v2v -i disk $source_path/$source_file -o local -os $temp_directory"
    Invoke-Expression "dd if=$temp_directory/$source_file-sda bs=128M | pv | dd of=$target_path/$target_file bs=128M"
    Invoke-Expression "sync"

}
function Convert-DiskFromNFS($vmdk_filename, $nfs_path) {
    #TODO:
}

$SYMP_COMMAND="/usr/bin/symp -q -k --url https://$SYMPIP -u $SYMPUSER -p $SYMPPASS -d $SYMPTENANT $SYMPPROJECT"
$connection_success = Connect-Vsphere $VIHOST $VIUSER $VIPASSWORD
if (-not $connection_success) {
    Exit-Script
}

# TODO: Add an option to list vms from a file
Write-Log "Generating a list  of VMs to migrate..."
$vms = Get-VMWFolderVMS $VMFOLDER 
if ($vms.Length -lt 1) {
    Write-Log "No vms in folder $VMFOLDER"
    Exit-Script
}

# TODO: Do async?
foreach ($vm in $vms) {
    $disks = Get-VMWVMDisks $vm
    if ($disks.Length -lt 1)
    {
        Write-Log "No disks found for vm $vm"
        Exit-Script
    }
    else {
        # TODO: Do async?
        $new_volume_ids = New-Object System.Collections.ArrayList
        foreach ($disk in $disks) {
            $symp_volume = New-SYMPVolume $SYMPPOOLNAME $disk.Parent $disk.Name $disk.CapacityGB
            $new_volume_ids.Add($symp_volume)
        }
        $symp_this_vm_id = Get-SYMPVMID $TAG

        $new_local_volumes = Attach-SYMPVolumes $symp_this_vm_id $new_volume_ids

        for ($i = 0 ; $i -lt $new_local_volumes.Length; $i++) {
            Copy-DiskFromVmware $disks[$i] $new_local_volumes[$i]
        }
        
        for ($i = 0 ; $i -lt $new_local_volumes.Length; $i++) {
            Convert-Disk -source_path  -source_file $disks[$i] -target_path '/dev' -target_file $new_local_volumes[$i] -temp_directory '/data'
        }
    }
}

