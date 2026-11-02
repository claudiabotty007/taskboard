<#
.SYNOPSIS
  Run the test suites on Windows (run .\scripts\build.ps1 first).
.DESCRIPTION
  python -> full pytest suite against the Python backend
  node   -> npm test + the pytest contract tests against the Node backend
  JUnit XML goes to reports\ for Jenkins. Extra arguments are passed to pytest.
.EXAMPLE
  .\scripts\test.ps1 -Backend python -k health
#>
param(
    [ValidateSet('python', 'node', 'all')]
    [string]$Backend = 'all',
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root '.venv\Scripts\python.exe'
$Extra = if ($PytestArgs) { $PytestArgs } else { @() }

function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "'$Exe $Arguments' failed with exit code $LASTEXITCODE" }
}

function Test-Python {
    Invoke-Checked $Py (@('-m', 'pytest', '--backend', 'python', '--junitxml=reports/pytest-python.xml') + $Extra)
}

function Test-Node {
    Invoke-Checked 'npm' @('test', '--prefix', 'backend-node')
    Invoke-Checked $Py (@('-m', 'pytest', '-m', 'contract', '--backend', 'node', '--junitxml=reports/pytest-node.xml') + $Extra)
}

if (-not (Test-Path $Py)) { throw 'No .venv found - run scripts\build.ps1 first' }
New-Item -ItemType Directory -Force (Join-Path $Root 'reports') | Out-Null

Push-Location $Root
try {
    switch ($Backend) {
        'python' { Test-Python }
        'node'   { Test-Node }
        'all'    { Test-Python; Test-Node }
    }
} finally {
    Pop-Location
}
