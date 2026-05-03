# MetroEyes - Cloudflare named tunnel automated setup
#
# Pre-requisites:
#   1. Cloudflare account + zone (DNS via Cloudflare)
#   2. cloudflared installed (winget install Cloudflare.cloudflared)
#   3. Run from a fresh PowerShell session
#
# Usage:
#   .\scripts\setup_cloudflared.ps1 -Domain app.allthatai.kr
#   .\scripts\setup_cloudflared.ps1 -Domain app.example.com -NoPush

param(
    [Parameter(Mandatory)] [string]$Domain,
    [string]$TunnelName = "metroeyes",
    [int]$Port = 8765,
    [switch]$NoPush
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Locate cloudflared
$cf = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $cf) {
    $cf = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"
}
if (-not (Test-Path $cf)) { Write-Error "cloudflared not found. Run: winget install Cloudflare.cloudflared"; exit 1 }
Write-Host "cloudflared: $cf"

# Step 1: Auth (one-time)
$cred = "$env:USERPROFILE\.cloudflared"
if (-not (Test-Path "$cred\cert.pem")) {
    Write-Host "[1/6] Cloudflare auth - browser opens. Pick zone and approve." -ForegroundColor Cyan
    & $cf tunnel login
}

# Step 2: Create or reuse tunnel
$listOut = & $cf tunnel list 2>$null | Out-String
if ($listOut -notmatch [regex]::Escape($TunnelName)) {
    Write-Host "[2/6] Creating tunnel: $TunnelName" -ForegroundColor Cyan
    & $cf tunnel create $TunnelName | Out-Host
} else {
    Write-Host "[2/6] Tunnel '$TunnelName' already exists - reusing" -ForegroundColor Gray
}

# Extract UUID
$listOut = & $cf tunnel list 2>$null | Out-String
$uuidLine = ($listOut -split "`n") | Where-Object { $_ -match $TunnelName } | Select-Object -First 1
$uuid = ($uuidLine -split '\s+' | Where-Object { $_ -match '^[a-f0-9]{8}-[a-f0-9]{4}-' } | Select-Object -First 1)
if (-not $uuid) { Write-Error "Failed to extract tunnel UUID"; exit 1 }
Write-Host "  UUID: $uuid"

# Step 3: DNS routing
Write-Host "[3/6] DNS route: $Domain -> $TunnelName" -ForegroundColor Cyan
& $cf tunnel route dns $TunnelName $Domain 2>$null | Out-Host

# Step 4: Write config (ASCII-safe lines, no here-string)
$configPath = Join-Path $root "cloudflared-config.yml"
$cfgLines = @(
    "tunnel: $uuid",
    "credentials-file: $cred\$uuid.json",
    "",
    "ingress:",
    "  - hostname: $Domain",
    "    service: http://localhost:$Port",
    "    originRequest:",
    "      noTLSVerify: true",
    "  - service: http_status:404"
)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($configPath, $cfgLines, $utf8NoBom)
Write-Host "[4/6] Config written: $configPath" -ForegroundColor Cyan

# Step 5: Patch frontend wss URLs (UTF-8 explicit)
if (-not $NoPush) {
    Write-Host "[5/6] Patching frontend wss URLs to wss://$Domain" -ForegroundColor Cyan
    $newWss = "wss://$Domain"
    $files = @(
        "frontend\operator_web\realbev.html",
        "frontend\operator_web\index.html",
        "frontend\operator_web\bus.html",
        "frontend\passenger_app\index.html",
        "frontend\passenger_app\onboard.html",
        ".github\workflows\pages.yml"
    )
    foreach ($f in $files) {
        $p = Join-Path $root $f
        if (Test-Path $p) {
            $c = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)
            $c2 = $c -replace 'wss://[a-z0-9\-]+\.trycloudflare\.com', $newWss
            $c2 = $c2 -replace 'wss://[a-z0-9\-]+\.ngrok-free\.dev', $newWss
            $c2 = $c2 -replace 'wss://[a-z0-9\-]+\.ngrok\.io', $newWss
            if ($c -ne $c2) {
                [System.IO.File]::WriteAllText($p, $c2, $utf8NoBom)
                Write-Host "  patched: $f" -ForegroundColor Gray
            }
        }
    }
    Write-Host "[6/6] git commit + push" -ForegroundColor Cyan
    & git -c "user.name=leelang7" -c "user.email=leescvsir@gmail.com" add frontend\ .github\workflows\pages.yml | Out-Host
    & git -c "user.name=leelang7" -c "user.email=leescvsir@gmail.com" commit -m "feat: switch to permanent Cloudflare domain wss://$Domain" | Out-Host
    & git push origin main | Out-Host
    Write-Host "  GitHub Pages will redeploy in 1-2 minutes." -ForegroundColor Green
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "  External demo URL : https://leelang7.github.io/MetroEyes/" -ForegroundColor Yellow
Write-Host "  WS endpoint       : wss://$Domain" -ForegroundColor Yellow
Write-Host ""
Write-Host "Start tunnel (foreground):" -ForegroundColor Cyan
Write-Host "  cloudflared tunnel --config $configPath run"
Write-Host "Or double-click start_silent.vbs (auto-detects cloudflared-config.yml)"
