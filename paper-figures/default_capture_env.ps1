$env:RCMS_R_HOME = 'C:/Program Files/R/R-4.6.2'
$env:RCMS_R_LIBS = (Resolve-Path build/dev-r-lib).Path
$env:R_LIBS_USER = $env:RCMS_R_LIBS
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path build/joss-qt6).Path
$env:RCMS_PAPER_OUTPUT = (Resolve-Path $env:RCMS_PAPER_OUTPUT).Path
$env:RCMS_ANALYSIS_SCRATCH_DIR = (New-Item -ItemType Directory -Force "$env:RCMS_PAPER_OUTPUT/capture-state/analysis").FullName
$env:TMP = $env:TEMP = (New-Item -ItemType Directory -Force "$env:RCMS_PAPER_OUTPUT/capture-state/temp").FullName
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = "$PWD;$PWD/.agents/skills/verify-rcms/scripts"
$env:QT_QPA_PLATFORM = 'windows'

