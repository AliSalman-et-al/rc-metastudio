param(
    [Parameter(Mandatory)]
    [ValidateSet('typing', 'setup', 'r', 'python', 'native100', 'native150', 'print', 'review')]
    [string]$Lane,
    [double]$SystemScale = 1.25,
    [string[]]$Only,
    [string]$Run = 'final'
)

$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$proof = (New-Item -ItemType Directory -Force "$PSScriptRoot/$Run/$Lane").FullName
$env:RCMS_QT6_BUILD_ROOT = Join-Path (Get-Location) 'build/qt6-verification'
$env:RCMS_R_HOME = "$env:USERPROFILE/Downloads/RCMetaStudio-0.5.6-windows-x64/R"
$env:RCMS_R_LIBS = (New-Item -ItemType Directory -Force .tmp/tsa-phase6-library).FullName
$env:R_LIBS = $env:R_LIBS_USER = $env:RCMS_R_LIBS
$env:PATH = (Resolve-Path .tmp/poppler-tsa/poppler-26.09.0/Library/bin).Path + ';' + $env:PATH
$rscript = "$env:RCMS_R_HOME/bin/Rscript.exe"

function Invoke-Logged([string]$Name, [string]$Program, [string[]]$Arguments) {
    $log = "$proof/$Name.log"
    "Command: $Program $($Arguments | ConvertTo-Json -Compress)" | Set-Content $log
    "Git revision: $(git rev-parse HEAD)" | Add-Content $log
    & $Program @Arguments *>> $log
    $code = $LASTEXITCODE
    "Exit: $code" | Add-Content $log
    Write-Host "$Lane $Name => $code"
    $match = Select-String -Path $log -Pattern '^(?:Typing evidence|Evidence): (.+)$' | Select-Object -Last 1
    if ($match) {
        Move-Item -LiteralPath $match.Matches[0].Groups[1].Value -Destination "$proof/$Name"
    }
    if ($code) { throw "See $log" }
}

switch ($Lane) {
    'typing' {
        Invoke-Logged generate uv @('run', 'python', 'scripts/build_qt6.py', 'generate', '--build-root', 'build/qt6-verification')
        Invoke-Logged typing uv @('run', 'python', '-c', "from pathlib import Path; from scripts.verify import run_typing; run_typing(Path('build/qt6-verification').resolve())")
    }
    'setup' {
        if (!(Test-Path "$env:RCMS_R_LIBS/metafor")) {
            Copy-Item .tmp/tsa-phase5-library/* -Exclude RCMetaR -Destination $env:RCMS_R_LIBS -Recurse
        }
        git rev-parse HEAD HEAD:r/RCMetaR | Set-Content "$proof/source.txt"
        git diff HEAD -- r/RCMetaR | Add-Content "$proof/source.txt"
        Invoke-Logged install $rscript @('--vanilla', 'artifacts/verification/tsa-phase4/install.R')
        Invoke-Logged doctor uv @('run', 'python', 'scripts/verify_rcms.py', 'doctor', '--native')
    }
    'r' {
        Invoke-Logged r-tests $rscript @('--vanilla', 'artifacts/verification/tsa-phase4/test-plots.R')
    }
    'python' {
        $env:QT_QPA_PLATFORM = 'offscreen'
        $env:PYTHONUNBUFFERED = '1'
        Invoke-Logged python-tests uv @('run', 'python', '-m', 'pytest', '-q', 'tests/python', '--basetemp', ".tmp/tsa-phase6-python-$Run", '--tb=short')
    }
    { $_ -in 'native100', 'native150' } {
        $target = if ($Lane -eq 'native100') { 1.0 } else { 1.5 }
        $env:QT_SCALE_FACTOR = ($target / $SystemScale).ToString([cultureinfo]::InvariantCulture)
        $env:RCMS_TSA_DESIGN_EXPORTS = '1'
        @("QT_SCALE_FACTOR=$env:QT_SCALE_FACTOR", "Expected device scale=$target",
          "RCMS_TSA_DESIGN_EXPORTS=$env:RCMS_TSA_DESIGN_EXPORTS", "RCMS_R_LIBS=$env:RCMS_R_LIBS") |
            Set-Content "$proof/environment.log"
        foreach ($case in @('plot-workflow-trial-sequential', 'tsa-hr', 'tsa-md', 'tsa-rr-mh', 'tsa-stress', 'tsa-peto', 'tsa-smd')) {
            if ($Only -and $case -notin $Only) { continue }
            Invoke-Logged $case uv @('run', 'python', 'scripts/verify_rcms.py', $case, '--native')
        }
    }
    'print' {
        Invoke-Logged print $rscript @('--vanilla', 'artifacts/verification/tsa-phase5b/print.R', (Split-Path $proof))
    }
    'review' {
        Invoke-Logged review uv @('run', 'python', "$PSScriptRoot/audit.py", (Split-Path $proof))
    }
}
