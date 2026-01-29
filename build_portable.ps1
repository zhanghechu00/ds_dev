# build_portable.ps1 - Create Portable Python Environment
$ErrorActionPreference = "Stop"

# Configuration
$PythonVer = "3.13.1"
$PythonUrl = "https://www.python.org/ftp/python/$PythonVer/python-$PythonVer-embed-amd64.zip"
$TargetDir = Join-Path $PSScriptRoot "portable_env"
$PipScriptUrl = "https://bootstrap.pypa.io/get-pip.py"

Write-Host "=== Building Portable Python Environment ===" -ForegroundColor Cyan

# 1. Prepare Directory
if (Test-Path $TargetDir) {
    Write-Host "Cleaning old portable_env..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $TargetDir
}
New-Item -ItemType Directory -Path $TargetDir | Out-Null

# 2. Download and Extract Python Embeddable
$ZipPath = Join-Path $env:TEMP "python-embed.zip"
Write-Host "Downloading Python $PythonVer (approx. 10-20MB)..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $PythonUrl -OutFile $ZipPath
} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Extracting..." -ForegroundColor Cyan
Expand-Archive -Path $ZipPath -DestinationPath $TargetDir -Force
Remove-Item $ZipPath

# 3. Enable site-packages (Critical: Edit ._pth to allow pip)
Write-Host "Configuring Python for third-party libraries..." -ForegroundColor Cyan
$PthFile = Get-ChildItem $TargetDir -Filter "*._pth" | Select-Object -First 1
if ($PthFile) {
    $Content = Get-Content $PthFile.FullName
    # Uncomment 'import site'
    $NewContent = $Content -replace "#import site", "import site"
    Set-Content $PthFile.FullName $NewContent
}

$PythonExe = Join-Path $TargetDir "python.exe"

# 4. Install pip
Write-Host "Installing pip..." -ForegroundColor Cyan
$GetPipPath = Join-Path $TargetDir "get-pip.py"
Invoke-WebRequest -Uri $PipScriptUrl -OutFile $GetPipPath

& $PythonExe $GetPipPath --no-warn-script-location
Remove-Item $GetPipPath

# 5. Install Dependencies (Using Python 3.11+ tomllib)
Write-Host "Installing dependencies..." -ForegroundColor Cyan

if (Test-Path "pyproject.toml") {
    # Extract dependencies using embedded python's tomllib
    $ParserScript = @"
import tomllib
import sys

try:
    with open('pyproject.toml', 'rb') as f:
        data = tomllib.load(f)
        deps = data.get('project', {}).get('dependencies', [])
        for d in deps:
            print(d)
except Exception as e:
    sys.exit(1)
"@
    $ParserFile = Join-Path $TargetDir "parse_deps.py"
    Set-Content -Path $ParserFile -Value $ParserScript
    
    try {
        $Deps = & $PythonExe $ParserFile
        if ($LASTEXITCODE -eq 0 -and $Deps) {
            Write-Host "Found dependencies: $Deps" -ForegroundColor Green
            & $PythonExe -m pip install $Deps --no-warn-script-location
        } else {
             Write-Host "Could not parse dependencies from pyproject.toml, falling back to manual install or skipping." -ForegroundColor Yellow
        }
    } finally {
        Remove-Item $ParserFile -ErrorAction SilentlyContinue
    }

} elseif (Test-Path "requirements.txt") {
     & $PythonExe -m pip install -r requirements.txt --no-warn-script-location
} else {
    Write-Host "Warning: No pyproject.toml or requirements.txt found." -ForegroundColor Yellow
}

# 6. Create Launch Script (BAT)
Write-Host "Generating start_portable.bat..." -ForegroundColor Cyan

$BatContent = @"
@echo off
set "BASE_DIR=%~dp0"
set "PYTHON_EXE=%BASE_DIR%portable_env\python.exe"

echo [Portable Mode] Using embedded Python...

REM Run main program
"%PYTHON_EXE%" "%BASE_DIR%mcp_server.py" %*

pause
"@

Set-Content -Path (Join-Path $PSScriptRoot "start_portable.bat") -Value $BatContent

Write-Host "`n=== Build Complete! ===" -ForegroundColor Green
Write-Host "You can now copy this entire folder to any machine." -ForegroundColor Green
Write-Host "Run 'start_portable.bat' to start." -ForegroundColor Green