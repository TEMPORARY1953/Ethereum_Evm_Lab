param([int]$Port = 8545)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$TaskRoot = Join-Path $ProjectRoot 'task4'
$Bin = Join-Path $ProjectRoot '.tools/bin'
foreach ($tool in @('forge', 'cast', 'anvil', 'solc')) {
    if (-not (Test-Path -LiteralPath (Join-Path $Bin "$tool.exe"))) {
        throw "Missing .tools/bin/$tool.exe; see .tools/README.md"
    }
}
if ($Port -lt 1024 -or $Port -gt 65535) { throw 'Invalid port' }
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    throw "Port $Port is occupied; refusing to use an unknown RPC server"
}
$rpc = "http://127.0.0.1:$Port"
$nodeProcess = $null
Push-Location $TaskRoot
try {
    & "$Bin/forge.exe" test -vv
    if ($LASTEXITCODE -ne 0) { throw 'Foundry tests failed' }
    # Silent mode avoids printing Anvil's public development private keys to logs.
    $nodeProcess = Start-Process -FilePath "$Bin/anvil.exe" -ArgumentList @('--silent', '--host', '127.0.0.1', '--port', "$Port", '--chain-id', '31337', '--hardfork', 'cancun') -WindowStyle Hidden -PassThru -RedirectStandardOutput "$TaskRoot/anvil.log" -RedirectStandardError "$TaskRoot/anvil.err.log"
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 200
        if ($nodeProcess.HasExited) { throw 'Anvil exited unexpectedly' }
        try {
            $response = Invoke-RestMethod -Uri $rpc -Method Post -ContentType 'application/json' -Body '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}'
            if ($response.result -eq '0x7a69') { $ready = $true; break }
        } catch { }
    }
    if (-not $ready) { throw 'Anvil readiness check failed' }
    $accounts = & "$Bin/cast.exe" rpc eth_accounts --rpc-url $rpc | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or -not $accounts[0]) { throw 'Cannot get local unlocked account' }
    $owner = $accounts[0]
    # Lowercase has the same 20-byte identity and avoids mixed-case checksum ambiguity.
    $recipient = '0x4a097d48ef380b479773eb609511a49cf17020f4'
    $deployJson = & "$Bin/forge.exe" create src/LabToken.sol:LabToken --rpc-url $rpc --unlocked --from $owner --broadcast --json --constructor-args 'Vmk Rulit Token' 'VMKRULIT' $owner
    if ($LASTEXITCODE -ne 0) { throw 'Local deployment failed' }
    $deployment = $deployJson | ConvertFrom-Json
    $contract = $deployment.deployedTo
    if (-not $contract) { throw 'No deployedTo in Foundry result' }
    $mintJson = & "$Bin/cast.exe" send $contract 'mint(address,uint256)' $owner 1000000000000000000 --rpc-url $rpc --unlocked --from $owner --json
    if ($LASTEXITCODE -ne 0) { throw 'Local mint failed' }
    $mint = $mintJson | ConvertFrom-Json
    $transferJson = & "$Bin/cast.exe" send $contract 'transfer(address,uint256)' $recipient 1000000000000000000 --rpc-url $rpc --unlocked --from $owner --json
    if ($LASTEXITCODE -ne 0) { throw 'Local transfer failed' }
    $transfer = $transferJson | ConvertFrom-Json
    $balance = & "$Bin/cast.exe" call $contract 'balanceOf(address)(uint256)' $recipient --rpc-url $rpc
    if ($LASTEXITCODE -ne 0 -or $balance.Trim().Split(' ')[0] -ne '1000000000000000000') { throw "Wrong recipient balance: $balance" }
    $result = [ordered]@{network='LOCAL ANVIL ONLY'; chainId=31337; contract=$contract; deploymentHash=$deployment.transactionHash; mintReceipt=$mint; transferReceipt=$transfer; recipient=$recipient; recipientBalanceBaseUnits='1000000000000000000'}
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath local_demo_result.json -Encoding UTF8
    Write-Output 'Local Anvil deployment, mint and transfer completed; result: task4/local_demo_result.json'
} finally {
    if ($nodeProcess -and -not $nodeProcess.HasExited) { Stop-Process -Id $nodeProcess.Id }
    Pop-Location
}
