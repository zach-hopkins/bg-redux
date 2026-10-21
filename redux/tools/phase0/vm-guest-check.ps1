param(
    [Parameter(Mandatory=$true)][string]$TransferRoot,
    [string]$ProjectRoot = 'C:\BGRedux'
)
$ErrorActionPreference = 'Stop'
$receipt = Get-Content -LiteralPath (Join-Path $TransferRoot 'transfer-manifest.json') -Raw | ConvertFrom-Json
$taskProject = (Resolve-Path -LiteralPath $ProjectRoot).Path
$taskMismatch = @()
foreach ($entry in $receipt.files.PSObject.Properties) {
    $taskFile = Join-Path $taskProject $entry.Name
    if (-not (Test-Path -LiteralPath $taskFile -PathType Leaf)) {
        $taskMismatch += $entry.Name
    } elseif ((Get-FileHash -LiteralPath $taskFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value.sha256) {
        $taskMismatch += $entry.Name
    }
}
if ($taskMismatch.Count) { throw ('Transfer mismatch: ' + ($taskMismatch -join ', ')) }
Write-Output ('Verified ' + $receipt.file_count + ' copied files. This is an integrity check, not a guest runtime test.')
Write-Output 'Next: install Git for Windows; use the bundled UCRT64 Python to rebuild external hosts and run the harness.'
Write-Output 'Do not use the copied CMake cache to rebuild engine code. Preserve historical host evidence.'
