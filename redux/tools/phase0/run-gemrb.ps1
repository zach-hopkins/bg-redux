param([ValidateSet('minimal','demo','bg2ee')][string]$Profile = 'bg2ee')
& python (Join-Path $PSScriptRoot 'launch.py') $Profile
exit $LASTEXITCODE
