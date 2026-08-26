param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $ArgsFromUser
)

$ErrorActionPreference = "Stop"

$uv = Get-Command uv -ErrorAction SilentlyContinue
$script = Join-Path $PSScriptRoot "app\src\dance_compare_ui.py"

if (-not $uv) {
    throw "No se encontro uv. Instalalo desde https://docs.astral.sh/uv/getting-started/installation/"
}

& $uv.Source run --locked python $script @ArgsFromUser
exit $LASTEXITCODE
