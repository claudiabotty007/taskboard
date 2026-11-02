<#
.SYNOPSIS
  Build one or both Taskboard backends on Windows.
.DESCRIPTION
  Always prepares .venv (pytest drives the tests of both backends), then packages
  dist\taskboard-<backend>-windows.zip containing the backend plus the frontend.
.EXAMPLE
  .\scripts\build.ps1 -Backend python
#>
param(
    [ValidateSet('python', 'node', 'all')]
    [string]$Backend = 'all'
)
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Dist = Join-Path $Root 'dist'
$Venv = Join-Path $Root '.venv'
$VenvPython = Join-Path $Venv 'Scripts\python.exe'
$Python = if ($env:PYTHON) { $env:PYTHON } else { 'python' }

function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "'$Exe $Arguments' failed with exit code $LASTEXITCODE" }
}

function Initialize-Venv {
    if (-not (Test-Path $VenvPython)) { Invoke-Checked $Python @('-m', 'venv', $Venv) }
    Invoke-Checked $VenvPython @('-m', 'pip', 'install', '--quiet', '--disable-pip-version-check',
        '-r', (Join-Path $Root 'requirements-dev.txt'))
}

function New-Package([string]$Name, [string]$Source) {
    $out = Join-Path $Dist "taskboard-$Name-windows"
    foreach ($old in @($out, "$out.zip")) {
        if (Test-Path $old) { Remove-Item -Recurse -Force $old }
    }
    New-Item -ItemType Directory -Force $out | Out-Null
    Copy-Item -Recurse $Source (Join-Path $out 'backend')
    Copy-Item -Recurse (Join-Path $Root 'frontend') (Join-Path $out 'frontend')
    Get-ChildItem $out -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force
    Compress-Archive -Path $out -DestinationPath "$out.zip"
    Write-Host "Built $out.zip"
}

function Build-Python {
    Write-Host '==> Building Python backend'
    Invoke-Checked $VenvPython @('-m', 'compileall', '-q', (Join-Path $Root 'backend-python'))
    New-Package 'python' (Join-Path $Root 'backend-python')
}

function Build-Node {
    Write-Host '==> Building Node backend'
    Invoke-Checked 'npm' @('ci', '--prefix', (Join-Path $Root 'backend-node'), '--no-audit', '--no-fund')
    New-Package 'node' (Join-Path $Root 'backend-node')
}

Initialize-Venv
switch ($Backend) {
    'python' { Build-Python }
    'node'   { Build-Node }
    'all'    { Build-Python; Build-Node }
}
