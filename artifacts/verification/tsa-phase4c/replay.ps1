param(
    [ValidateSet("setup", "r", "native100", "native150")]
    [string]$Lane,
    [double]$SystemScale = 1.25,
    [string[]]$Only,
    [string]$Run = "qualification"
)

$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$proof = (New-Item -ItemType Directory -Force "$PSScriptRoot/$Run/$Lane").FullName
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path build/qt6-verification).Path
$env:RCMS_R_HOME = "$env:USERPROFILE/Downloads/RCMetaStudio-0.5.6-windows-x64/R"
$env:RCMS_R_LIBS = (New-Item -ItemType Directory -Force .tmp/tsa-phase4c-library).FullName
$env:R_LIBS = $env:R_LIBS_USER = $env:RCMS_R_LIBS
$env:PATH = (Resolve-Path .tmp/poppler-tsa/poppler-26.09.0/Library/bin).Path + ";" + $env:PATH
$rscript = "$env:RCMS_R_HOME/bin/Rscript.exe"
$prior = "$PSScriptRoot/../tsa-phase4"

function Invoke-Logged([string]$Name, [string]$Program, [string[]]$Arguments) {
    $log = "$proof/$Name.log"
    "Command: $Program $($Arguments | ConvertTo-Json -Compress)" | Set-Content $log
    & $Program @Arguments *>> $log
    $code = $LASTEXITCODE
    "Exit: $code" | Add-Content $log
    Write-Host "$Lane $Name => $code"
    $match = Select-String -Path $log -Pattern '^Evidence: (.+)$' | Select-Object -Last 1
    if ($match) {
        Move-Item -LiteralPath $match.Matches[0].Groups[1].Value -Destination "$proof/$Name"
    }
    if ($code) { throw "See $log" }
}

switch ($Lane) {
    "setup" {
        Invoke-Logged typing uv @("run", "python", "-c", "from pathlib import Path; from scripts.verify import run_typing; run_typing(Path('build/qt6-verification').resolve())")
        if (!(Test-Path "$env:RCMS_R_LIBS/metafor")) {
            Copy-Item .tmp/tsa-phase3b-libraries/branch/* -Destination $env:RCMS_R_LIBS -Recurse
        }
        git rev-parse HEAD | Set-Content "$proof/source.txt"
        git diff HEAD -- r/RCMetaR | Add-Content "$proof/source.txt"
        Invoke-Logged install $rscript @("--vanilla", "$prior/install.R")
        Invoke-Logged doctor uv @("run", "python", "scripts/verify_rcms.py", "doctor", "--native")
    }
    "r" {
        Invoke-Logged r-tests $rscript @("--vanilla", "$prior/test-plots.R")
    }
    { $_ -in "native100", "native150" } {
        $target = if ($Lane -eq "native100") { 1.0 } else { 1.5 }
        $env:QT_SCALE_FACTOR = ($target / $SystemScale).ToString([cultureinfo]::InvariantCulture)
        $env:RCMS_TSA_DESIGN_EXPORTS = "0"
        @("QT_SCALE_FACTOR=$env:QT_SCALE_FACTOR", "Expected device scale=$target",
          "RCMS_TSA_DESIGN_EXPORTS=$env:RCMS_TSA_DESIGN_EXPORTS", "RCMS_R_LIBS=$env:RCMS_R_LIBS") |
            Set-Content "$proof/environment.log"
        foreach ($case in @("plot-workflow-trial-sequential", "tsa-hr", "tsa-md", "tsa-rr-mh", "tsa-stress")) {
            if ($Only -and $case -notin $Only) { continue }
            Invoke-Logged $case uv @("run", "python", "scripts/verify_rcms.py", $case, "--native")
        }
    }
}
