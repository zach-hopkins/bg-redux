param(
    [string]$ProjectRoot = 'C:\BGRedux',
    [string]$GameRoot = "C:\Program Files (x86)\Steam\steamapps\common\Baldur's Gate II Enhanced Edition"
)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$taskRun = Join-Path $taskRoot ('phase0-local/results/' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') + '-guest-preflight-' + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $taskRun | Out-Null
$taskManifestPath = Join-Path $taskRoot 'docs/compatibility/evidence/bg2ee-copy-manifest.json'
$taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw | ConvertFrom-Json
$taskChecks = foreach ($taskEntry in $taskManifest.files) {
    $taskFile = Join-Path $GameRoot $taskEntry.path
    $taskExists = Test-Path -LiteralPath $taskFile -PathType Leaf
    $taskSize = if ($taskExists) { (Get-Item -LiteralPath $taskFile).Length } else { $null }
    $taskHash = if ($taskExists) { (Get-FileHash -LiteralPath $taskFile -Algorithm SHA256).Hash.ToLowerInvariant() } else { $null }
    [pscustomobject]@{path=$taskEntry.path; exists=$taskExists; bytes=$taskSize; sha256=$taskHash; matches=($taskExists -and $taskSize -eq $taskEntry.bytes -and $taskHash -eq $taskEntry.sha256)}
}
$taskChecks | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskRun 'game-files.json') -Encoding utf8
$taskSystem = Get-CimInstance Win32_ComputerSystem
$taskOS = Get-CimInstance Win32_OperatingSystem
$taskCPU = Get-CimInstance Win32_Processor
$taskRepo = Join-Path $taskRoot 'gemrb'
$taskChanged = @(& git -C $taskRepo diff --name-only bcb5cfaa9f19ffbe8a51f25a3c014fa344173351 HEAD -- . ':(exclude)redux' ':(exclude)README_BG_REDUX.md')
if ($LASTEXITCODE -ne 0) { throw 'Could not compare engine baseline' }
$taskWorking = @(& git -C $taskRepo diff --name-only HEAD -- . ':(exclude)redux' ':(exclude)README_BG_REDUX.md')
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect working tree' }
$taskMissing = @('phase0-local/build/gemrb/gemrb.exe','phase0-local/toolchain/msys64/ucrt64/bin/python.exe','phase0-local/fixtures/original-bg2ee-20261020/GemRB/baldur.gam') | Where-Object { -not (Test-Path -LiteralPath (Join-Path $taskRoot $_)) }
$taskReceipt = [ordered]@{
    recorded_at_utc=[DateTime]::UtcNow.ToString('o'); run_directory=$taskRun
    hostname=$env:COMPUTERNAME; user=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    manufacturer=$taskSystem.Manufacturer; model=$taskSystem.Model; ram_bytes=$taskSystem.TotalPhysicalMemory
    cpu=@($taskCPU | Select-Object NumberOfCores,NumberOfLogicalProcessors)
    os=$taskOS.Caption; os_version=$taskOS.Version; free_c_bytes=(Get-PSDrive C).Free
    display=@(Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion)
    vmtools_status=[string](Get-Service VMTools -ErrorAction SilentlyContinue).Status
    repository_commit=(& git -C $taskRepo rev-parse HEAD); engine_baseline='bcb5cfaa9f19ffbe8a51f25a3c014fa344173351'
    engine_committed_changes=$taskChanged; engine_working_changes=$taskWorking
    reference_manifest_sha256=(Get-FileHash -LiteralPath $taskManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    game_root=$GameRoot; game_files_checked=@($taskChecks).Count
    game_files_mismatched=@($taskChecks | Where-Object { -not $_.matches }).Count
    game_executable_version=(Get-Item -LiteralPath (Join-Path $GameRoot 'Baldur.exe')).VersionInfo.FileVersion
    missing_runtime_prerequisites=@($taskMissing)
    transfer_integrity_verified=$false; engine_tests_executed=$false; migration_complete=$false
    limits='File equality against historical manifest does not establish depot cleanliness, runtime parity, input isolation or snapshot acceptance. Private transfer manifests and runtime execution remain separate gates.'
}
$taskReceipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskRun 'result.json') -Encoding utf8
$taskReceipt | ConvertTo-Json -Depth 8
if ($taskReceipt.game_files_mismatched -or $taskChanged.Count -or $taskWorking.Count) { exit 1 }
