#!/usr/bin/env pwsh
. ./config.ps1
. ./logger.ps1
. ./vmware.ps1
. ./symp.ps1

$dir = $PWD
$data_dir = '/data'
function Exit-Script () {
    Write-Log "Exiting script"
    Exit
}

function Convert-Disk($source_path, $source_file, $target_path, $target_file, $temp_directory) {
    # Remove-Item -Path "$temp_directory/$source_file-sda"
    # $ntfsfix_command = "ntfsfix -d $source_path/$sourcefile"
    # Write-Log $ntfsfix_command
    # Invoke-Expression $ntfsfix_command | Write-Log
    $virt_v2v_command = "./convert-vmdk.sh $source_file $temp_directory "
    Write-Log $virt_v2v_command
    Invoke-Expression $virt_v2v_command | Write-Log
    $dd_command = "dd if=$temp_directory/$source_file-sda bs=128M | pv | dd of=$target_path/$target_file bs=128M"
    Write-Log $virt_v2v_command
    Invoke-Expression $dd_command | Write-Log
    Invoke-Expression "sync"
}

function Convert-DiskFromNFS($vmdk_filename, $nfs_path, $target_path, $target_file, $temp_directory) {
    # TODO
}

$connection_success = Connect-VMWVsphere $VIHOST $VIUSER $VIPASSWORD
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
        foreach ($disk in $disks) {
            $symp_volume = New-SYMPVolume $SYMPPOOLNAME $disk.Parent.Name $disk.Name $disk.CapacityGB
            $disk | Add-Member -NotePropertyName "symp_volume_id" -NotePropertyValue $symp_volume
        }
        $symp_this_vm_id = Get-SYMPVMID $TAG
        
        foreach ($disk in $disks) {
            $new_local_device = AttachWait-SYMPVolumeLocal $symp_this_vm_id $disk.symp_volume_id
            $disk | Add-Member -NotePropertyName "local_device" -NotePropertyValue $new_local_device
        }

        foreach ($disk in $disks) {
            $vmdk_path = $data_dir + '/' + (Get-VMWDiskVMDK $disk).split('/')[1]
            $disk | Add-Member -NotePropertyName "vmdk_path" -NotePropertyValue $vmdk_path
            Copy-DiskFromVmware $disk $vmdk_path
        }

        foreach ($disk in $disks) {
            Convert-Disk -source_path "" -source_file $disk.vmdk_path -target_path '/dev' -target_file $disk.local_device -temp_directory $data_dir
        }

        foreach ($disk in $disks) {
            Detach-SYMPVolume -vm_id $symp_this_vm_id -volume_id $disk.symp_volume_id
        }
        $vm_id = New-SYMPVM -name $vm.Name -boot_volume_id $disks[0].symp_volume_id -cpu $vm.NumCpu -ram_gb $vm.MemoryGB
        
        foreach ($disk in $disks[1..$disks.Length]) {
            Attach-SYMPVolume -vm_id $vm_id -volume_id $disk.symp_volume_id
        }
    }
}

