<#
.SYNOPSIS
  Start a backend locally (serves the frontend too).
  env: PORT (default 8000), HOST, TASKBOARD_DATA_FILE
.EXAMPLE
  .\scripts\run.ps1 -Backend node
#>
param(
    [ValidateSet('python', 'node')]
    [string]$Backend = 'python'
)
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
if (-not $env:PORT) { $env:PORT = '8000' }

switch ($Backend) {
    'python' { & (Join-Path $Root '.venv\Scripts\python.exe') (Join-Path $Root 'backend-python\run.py') }
    'node'   { & node (Join-Path $Root 'backend-node\src\server.js') }
}
