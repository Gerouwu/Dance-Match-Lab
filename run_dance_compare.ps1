param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $ArgsFromUser
)

$ErrorActionPreference = "Stop"

$python = "C:\Users\viejo\anaconda3\envs\biof_docker\python.exe"
$script = Join-Path $PSScriptRoot "app\src\dance_compare_ui.py"

if (-not (Test-Path $python)) {
    throw "No encontre el Python del entorno biof_docker en: $python"
}

& $python $script @ArgsFromUser
