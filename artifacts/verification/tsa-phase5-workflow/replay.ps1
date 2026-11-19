param(
    [ValidateSet("typing", "r", "python", "native100", "native150", "full")]
    [string]$Lane,
    [string[]]$Only,
    [double]$SystemScale = 1.25,
    [string]$Run = "qualification"
)

$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$proof = (New-Item -ItemType Directory -Force "$PSScriptRoot/$Run/$Lane").FullName
$env:RCMS_QT6_BUILD_ROOT = (Resolve-Path build/qt6-verification).Path
$env:R_LIBS = $env:R_LIBS_USER = $env:RCMS_R_LIBS
$rscript = Join-Path $env:RCMS_R_HOME 'bin/Rscript.exe'

function Invoke-Logged([string]$Name, [string]$Program, [string[]]$Arguments) {
    $log = "$proof/$Name.log"
    "Command: $Program $($Arguments | ConvertTo-Json -Compress)" | Set-Content $log
    "Git revision: $(git rev-parse HEAD)" | Add-Content $log
    & $Program @Arguments *>> $log
    $code = $LASTEXITCODE
    "Exit: $code" | Add-Content $log
    Write-Host "$Lane $Name => $code"
    $match = Select-String -Path $log -Pattern '^(?:Evidence|Complete-run evidence): (.+)$' | Select-Object -Last 1
    if ($match) {
        Copy-Item -LiteralPath $match.Matches[0].Groups[1].Value -Destination "$proof/$Name" -Recurse
    }
    if ($code) { throw "See $log" }
}

switch ($Lane) {
    "typing" {
        Invoke-Logged typing uv @("run", "python", "-c", "from pathlib import Path; from scripts.verify import run_typing; run_typing(Path('build/qt6-verification').resolve())")
    }
    "r" {
        Invoke-Logged r-tests $rscript @("--vanilla", "artifacts/verification/tsa-phase4/test-plots.R")
        Invoke-Logged install $rscript @("--vanilla", "artifacts/verification/tsa-phase4/install.R")
    }
    "python" {
        $env:QT_QPA_PLATFORM = "offscreen"
        $env:PYTHONUNBUFFERED = "1"
        Invoke-Logged python-tests uv @("run", "python", "-m", "pytest", "-q", "tests/python", "--basetemp", ".tmp/tsa-phase5-python")
    }
    "full" {
        Invoke-Logged full uv @("run", "python", ".agents/skills/verify-rcms/scripts/verify_all.py", "--full")
    }
    { $_ -in "native100", "native150" } {
        $target = if ($Lane -eq "native100") { 1.0 } else { 1.5 }
        $env:QT_SCALE_FACTOR = ($target / $SystemScale).ToString([cultureinfo]::InvariantCulture)
        $env:RCMS_TSA_DESIGN_EXPORTS = "0"
        @("QT_SCALE_FACTOR=$env:QT_SCALE_FACTOR", "Expected device scale=$target") |
            Set-Content "$proof/environment.log"
        foreach ($case in @("doctor", "plot-workflow-trial-sequential", "tsa-hr", "tsa-md", "tsa-rr-mh", "tsa-smd", "tsa-stress")) {
            if ($Only -and $case -notin $Only) { continue }
            Invoke-Logged $case uv @("run", "python", "scripts/verify_rcms.py", $case, "--native")
        }
    }
}
