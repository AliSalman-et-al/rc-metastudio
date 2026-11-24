$repo = Split-Path $PSScriptRoot -Parent
$fig = $PSScriptRoot
$env:RCMS_R_HOME = 'C:/Program Files/R/R-4.6.2'
$env:RCMS_R_LIBS = "$fig/.build/r-library"
$env:RCMS_QT6_BUILD_ROOT = "$fig/.build/qt6"
$env:RCMS_ANALYSIS_SCRATCH_DIR = "$fig/.build/analysis"
$env:TMP = $env:TEMP = "$fig/.build/temp"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = "$repo;$repo/.agents/skills/verify-rcms/scripts"
$env:QT_QPA_PLATFORM = 'windows'
Set-Location $repo
& "$repo/.venv/Scripts/python.exe" "$fig/capture_rcms.py" @args
exit $LASTEXITCODE
