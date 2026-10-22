param([string]$PythonPath)
$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
Push-Location $ProjectRoot
try {
    New-Item -ItemType Directory -Force checks | Out-Null
    $checks = [System.Collections.Generic.List[object]]::new()
    $syntaxMessages = [System.Collections.Generic.List[string]]::new()
    $syntaxOk = $true
    foreach ($script in @('verify.ps1','run_local.ps1','.tools/install.ps1','task4/scripts/local_demo.ps1')) {
        $parseErrors = $null
        $parseTokens = $null
        [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $ProjectRoot $script), [ref]$parseTokens, [ref]$parseErrors) | Out-Null
        if ($parseErrors.Count -gt 0) {
            $syntaxOk = $false
            $syntaxMessages.Add("FAIL ${script}: $($parseErrors -join '; ')")
        } else { $syntaxMessages.Add("PASS PowerShell syntax: $script") }
    }
    $syntaxMessages | Set-Content -LiteralPath (Join-Path $ProjectRoot 'checks/powershell_parse.log') -Encoding UTF8
    $syntaxMessages | Write-Output
    $checks.Add([pscustomobject]@{name='powershell_syntax'; status=$(if ($syntaxOk) { 'PASS' } else { 'FAIL' }); exit_code=$(if ($syntaxOk) { 0 } else { 1 })})
    if (-not $PythonPath) {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if ($pythonCommand) { $PythonPath = $pythonCommand.Source }
        else { $PythonPath = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' }
    }
    function Run-Check([string]$Name, [string]$Executable, [string[]]$Arguments) {
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $output = & $Executable @Arguments 2>&1 | ForEach-Object { $_.ToString() }
        $code = $LASTEXITCODE
        $ErrorActionPreference = $previousPreference
        $output | Set-Content -LiteralPath (Join-Path $ProjectRoot "checks/$Name.log") -Encoding UTF8
        $output | Write-Output
        $status = if ($code -eq 0) { 'PASS' } else { 'FAIL' }
        $checks.Add([pscustomobject][ordered]@{name=$Name; status=$status; exit_code=$code})
    }
    if (Test-Path -LiteralPath $PythonPath) {
        Run-Check 'task1' $PythonPath @('-B', 'run_python_tests.py', 'task1')
        Run-Check 'task2_rpc_unit' $PythonPath @('-B', 'run_python_tests.py', 'task2')
        Run-Check 'task3' $PythonPath @('-B', 'run_python_tests.py', 'task3')
        Run-Check 'artifacts' $PythonPath @('-B', 'verify_artifacts.py')
    } else { $checks.Add([pscustomobject][ordered]@{name='python'; status='BLOCKED'; reason='Python unavailable'}) }
    $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
    if ($nodeCommand) { Run-Check 'assembler' $nodeCommand.Source @('task1/build_program.mjs', '--check') }
    else { $checks.Add([pscustomobject][ordered]@{name='assembler'; status='BLOCKED'; reason='Node unavailable'}) }
    $forgePath = Join-Path $ProjectRoot '.tools/bin/forge.exe'
    $solcPath = Join-Path $ProjectRoot '.tools/bin/solc.exe'
    if ((Test-Path -LiteralPath $forgePath) -and (Test-Path -LiteralPath $solcPath)) {
        # Same working directory as the standalone Anvil scenario and readFile fixtures.
        Push-Location (Join-Path $ProjectRoot 'task4')
        try { Run-Check 'foundry' $forgePath @('test', '-vv') }
        finally { Pop-Location }
    } else {
        $checks.Add([pscustomobject][ordered]@{name='foundry'; status='BLOCKED'; reason='Local forge.exe and/or solc.exe unavailable; see checks/install_results.json'})
        'BLOCKED: forge.exe and/or solc.exe unavailable; no Solidity tests executed' | Set-Content -LiteralPath checks/foundry.log -Encoding UTF8
    }
    $checks | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath checks/results.json -Encoding UTF8
    $checks | Format-Table -AutoSize
    if ($checks.status -contains 'FAIL') { exit 1 }
    if ($checks.status -contains 'BLOCKED') { exit 2 }
} finally { Pop-Location }
