param(
  [string]$Url = "http://127.0.0.1:5001/",
  [int]$BallSize = 44
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $repo ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
  throw "Python venv not found at $py. Create it first (or adjust the path)."
}

& $py (Join-Path $repo "desktop_app.py") --url $Url --gui qt --ball-size $BallSize

