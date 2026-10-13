# Run from the repository root. This library belongs to this verification round.
$env:RCMS_R_HOME = (Resolve-Path 'build/windows-package/dist/RCMetaStudio/R').Path
$round2Library = Join-Path (Get-Location) 'build/verification/round2-r-library'
$env:RCMS_R_LIBS = $round2Library
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path 'build/qt6-verification').Path
$env:R_HOME = $env:RCMS_R_HOME
$env:R_LIBS = $round2Library
$env:R_LIBS_USER = $round2Library
$env:PATH = "$env:RCMS_R_HOME/bin/x64;$env:RCMS_R_HOME/bin;$env:PATH"
$env:RCMS_R_STACK_REQUIRED = '1'
