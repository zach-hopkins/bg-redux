param([string]$Filter = 'MovementTest.*:MapTest.*', [string]$RunName = 'focused-live', [int]$Timeout = 30, [switch]$Managed)
$taskArgs = @((Join-Path $PSScriptRoot 'harness.py'), 'core', '--filter', $Filter, '--name', $RunName, '--timeout', $Timeout)
if ($Managed) { $taskArgs += '--managed' }
& python @taskArgs
exit $LASTEXITCODE
