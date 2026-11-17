# EduRecommend one-time setup for a new Windows laptop.
# Run from the project folder:
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Step($text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Ok($text) { Write-Host "   OK  $text" -ForegroundColor Green }
function Fail($text) { Write-Host "   MISSING  $text" -ForegroundColor Red }

# Flutter may be installed but not on PATH in this window yet.
foreach ($p in @("$env:USERPROFILE\flutter\bin", 'C:\flutter\bin', 'C:\src\flutter\bin')) {
    if ((Test-Path "$p\flutter.bat") -and ($env:Path -notlike "*$p*")) { $env:Path += ";$p" }
}

Step 'Checking tools'
$missing = @()
foreach ($tool in @(
        @{ Name = 'git'; Help = 'Git for Windows: https://git-scm.com/download/win' },
        @{ Name = 'uv'; Help = 'uv (Python manager): run  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"' },
        @{ Name = 'flutter'; Help = 'Flutter SDK: https://docs.flutter.dev/get-started/install/windows' })) {
    if (Get-Command $tool.Name -ErrorAction SilentlyContinue) { Ok $tool.Name }
    else { Fail "$($tool.Name)  ->  $($tool.Help)"; $missing += $tool.Name }
}
$chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ }
if ($chrome) { Ok 'Google Chrome' } else { Fail 'Google Chrome  ->  https://www.google.com/chrome/'; $missing += 'chrome' }
if ($missing.Count -gt 0) {
    Write-Host "`nInstall the missing tools above, open a NEW PowerShell window, and run this script again." -ForegroundColor Yellow
    exit 1
}

Step 'Installing backend packages (Python is downloaded automatically if needed)'
Push-Location backend
uv sync
if ($LASTEXITCODE -ne 0) {
    Write-Host '   Retrying with Windows certificates (needed on some networks)...' -ForegroundColor Yellow
    uv sync --system-certs
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw 'uv sync failed. See the messages above.' }
}
Pop-Location
Ok 'backend'

Step 'Installing Flutter packages'
foreach ($app in @('mobile', 'admin')) {
    Push-Location $app
    flutter pub get
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw "flutter pub get failed in $app." }
    Pop-Location
    Ok $app
}

Step 'Local settings (backend\.env)'
$envFile = Join-Path $root 'backend\.env'
if (Test-Path $envFile) {
    Ok 'backend\.env already exists - left unchanged'
} else {
    $bytes = New-Object byte[] 9
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $password = 'Dev-' + ([Convert]::ToBase64String($bytes) -replace '[+/=]', 'x')
    Set-Content -Path $envFile -Encoding ascii -Value @(
        '# Local development settings for this laptop (not shared, not committed).',
        "UNIRAH_DEV_STAFF_PASSWORD=$password")
    Ok 'Created backend\.env with a new random staff password'
}

Step 'Quick check of the backend'
Push-Location backend
uv run python -m pytest -q -p no:warnings
$testsOk = $LASTEXITCODE -eq 0
Pop-Location
if ($testsOk) { Ok 'backend tests passed' } else { Write-Host '   Some backend tests failed - see above.' -ForegroundColor Yellow }

Write-Host "`nSetup finished." -ForegroundColor Green
Write-Host 'Next: powershell -ExecutionPolicy Bypass -File scripts\start.ps1'
Write-Host 'Admin login: admin@example.com or verifier@example.com, password = the line in backend\.env'
