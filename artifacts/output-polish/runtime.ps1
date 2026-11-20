$env:RCMS_R_HOME = 'C:/Program Files/R/R-4.6.2'
$env:RCMS_R_LIBS = (Resolve-Path build/output-polish/r-library).Path
$env:R_LIBS = $env:RCMS_R_LIBS
$env:R_LIBS_USER = $env:RCMS_R_LIBS
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path build/qt6-verification).Path
Remove-Item Env:LC_ALL,Env:LC_CTYPE,Env:LANG,Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
