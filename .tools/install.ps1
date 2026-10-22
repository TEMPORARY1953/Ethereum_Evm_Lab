param([string]$FoundryVersion = 'v1.8.6')
$ErrorActionPreference = 'Stop'
if ($FoundryVersion -notmatch '^v\d+\.\d+\.\d+$') { throw 'A stable Foundry version is required' }
if (-not [Environment]::Is64BitOperatingSystem) { throw 'Windows x64 is required' }
$ToolsRoot = $PSScriptRoot
$ProjectRoot = Split-Path $ToolsRoot -Parent
$Bin = Join-Path $ToolsRoot 'bin'
$Downloads = Join-Path $ToolsRoot 'downloads'
New-Item -ItemType Directory -Force $Bin, $Downloads, (Join-Path $ProjectRoot 'checks') | Out-Null
$results = [System.Collections.Generic.List[object]]::new()

function Download-File([string]$Url, [string]$Destination) {
    if (-not $Url.StartsWith('https://')) { throw 'HTTPS is required' }
    Write-Output "Downloading $Url"
    # No external installer, global PATH changes or writes to the user profile.
    & curl.exe --fail --location --silent --show-error --connect-timeout 10 --max-time 60 --user-agent 'Ethereum-Lab-Local-Installer' --output "$Destination.partial" $Url
    if ($LASTEXITCODE -ne 0) { throw "DOWNLOAD_FAILED: curl exit $LASTEXITCODE for $Url" }
    Move-Item -LiteralPath "$Destination.partial" -Destination $Destination -Force
}

function Assert-Sha256([string]$Path, [string]$Expected) {
    if ($Expected -notmatch '^[0-9a-fA-F]{64}$') { throw 'No valid official SHA-256 digest' }
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Expected.ToLowerInvariant()) { throw "SHA-256 mismatch: $Path" }
    Write-Output "SHA-256 verified: $([IO.Path]::GetFileName($Path))"
}

function Tool-Version([string]$Name) {
    $version = & (Join-Path $Bin "$Name.exe") --version
    if ($LASTEXITCODE -ne 0) { throw "$Name --version failed" }
    return ($version -join "`n")
}

try {
    $metadataFile = Join-Path $Downloads "foundry-$FoundryVersion.json"
    Download-File "https://api.github.com/repos/foundry-rs/foundry/releases/tags/$FoundryVersion" $metadataFile
    $release = Get-Content -LiteralPath $metadataFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($release.tag_name -ne $FoundryVersion -or $release.prerelease -or $release.draft) { throw 'Unexpected Foundry release' }
    $assets = @($release.assets | Where-Object { $_.name -match '_win32_amd64\.(zip|tar\.gz)$' })
    if ($assets.Count -ne 1) { throw 'Expected exactly one official Windows amd64 archive' }
    $asset = $assets[0]
    $prefix = "https://github.com/foundry-rs/foundry/releases/download/$FoundryVersion/"
    if (-not $asset.browser_download_url.StartsWith($prefix)) { throw 'Unexpected asset source' }
    if ($asset.digest -notmatch '^sha256:([0-9a-fA-F]{64})$') { throw 'Official GitHub asset SHA-256 digest is missing' }
    $expected = $Matches[1]
    $archive = Join-Path $Downloads $asset.name
    Download-File $asset.browser_download_url $archive
    Assert-Sha256 $archive $expected
    $staging = Join-Path $Downloads "foundry-$FoundryVersion-unpacked"
    New-Item -ItemType Directory -Force $staging | Out-Null
    $entries = & tar.exe -tf $archive
    if ($LASTEXITCODE -ne 0) { throw 'Cannot list Foundry archive' }
    foreach ($entry in $entries) {
        if ($entry -match '^[/\\]|^[a-zA-Z]:|(^|[/\\])\.\.([/\\]|$)') { throw 'Unsafe archive entry' }
    }
    & tar.exe -xf $archive -C $staging
    if ($LASTEXITCODE -ne 0) { throw 'Cannot extract Foundry archive' }
    $versions = [ordered]@{}
    foreach ($tool in @('forge','cast','anvil')) {
        $matchesInArchive = @(Get-ChildItem -LiteralPath $staging -Recurse -File -Filter "$tool.exe")
        if ($matchesInArchive.Count -ne 1) { throw "Missing or ambiguous $tool.exe" }
        Copy-Item -LiteralPath $matchesInArchive[0].FullName -Destination (Join-Path $Bin "$tool.exe") -Force
        $versions[$tool] = Tool-Version $tool
        Write-Output $versions[$tool]
    }
    $results.Add([pscustomobject]@{component='foundry'; status='PASS'; release=$FoundryVersion; source=$asset.browser_download_url; archive_sha256=$expected; versions=$versions})
} catch {
    $status = if ($_.Exception.Message.StartsWith('DOWNLOAD_FAILED:')) { 'BLOCKED' } else { 'FAIL' }
    $results.Add([pscustomobject]@{component='foundry'; status=$status; reason=$_.Exception.Message})
    Write-Output "$status Foundry: $($_.Exception.Message)"
}

try {
    # Official Solidity Windows binary and SHA-256 from its release index.
    $source = 'https://binaries.soliditylang.org/windows-amd64/solc-windows-amd64-v0.8.28+commit.7893614a.exe'
    $expected = '76a71001309810aafd0462d9b2f2612bf19b89550c866140edca26e533de06bc'
    $compiler = Join-Path $Downloads 'solc-0.8.28.exe'
    Download-File $source $compiler
    Assert-Sha256 $compiler $expected
    Copy-Item -LiteralPath $compiler -Destination (Join-Path $Bin 'solc.exe') -Force
    $version = Tool-Version 'solc'
    if ($version -notmatch '0\.8\.28\+commit\.7893614a') { throw 'Unexpected Solidity compiler version' }
    Write-Output $version
    $results.Add([pscustomobject]@{component='solc'; status='PASS'; source=$source; sha256=$expected; version=$version})
} catch {
    $status = if ($_.Exception.Message.StartsWith('DOWNLOAD_FAILED:')) { 'BLOCKED' } else { 'FAIL' }
    $results.Add([pscustomobject]@{component='solc'; status=$status; reason=$_.Exception.Message})
    Write-Output "$status Solidity: $($_.Exception.Message)"
}

[ordered]@{timestamp_utc=[DateTime]::UtcNow.ToString('o'); sandbox_network_disabled=($env:CODEX_SANDBOX_NETWORK_DISABLED -eq '1'); components=@($results.ToArray())} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ProjectRoot 'checks/install_results.json') -Encoding UTF8
if ($results.status -contains 'FAIL') { exit 1 }
if ($results.status -contains 'BLOCKED') { exit 2 }
