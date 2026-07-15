# SupplyCore one-click installer for Windows (Docker Desktop).
# Right-click > "Run with PowerShell", or:  powershell -ExecutionPolicy Bypass -File install.ps1
#
# Optional env vars: GHCR_USER, GHCR_TOKEN, SITE_NAME, ADMIN_PASSWORD, DB_PASSWORD, HTTP_PORT, IMAGE_TAG
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Say  ($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Warn ($m) { Write-Host "!!  $m" -ForegroundColor Yellow }
function Die  ($m) { Write-Host "xx  $m" -ForegroundColor Red; exit 1 }
function Gen  { -join ((48..57)+(97..102) | Get-Random -Count 24 | ForEach-Object {[char]$_}) }

# --- 1. Docker -------------------------------------------------------------
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Die "Docker Desktop not found. Install it from https://www.docker.com/products/docker-desktop and start it, then re-run."
}
try { docker info | Out-Null } catch { Die "Docker Desktop is installed but not running. Start it (whale icon) and re-run." }
try { docker compose version | Out-Null } catch { Die "Docker Compose v2 not available. Update Docker Desktop." }

# --- 2. .env ---------------------------------------------------------------
function EnvVal($k, $def) { $v = [Environment]::GetEnvironmentVariable($k); if ($v) { return $v } else { return $def } }
if (-not (Test-Path ".env")) {
  Say "Creating .env…"
  Copy-Item ".env.example" ".env"
  $site  = EnvVal "SITE_NAME"      "supplycore.localhost"
  $admin = EnvVal "ADMIN_PASSWORD" (Gen)
  $dbpw  = EnvVal "DB_PASSWORD"    (Gen)
  $port  = EnvVal "HTTP_PORT"      "8080"
  $tag   = EnvVal "IMAGE_TAG"      "latest"
  (Get-Content ".env") `
    -replace '^SITE_NAME=.*',      "SITE_NAME=$site" `
    -replace '^ADMIN_PASSWORD=.*', "ADMIN_PASSWORD=$admin" `
    -replace '^DB_PASSWORD=.*',    "DB_PASSWORD=$dbpw" `
    -replace '^HTTP_PORT=.*',      "HTTP_PORT=$port" `
    -replace '^IMAGE_TAG=.*',      "IMAGE_TAG=$tag" | Set-Content ".env"
} else {
  Warn ".env already exists — reusing it."
}

# Load .env into a hashtable for later display.
$cfg = @{}
Get-Content ".env" | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object {
  $k,$v = $_ -split '=',2; $cfg[$k.Trim()] = $v.Trim()
}

# --- 3. GHCR login (private image) ----------------------------------------
$image = "$($cfg['IMAGE']):$($cfg['IMAGE_TAG'])"
& docker pull $image 2>$null
if ($LASTEXITCODE -ne 0) {
  Say "Logging in to GitHub Container Registry to pull the private image…"
  $user = if ($env:GHCR_USER) { $env:GHCR_USER } else { Read-Host "GitHub username" }
  if ($env:GHCR_TOKEN) { $tok = $env:GHCR_TOKEN }
  else { $sec = Read-Host "GitHub PAT (read:packages)" -AsSecureString
         $tok = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)) }
  $tok | docker login ghcr.io -u $user --password-stdin
  if ($LASTEXITCODE -ne 0) { Die "GHCR login failed." }
  docker pull $image
}

# --- 4. Up -----------------------------------------------------------------
Say "Starting the SupplyCore stack…"
docker compose up -d

Say "Waiting for first-run site creation (installs SupplyCore)…"
$ready = $false
for ($i = 1; $i -le 90; $i++) {
  $line = (docker compose ps -a --format '{{.Service}} {{.State}} {{.ExitCode}}' |
           Select-String '^create-site ') -replace '^create-site ', ''
  if ($line -match '^exited 0')   { Say "Site ready."; $ready = $true; break }
  if ($line -match '^exited [1-9]'){ docker compose logs create-site; Die "Site creation failed." }
  Write-Host ("    still working… ({0}/90)" -f $i)
  Start-Sleep -Seconds 10
}
if (-not $ready) { Warn "Site creation is taking long — check: docker compose logs -f create-site" }

# --- 5. Done ---------------------------------------------------------------
Write-Host ""
Write-Host "SupplyCore is up." -ForegroundColor Green
Write-Host "  URL:       http://localhost:$($cfg['HTTP_PORT'])"
Write-Host "  Login:     Administrator"
Write-Host "  Password:  $($cfg['ADMIN_PASSWORD'])"
Write-Host ""
Write-Host "  Logs:   docker compose logs -f backend"
Write-Host "  Stop:   docker compose down"
Write-Host "  Update: edit IMAGE_TAG in .env, re-run install.ps1 (then 'bench migrate' — see README)"
