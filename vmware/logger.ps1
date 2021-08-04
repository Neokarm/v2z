#!/usr/bin/env pwsh
function Write-Log {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline, Position=1)]
        [string]$content
    )
    
    $output = (Get-Date).ToString() + " " + $content
    # Write-Output $output
    Out-File -FilePath $LOG -Append -InputObject $output
    Exit-PSHostProcess
}