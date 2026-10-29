# Run from any directory; no activation or npm installation required.
param(
    [ValidateRange(1, 65535)]
    [int]$Port = 5281
)

$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$requirements = Join-Path $PSScriptRoot 'scout\requirements.txt'
$server = Join-Path $PSScriptRoot 'scout\server.py'

if (-not (Test-Path -LiteralPath $python)) {
    Write-Host 'Creating Python virtual environment...'
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv (Join-Path $PSScriptRoot '.venv')
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv (Join-Path $PSScriptRoot '.venv')
    } else {
        throw 'Install Python 3.10 or newer, then run this script again.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python virtual environment.' }
}

& $python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10 or newer is required.' }

Write-Host 'Checking Python dependencies...'
& $python -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check the error above and retry.' }

& $python $server --port $Port --auto-port --open-browser
exit $LASTEXITCODE
