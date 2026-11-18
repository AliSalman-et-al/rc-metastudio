param(
    [ValidateSet("setup", "r", "plots", "native100", "native150")]
    [string]$Lane,
    [string]$Run = "qualification",
    [double]$SystemScale = 1.25,
    [string[]]$Only,
    [string]$Library = ".tmp/tsa-phase4-library"
)

$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$proof = (New-Item -ItemType Directory -Force "$PSScriptRoot/$Run/$Lane").FullName
$env:RCMS_QT6_RCC = (Resolve-Path build/qt-rcc-verified/bin/rcc.exe).Path
$env:RCMS_R_HOME = "$env:USERPROFILE/Downloads/RCMetaStudio-0.5.6-windows-x64/R"
$env:RCMS_QT6_BUILD_ROOT = "$PWD/build/qt6-verification"
$env:RCMS_R_LIBS = (New-Item -ItemType Directory -Force $Library).FullName
$env:R_LIBS = $env:R_LIBS_USER = $env:RCMS_R_LIBS
$env:PATH = (Resolve-Path .tmp/poppler-tsa/poppler-26.09.0/Library/bin).Path + ";" + $env:PATH
$rscript = "$env:RCMS_R_HOME/bin/Rscript.exe"

function Invoke-Logged([string]$Name, [string]$Program, [string[]]$Arguments) {
    $log = "$proof/$Name.log"
    $argText = ($Arguments | ForEach-Object { "'" + ($_ -replace "'", "''") + "'" }) -join " "
    "Command: $Program $argText" | Set-Content $log
    & $Program @Arguments *>> $log
    $code = $LASTEXITCODE
    "Exit: $code" | Add-Content $log
    Write-Host "$Lane $Name => $code"
    $match = Select-String -Path $log -Pattern '^Evidence: (.+)$' | Select-Object -Last 1
    if ($match) {
        $source = $match.Matches[0].Groups[1].Value
        Move-Item -LiteralPath $source -Destination "$proof/$Name"
    }
    if ($code) { throw "See $log" }
}

if ($Lane -eq "setup") {
    Invoke-Logged sync uv @("sync", "--locked")
    Invoke-Logged forms uv @("run", "python", "scripts/build_qt6.py", "generate", "--build-root", "build/qt6-verification")
}
Invoke-Logged typing uv @("run", "python", "-c", "from pathlib import Path; from scripts.verify import run_typing; run_typing(Path('build/qt6-verification').resolve())")
switch ($Lane) {
    "setup" {
        if (!(Test-Path "$env:RCMS_R_LIBS/metafor")) {
            Copy-Item .tmp/tsa-phase3b-libraries/branch/* -Destination $env:RCMS_R_LIBS -Recurse
        }
        git rev-parse HEAD | Set-Content "$proof/source.txt"
        git diff HEAD -- r/RCMetaR | Add-Content "$proof/source.txt"
        Invoke-Logged install $rscript @("--vanilla", "$PSScriptRoot/install.R")
    }
    "r" {
        Invoke-Logged r-tests $rscript @("--vanilla", "$PSScriptRoot/test-plots.R")
    }
    "plots" {
        $env:RCMS_TSA_DESIGN_EXPORTS = "1"
        $cases = @("plot-workflow-regression", "plot-workflow-trimfill", "plot-workflow-sroc", "plot-workflow-forest")
        foreach ($case in $cases) {
            if ($Only -and $case -notin $Only) { continue }
            Invoke-Logged $case uv @("run", "python", "scripts/verify_rcms.py", $case)
        }
        $env:QT_QPA_PLATFORM = "offscreen"
        Invoke-Logged python-plots uv @("run", "python", "-m", "pytest", "-q", "tests/python/gui/test_funnel_plot_editor.py", "tests/python/fast/test_plot_service.py", "tests/python/fast/test_plot_capabilities.py")
    }
    { $_ -in "native100", "native150" } {
        $target = if ($Lane -eq "native100") { 1.0 } else { 1.5 }
        $env:QT_SCALE_FACTOR = [string]($target / $SystemScale)
        $env:RCMS_TSA_DESIGN_EXPORTS = if ($Lane -eq "native100") { "1" } else { "0" }
        @("QT_SCALE_FACTOR=$env:QT_SCALE_FACTOR", "Expected device scale=$target", "RCMS_R_LIBS=$env:RCMS_R_LIBS") |
            Set-Content "$proof/environment.log"
        $cases = @("plot-workflow-trial-sequential", "tsa-hr", "tsa-md", "tsa-rr-mh", "tsa-stress")
        if ($Lane -eq "native100") { $cases += "tsa-smd" }
        foreach ($case in $cases) {
            if ($Only -and $case -notin $Only) { continue }
            Invoke-Logged $case uv @("run", "python", "scripts/verify_rcms.py", $case, "--native")
        }
    }
}
