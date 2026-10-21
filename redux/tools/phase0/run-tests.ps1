param([string]$RunName = 'ctest', [int]$Timeout = 30)
& python (Join-Path $PSScriptRoot 'harness.py') ctest --name $RunName --timeout $Timeout
exit $LASTEXITCODE
