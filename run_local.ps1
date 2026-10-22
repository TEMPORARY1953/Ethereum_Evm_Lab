param()
$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$ChecksRoot = Join-Path $ProjectRoot 'checks'
New-Item -ItemType Directory -Force $ChecksRoot | Out-Null
$steps = [System.Collections.Generic.List[object]]::new()

function Run-Step([string]$Name, [string]$Script) {
    $log = Join-Path $ChecksRoot "$Name.log"
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Script 2>&1 | ForEach-Object { $_.ToString() }
    $code = $LASTEXITCODE
    $ErrorActionPreference = $oldPreference
    $output | Set-Content -LiteralPath $log -Encoding UTF8
    $output | Write-Output
    return [pscustomobject]@{name=$Name; exit_code=$code; log="checks/$Name.log"}
}

Push-Location $ProjectRoot
try {
    # Output is displayed, while the final object is collected for the JSON summary.
    $installOutput = @(Run-Step 'install' (Join-Path $ProjectRoot '.tools/install.ps1'))
    $install = $installOutput[-1]
    $installOutput | Select-Object -SkipLast 1 | Write-Output
    $install | Add-Member -NotePropertyName status -NotePropertyValue $(if ($install.exit_code -eq 0) { 'PASS' } elseif ($install.exit_code -eq 2) { 'BLOCKED' } else { 'FAIL' })
    $steps.Add($install)

    $verifyOutput = @(Run-Step 'verify' (Join-Path $ProjectRoot 'verify.ps1'))
    $verify = $verifyOutput[-1]
    $verifyOutput | Select-Object -SkipLast 1 | Write-Output
    $verify | Add-Member -NotePropertyName status -NotePropertyValue $(if ($verify.exit_code -eq 0) { 'PASS' } elseif ($verify.exit_code -eq 2) { 'BLOCKED' } else { 'FAIL' })
    $steps.Add($verify)

    if ($verify.exit_code -eq 1) {
        $steps.Add([pscustomobject]@{name='anvil'; status='SKIPPED'; reason='Tests failed; refusing to deploy'})
    } else {
        $demoOutput = @(Run-Step 'anvil_attempt' (Join-Path $ProjectRoot 'task4/scripts/local_demo.ps1'))
        $demo = $demoOutput[-1]
        $demoOutput | Select-Object -SkipLast 1 | Write-Output
        $missingTools = @(@('forge','cast','anvil','solc') | Where-Object { -not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".tools/bin/$_.exe")) })
        $demoStatus = if ($demo.exit_code -eq 0) { 'PASS' } elseif ($missingTools.Count -gt 0) { 'BLOCKED' } else { 'FAIL' }
        $demo | Add-Member -NotePropertyName status -NotePropertyValue $demoStatus
        $demo | Add-Member -NotePropertyName missing_tools -NotePropertyValue $missingTools
        $steps.Add($demo)
    }
    [ordered]@{timestamp_utc=[DateTime]::UtcNow.ToString('o'); public_transactions_sent=$false; steps=@($steps.ToArray())} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ChecksRoot 'local_run.json') -Encoding UTF8
    $steps | Format-Table name,status,exit_code -AutoSize
    if ($steps.status -contains 'FAIL') { exit 1 }
    if ($steps.status -contains 'BLOCKED') { exit 2 }
} finally { Pop-Location }
