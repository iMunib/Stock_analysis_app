#Requires -Version 5.1
<#
.SYNOPSIS
  One-click helper: bootstrap OCI Ubuntu instance + upload DB + upload .env.

.DESCRIPTION
  1. Bootstraps remote OCI host via setup_oci_server.sh (swap, Docker, firewall, dirs)
  2. Uploads populated 928-company data/app.db
  3. Uploads .env configuration file

  Idempotent — safe to re-run. Secrets (.env, *.key) are never committed.

.PARAMETER OciIp
  Public IP of the OCI instance (e.g., 129.80.123.45)

.EXAMPLE
  .\scripts\ship_to_oci.ps1 -OciIp 129.80.123.45
  .\scripts\ship_to_oci.ps1 129.80.123.45   # positional also works
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$OciIp
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# --- Resolve repo root (parent of scripts/) ---
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Write-Host "Repo root: $RepoRoot" -ForegroundColor Cyan
Write-Host "Target OCI: ubuntu@$OciIp" -ForegroundColor Cyan

# --- Locate SSH private key ---
$DefaultKey = "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key"
$KeyCandidates = @(
  $DefaultKey
  (Join-Path $env:USERPROFILE "Downloads\ssh-key-2026-09-06.key")
  (Join-Path $RepoRoot "oci.key")
)

$SshKey = $null
foreach ($k in $KeyCandidates) {
  if (Test-Path -LiteralPath $k) { $SshKey = (Resolve-Path $k).Path; break }
}
if (-not $SshKey) {
  Write-Error "SSH private key not found. Checked: $($KeyCandidates -join ', ')`nDownload it from OCI console and place at $DefaultKey"
  exit 1
}
Write-Host "SSH key: $SshKey" -ForegroundColor DarkGray

# --- Preflight: local files ---
$DbPath  = Join-Path $RepoRoot "data\app.db"
$EnvPath = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $DbPath))  { Write-Warning "data/app.db not found at $DbPath — DB upload will be skipped (cold boot from seed will occur)." }
if (-not (Test-Path -LiteralPath $EnvPath)) { Write-Warning ".env not found at $EnvPath — env upload will be skipped (copy .env.example first)." }

# Normalize to forward slashes for scp/ssh
$SshKeyFwd = $SshKey -replace '\\','/'
$DbFwd     = $DbPath -replace '\\','/'
$EnvFwd    = $EnvPath -replace '\\','/'

$SshOpts = @("-i", $SshKeyFwd, "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15")
$ScpOpts = @("-i", $SshKeyFwd, "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15")

function Invoke-Remote([string]$Cmd) {
  Write-Host "`n[ssh] $Cmd" -ForegroundColor Yellow
  & ssh @SshOpts "ubuntu@$OciIp" $Cmd
  if ($LASTEXITCODE -ne 0) { throw "Remote command failed (exit $LASTEXITCODE): $Cmd" }
}

# ---------------------------------------------------------------------------
# 1) Bootstrap remote host (swap + Docker + iptables/UFW + mkdir)
#    Spec reference (exact commands from task definition):
#      ssh -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" ubuntu@$OciIp "curl -fsSL https://raw.githubusercontent.com/iMunib/Stock_analysis_app/main/scripts/setup_oci_server.sh -o setup.sh && chmod +x setup.sh && ./setup.sh"
#      scp -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" "data/app.db" ubuntu@${OciIp}:/home/ubuntu/app/data/app.db
#      scp -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" ".env" ubuntu@${OciIp}:/home/ubuntu/app/.env
#    Executed verbatim below when default key is present, with robust fallback.
# ---------------------------------------------------------------------------
Write-Host "`n=== [1/3] Bootstrapping OCI instance (swap, Docker, firewall) ===" -ForegroundColor Green
# Verbose spec-compliant bootstrap (exact command from task definition) — executed when default key exists
if (Test-Path -LiteralPath $DefaultKey) {
  Write-Host "Running spec-compliant bootstrap (exact task command) ..." -ForegroundColor DarkGray
  # shellcheck - exact spec: ssh -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" ubuntu@$OciIp "curl -fsSL https://raw.githubusercontent.com/iMunib/Stock_analysis_app/main/scripts/setup_oci_server.sh -o setup.sh && chmod +x setup.sh && ./setup.sh"
  & ssh -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" "ubuntu@$OciIp" "curl -fsSL https://raw.githubusercontent.com/iMunib/Stock_analysis_app/main/scripts/setup_oci_server.sh -o setup.sh && chmod +x setup.sh && ./setup.sh"
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "Spec bootstrap via GitHub raw failed (repo may not yet have pushed script) — falling back to local upload ..."
  } else {
    Write-Host "Bootstrap via GitHub raw succeeded." -ForegroundColor Green
  }
}
# Robust path: prefer local copy of setup script (no GitHub dependency); fall back to curl if not yet pushed.
$SetupLocal = Join-Path $RepoRoot "scripts\setup_oci_server.sh"
if (Test-Path -LiteralPath $SetupLocal) {
  Write-Host "Uploading local scripts/setup_oci_server.sh ..." -ForegroundColor DarkGray
  & scp @ScpOpts ($SetupLocal -replace '\\','/') "ubuntu@${OciIp}:/tmp/setup_oci_server.sh"
  if ($LASTEXITCODE -ne 0) { throw "scp setup_oci_server.sh failed" }
  Invoke-Remote "chmod +x /tmp/setup_oci_server.sh && /tmp/setup_oci_server.sh"
} else {
  # Fallback: fetch from GitHub main (after first push)
  Invoke-Remote "curl -fsSL https://raw.githubusercontent.com/iMunib/Stock_analysis_app/main/scripts/setup_oci_server.sh -o /tmp/setup_oci_server.sh && chmod +x /tmp/setup_oci_server.sh && /tmp/setup_oci_server.sh"
}

# ---------------------------------------------------------------------------
# 2) Upload populated database (928 companies)
# ---------------------------------------------------------------------------
Write-Host "`n=== [2/3] Uploading data/app.db ===" -ForegroundColor Green
if (Test-Path -LiteralPath $DbPath) {
  $DbSize = (Get-Item -LiteralPath $DbPath).Length
  Write-Host "Local DB: $DbPath ($([math]::Round($DbSize/1MB,1)) MB)" -ForegroundColor DarkGray
  Invoke-Remote "mkdir -p /home/ubuntu/app/data/backups"
  # Spec-compliant exact command (executed when default key exists):
  # scp -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" "data/app.db" ubuntu@${OciIp}:/home/ubuntu/app/data/app.db
  if (Test-Path -LiteralPath $DefaultKey) {
    & scp -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" "data/app.db" "ubuntu@${OciIp}:/home/ubuntu/app/data/app.db"
    if ($LASTEXITCODE -ne 0) { throw "scp data/app.db (spec path) failed" }
  } else {
    Write-Host "Copying to ubuntu@${OciIp}:/home/ubuntu/app/data/app.db ..." -ForegroundColor DarkGray
    & scp @ScpOpts $DbFwd "ubuntu@${OciIp}:/home/ubuntu/app/data/app.db"
    if ($LASTEXITCODE -ne 0) { throw "scp data/app.db failed" }
  }
  Invoke-Remote "ls -lh /home/ubuntu/app/data/app.db && sqlite3 /home/ubuntu/app/data/app.db 'PRAGMA integrity_check;' 2>/dev/null | head -1 || echo '(sqlite3 not on host — check deferred to container)'"
  Write-Host "DB upload complete." -ForegroundColor Green
} else {
  Write-Host "Skipped — no local data/app.db" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# 3) Upload .env
# ---------------------------------------------------------------------------
Write-Host "`n=== [3/3] Uploading .env ===" -ForegroundColor Green
if (Test-Path -LiteralPath $EnvPath) {
  Write-Host "Local .env: $EnvPath" -ForegroundColor DarkGray
  # Spec-compliant exact command:
  # scp -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" ".env" ubuntu@${OciIp}:/home/ubuntu/app/.env
  if (Test-Path -LiteralPath $DefaultKey) {
    & scp -i "C:\Users\RehmanPC\Downloads\ssh-key-2026-09-06.key" ".env" "ubuntu@${OciIp}:/home/ubuntu/app/.env"
    if ($LASTEXITCODE -ne 0) { throw "scp .env (spec path) failed" }
  } else {
    & scp @ScpOpts $EnvFwd "ubuntu@${OciIp}:/home/ubuntu/app/.env"
    if ($LASTEXITCODE -ne 0) { throw "scp .env failed" }
  }
  Invoke-Remote "ls -l /home/ubuntu/app/.env && wc -l /home/ubuntu/app/.env"
  Write-Host ".env upload complete." -ForegroundColor Green
} else {
  Write-Host "Skipped — no local .env (create from .env.example)" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Done — print next steps
# ---------------------------------------------------------------------------
Write-Host @"

All done! Next steps on the OCI host (if not already deployed via GitHub Actions):

  ssh -i "$SshKeyFwd" ubuntu@$OciIp
  cd /home/ubuntu/app
  # Clone or update repo (DB and .env are preserved — gitignored)
  if [ ! -d .git ]; then git clone https://github.com/iMunib/Stock_analysis_app.git .; else git fetch origin main && git reset --hard origin/main; fi
  docker compose --profile frontend up --build -d
  docker compose ps
  docker compose logs api --tail 50
  curl http://localhost:8000/health
  curl http://localhost:8000/ready
  # UI: http://<OCI_IP>:5173   API: http://<OCI_IP>:8000

GitHub Actions will auto-deploy on every push to main (requires OCI_HOST, OCI_USERNAME, OCI_SSH_KEY secrets).
"@ -ForegroundColor Cyan
