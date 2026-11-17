# EduRecommend: install EVERYTHING on a fresh Windows 10/11 laptop, then set up the project.
#
# 1. Extract EduRecommend-project.zip (e.g. to Documents\EduRecommend).
# 2. Open that folder in File Explorer, type  powershell  in the address bar, press Enter.
# 3. Run:
#      powershell -ExecutionPolicy Bypass -File scripts\install-everything.ps1
#
# It installs (only what is missing): Git, Google Chrome, uv (Python), Flutter.
# Safe to run again: it skips anything already installed.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$flutterDir = Join-Path $env:USERPROFILE 'flutter'

function Step($t) { Write-Host "`n== $t" -ForegroundColor Cyan }
function Ok($t) { Write-Host "   OK  $t" -ForegroundColor Green }
function Info($t) { Write-Host "   $t" -ForegroundColor Gray }
function Warn($t) { Write-Host "   !  $t" -ForegroundColor Yellow }

function Refresh-Path {
    # Pick up PATH changes made by installers without opening a new window.
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
    foreach ($extra in @("$env:USERPROFILE\.local\bin", "$flutterDir\bin")) {
        if ((Test-Path $extra) -and ($env:Path -notlike "*$extra*")) { $env:Path += ";$extra" }
    }
}

function Has($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

function Has-Chrome {
    [bool](@("$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
            "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
            "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ })
}

Refresh-Path

Step 'Checking this laptop'
$plan = @()
if (Has 'git') { Ok 'Git' } else { $plan += 'Git' }
if (Has-Chrome) { Ok 'Google Chrome' } else { $plan += 'Google Chrome' }
if (Has 'uv') { Ok 'uv (Python)' } else { $plan += 'uv (Python)' }
if ((Has 'flutter') -or (Test-Path "$flutterDir\bin\flutter.bat")) { Ok 'Flutter' } else { $plan += 'Flutter (about 2 GB)' }

# Smart App Control blocks Flutter's tools. We only warn; the laptop owner decides.
try {
    $sac = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy' -ErrorAction Stop).VerifiedAndReputablePolicyState
    if ($sac -eq 1) {
        Warn 'Windows Smart App Control is ON. It blocks parts of Flutter, so the apps will not build.'
        Warn 'To turn it off: Windows Security > App & browser control > Smart App Control > Off.'
        Warn 'Note: it cannot be turned back on without resetting Windows. The laptop owner should decide.'
    } elseif ($sac -eq 2) {
        Warn 'Smart App Control is in Evaluation mode; it may block Flutter. If builds fail, see the guide.'
    }
} catch { }

if ($plan.Count -gt 0) {
    Write-Host "`nThis will download and install: $($plan -join ', ')." -ForegroundColor White
    Write-Host 'Each tool has its own licence (Git: GPL, Chrome: Google terms, uv: MIT/Apache, Flutter: BSD).' -ForegroundColor White
    $answer = Read-Host 'Install them now and accept those licences? Type Y and press Enter'
    if ($answer -notmatch '^[Yy]') { Write-Host 'Nothing installed.'; exit 1 }

    $needWinget = ($plan -contains 'Git') -or ($plan -contains 'Google Chrome') -or ($plan -contains 'uv (Python)')
    if ($needWinget -and -not (Has 'winget')) {
        Warn 'winget (Windows App Installer) is missing. Install "App Installer" from the Microsoft Store, then run this again.'
        exit 1
    }
    $wingetArgs = @('--silent', '--accept-package-agreements', '--accept-source-agreements', '--scope', 'user')

    if ($plan -contains 'Git') {
        Step 'Installing Git'
        winget install --id Git.Git -e @wingetArgs
        if ($LASTEXITCODE -ne 0) { winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements }
    }
    if ($plan -contains 'Google Chrome') {
        Step 'Installing Google Chrome'
        winget install --id Google.Chrome -e @wingetArgs
        if ($LASTEXITCODE -ne 0) { winget install --id Google.Chrome -e --silent --accept-package-agreements --accept-source-agreements }
    }
    if ($plan -contains 'uv (Python)') {
        Step 'Installing uv'
        winget install --id astral-sh.uv -e @wingetArgs
        if ($LASTEXITCODE -ne 0) {
            Info 'winget could not install uv; using the official installer instead.'
            powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        }
    }
    Refresh-Path

    if ($plan -contains 'Flutter (about 2 GB)') {
        Step 'Downloading Flutter (stable). This takes a while...'
        if (-not (Has 'git')) { throw 'Git is still not available. Close this window, open a new one, and run the script again.' }
        if (-not (Test-Path "$flutterDir\bin\flutter.bat")) {
            git clone --depth 1 -b stable https://github.com/flutter/flutter.git $flutterDir
            if ($LASTEXITCODE -ne 0) { throw 'Downloading Flutter failed. Check the internet connection and run again.' }
        }
        $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
        if ($userPath -notlike "*$flutterDir\bin*") {
            [Environment]::SetEnvironmentVariable('Path', ($userPath.TrimEnd(';') + ";$flutterDir\bin"), 'User')
            Ok "Added $flutterDir\bin to your Path"
        }
        Refresh-Path
        Info 'First Flutter start (downloads its tools)...'
        flutter --disable-analytics | Out-Null
        flutter --version
    }
}

Step 'All tools ready - setting up the project'
Refresh-Path
& powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'setup.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`nDone! Start the app any time with:" -ForegroundColor Green
Write-Host '   powershell -ExecutionPolicy Bypass -File scripts\start.ps1' -ForegroundColor Green
