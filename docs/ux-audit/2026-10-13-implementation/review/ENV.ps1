$env:RCMS_R_HOME = (Resolve-Path 'build/windows-package/dist/RCMetaStudio/R').Path
$reviewLibrary = Join-Path (Get-Location) 'build/verification/review-r-library'
New-Item -ItemType Directory -Force -Path $reviewLibrary | Out-Null
$env:RCMS_R_LIBS = $reviewLibrary
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path 'build/qt6-verification').Path
$env:R_HOME = $env:RCMS_R_HOME
$env:R_LIBS = $env:RCMS_R_LIBS
$env:R_LIBS_USER = $env:RCMS_R_LIBS
$env:PATH = "$env:RCMS_R_HOME/bin;$env:PATH"
$env:RCMS_R_STACK_REQUIRED = '1'
$reviewEvidence = 'docs/ux-audit/2026-10-13-implementation/review'
