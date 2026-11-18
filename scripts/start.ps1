# Starts EduRecommend: backend, student app and admin panel, each in its own window.
# Run from the project folder:
#   powershell -ExecutionPolicy Bypass -File scripts\start.ps1
# Close a window (or press Ctrl+C / q in it) to stop that part.

$root = Split-Path -Parent $PSScriptRoot

# Pick up tools installed after this window was opened.
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
foreach ($extra in @("$env:USERPROFILE\.local\bin", "$env:USERPROFILE\flutter\bin")) {
    if ((Test-Path $extra) -and ($env:Path -notlike "*$extra*")) { $env:Path += ";$extra" }
}
$missing = @('uv', 'flutter') | Where-Object { -not (Get-Command $_ -ErrorAction SilentlyContinue) }
if ($missing) {
    Write-Host "Not installed yet: $($missing -join ', ')." -ForegroundColor Red
    Write-Host 'Run this first, type Y when asked, and wait for "Done!":' -ForegroundColor Yellow
    Write-Host '   powershell -ExecutionPolicy Bypass -File scripts\install-everything.ps1' -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path "$root\backend\.venv")) {
    Write-Host 'The project is not set up yet. Run this first:' -ForegroundColor Yellow
    Write-Host '   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1' -ForegroundColor Yellow
    exit 1
}

$flutterPath = @("$env:USERPROFILE\flutter\bin", 'C:\flutter\bin', 'C:\src\flutter\bin') |
    Where-Object { Test-Path "$_\flutter.bat" } | Select-Object -First 1
$addPath = if ($flutterPath) { "`$env:Path += ';$flutterPath'; " } else { '' }

function Open-Window($title, $folder, $command) {
    $script = "$addPath`$Host.UI.RawUI.WindowTitle = '$title'; Set-Location '$root\$folder'; $command"
    Start-Process powershell -ArgumentList '-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $script
}

Open-Window 'EduRecommend backend' 'backend' 'uv run python -m uvicorn app.main:app --port 8000'

Write-Host 'Waiting for the backend to start...'
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        Invoke-RestMethod -Uri 'http://localhost:8000/health' -TimeoutSec 2 | Out-Null
        $ready = $true
        break
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $ready) {
    Write-Host 'The backend did not start. Look at the "EduRecommend backend" window for the error.' -ForegroundColor Red
    exit 1
}
Write-Host 'Backend is running: http://localhost:8000/docs' -ForegroundColor Green

Open-Window 'EduRecommend student app' 'mobile' 'flutter run -d chrome --web-port 5173'
Open-Window 'EduRecommend admin panel' 'admin' 'flutter run -d chrome --web-port 5174'

Write-Host 'Student app and admin panel are building - Chrome opens in about a minute.'
Write-Host 'Admin login: admin@example.com or verifier@example.com, password = the line in backend\.env'
