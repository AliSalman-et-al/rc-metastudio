$env:RCMS_R_HOME = (Resolve-Path 'build/windows-package/dist/RCMetaStudio/R').Path
$env:RCMS_R_LIBS = (Resolve-Path 'docs/ux-audit/2026-10-13-native/runtime-library').Path
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path 'build/qt6-verification').Path
if ($args.Count) {
    & uv run python @args
    exit $LASTEXITCODE
}
