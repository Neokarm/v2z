$VMs = Get-Content C:\vms.txt
$Destination = "D:\export2"
if (-not (Test-Path $Destination)) {
    New-Item -Path $Destination -ItemType Directory
}
foreach ( $VM in $VMs ) {
    $VMTargetDir = New-Item -Path $Destination -ItemType Directory -Name $VM
    $VMObject = Get-VM $VM
    $RAM = $VMObject.MemoryStartup/1MB
    $CPU = $VMObject.ProcessorCount
    $HardDrives = $VMObject.HardDrives
    Set-Content -Value $RAM -Path "$VMTargetDir\ram.txt"
    Set-Content -Value $CPU -Path "$VMTargetDir\cpu.txt"
    foreach ( $HardDrive in $HardDrives) {
        if ($HardDrive.ControllerNumber -eq 0 -and $HardDrive.ControllerLocation -eq 0)
        {
            $HDName = (Get-Item $HardDrive.Path).Name
            Convert-VHD -Path $HardDrive.Path -VHDType Fixed -DestinationPath "$VMTargetDir\$HDName"
        }
        else {
            Copy-Item -Path $HardDrive.Path -Destination $VMTargetDir
        }
    }
}