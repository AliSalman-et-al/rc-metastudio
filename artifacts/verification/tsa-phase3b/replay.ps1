param(
    [Parameter(Mandatory)][string]$Checkout,
    [Parameter(Mandatory)][string]$Label,
    [switch]$Full,
    [switch]$FirstFailure,
    [switch]$Tsa,
    [string]$Case,
    [switch]$ReviewOnly,
    [switch]$PythonOnly,
    [switch]$BinaryPrefix,
    [switch]$FastBeforeBinary,
    [switch]$Offscreen,
    [string]$Scale,
    [string]$LibraryLabel = $Label,
    [switch]$ReuseR
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$repo = (Resolve-Path "$PSScriptRoot/../../..").Path
$proof = (New-Item -ItemType Directory -Force "$PSScriptRoot/$Label").FullName
$env:RCMS_R_HOME = "$env:USERPROFILE/Downloads/RCMetaStudio-0.5.6-windows-x64/R"
$env:RCMS_QT6_RCC = (Resolve-Path "$repo/build/qt-rcc-verified/bin/rcc.exe").Path
$env:PATH = (Resolve-Path "$repo/.tmp/poppler-tsa/poppler-26.09.0/Library/bin").Path + ';' + $env:PATH
$env:QT_QPA_PLATFORM = if ($Offscreen) { 'offscreen' } else { 'windows' }
$env:PYTHONFAULTHANDLER = '1'
if ($Scale) { $env:QT_SCALE_FACTOR = $Scale }
else { Remove-Item Env:QT_SCALE_FACTOR -ErrorAction SilentlyContinue }
$env:RCMS_R_LIBS = (New-Item -ItemType Directory -Force "$repo/.tmp/tsa-phase3b-libraries/$LibraryLabel").FullName
$env:R_LIBS = $env:R_LIBS_USER = $env:RCMS_R_LIBS
$rscript = "$env:RCMS_R_HOME/bin/Rscript.exe"

function Invoke-Proof([string]$Name, [string]$Program, [string[]]$Arguments) {
    $log = "$proof/$Name.log"
    $command = "$Program " + (($Arguments | ForEach-Object { "'" + ($_ -replace "'", "''") + "'" }) -join ' ')
    "Command: $command" | Set-Content $log
    & $Program @Arguments *>> $log
    $code = $LASTEXITCODE
    "Exit: $code" | Add-Content $log
    Write-Host "$Label $Name $code"
    return $code
}

function Invoke-Desktop([string]$Case) {
    $arguments = @('run', 'python', 'scripts/verify_rcms.py', $Case)
    if (-not $Offscreen) { $arguments += '--native' }
    $null = Invoke-Proof $Case uv $arguments
    $record = Select-String -LiteralPath "$proof/$Case.log" -Pattern '^Evidence: (.+)$' | Select-Object -First 1
    if ($record) {
        $evidence = $record.Matches[0].Groups[1].Value.Trim()
        Copy-Item -LiteralPath $evidence -Destination "$proof/$Case" -Recurse
    }
}

Push-Location (Resolve-Path $Checkout)
try {
    @(
        "Checkout: $PWD"
        "Revision: $(git rev-parse HEAD)"
        "R source tree: $(git rev-parse HEAD:r/RCMetaR)"
        "Platform: $env:OS $env:PROCESSOR_ARCHITECTURE, QT_QPA_PLATFORM=$env:QT_QPA_PLATFORM, QT_SCALE_FACTOR=$env:QT_SCALE_FACTOR"
        "RCMS_R_HOME=$env:RCMS_R_HOME"
        "RCMS_R_LIBS=$env:RCMS_R_LIBS"
        "RCMS_QT6_RCC=$env:RCMS_QT6_RCC"
        "PATH prefix: $($env:PATH.Split(';')[0])"
    ) | Set-Content "$proof/environment.log"
    if ((Invoke-Proof sync uv @('sync', '--locked')) -ne 0) { throw 'uv sync failed' }
    if ((Invoke-Proof forms uv @('run', 'python', 'scripts/build_qt6.py', 'generate', '--build-root', 'build/qt6-verification')) -ne 0) { throw 'Qt form generation failed' }
    $env:RCMS_QT6_BUILD_ROOT = (Resolve-Path build/qt6-verification).Path
    "RCMS_QT6_BUILD_ROOT=$env:RCMS_QT6_BUILD_ROOT" | Add-Content "$proof/environment.log"
    if ((Invoke-Proof typing uv @('run', 'python', '-c', "from pathlib import Path; from scripts.verify import run_typing; run_typing(Path('build/qt6-verification').resolve())")) -ne 0) { throw 'Strict typing failed' }
    if (-not $ReuseR) {
        Get-ChildItem -LiteralPath "$repo/.tmp/tsa-r" -Directory |
            Where-Object Name -ne 'RCMetaR' |
            Copy-Item -Destination $env:RCMS_R_LIBS -Recurse
        if ((Invoke-Proof install-r $rscript @('--vanilla', '-e', 'install.packages("r/RCMetaR", repos=NULL, type="source", lib=Sys.getenv("RCMS_R_LIBS"))')) -ne 0) { throw 'RCMetaR install failed' }
    }
    if ($Case) {
        Invoke-Desktop $Case
        return
    }
    New-Item -ItemType Directory -Force .tmp | Out-Null
    if (-not $ReviewOnly) {
        $null = Invoke-Proof results uv @('run', 'python', '-m', 'pytest', 'tests/python/gui/test_main_window_automation_launch.py', '-k', 'test_results_window_refits_svg_plots_and_reflows_sections_on_resize or test_results_window_refits_svg_after_viewport_geometry_settles or test_results_window_refits_raster_fallback_from_original_source', '-q', '--basetemp', '.tmp/tsa-phase3b-results')
        if ($BinaryPrefix) {
            $prefix = @(
                'test_adaptive_layout_native_evidence.py', 'test_adaptive_window_policy.py',
                'test_analysis_configuration_layout.py', 'test_analysis_failure_safety.py',
                'test_binary_data_transactional_layout.py'
            ) | ForEach-Object { "tests/python/gui/$_" }
            if ($FastBeforeBinary) {
                $prefix = @('tests/python/fast', '--ignore=tests/python/fast/test_code_health.py') + $prefix
            }
            $null = Invoke-Proof binary-prefix uv (@('run', 'python', '-m', 'pytest') + $prefix + @('-q', '--basetemp', '.tmp/tsa-phase3b-binary-prefix'))
            return
        }
        $null = Invoke-Proof binary-layout uv @('run', 'python', '-m', 'pytest', 'tests/python/gui/test_binary_data_transactional_layout.py', '-q', '--basetemp', '.tmp/tsa-phase3b-layout')
    }
    if (-not $PythonOnly) { Invoke-Desktop review-workflows }
    if ($FirstFailure) {
        $null = Invoke-Proof python-first-failure uv @('run', 'python', '-m', 'pytest', 'tests/python', '--ignore=tests/python/fast/test_code_health.py', '-x', '-q', '--basetemp', '.tmp/tsa-phase3b-first-failure')
    }
    if ($Full) {
        $null = Invoke-Proof python uv @('run', 'python', '-m', 'pytest', 'tests/python', '-q', '--basetemp', '.tmp/tsa-phase3b-python')
    }
    if ($Tsa) {
        $null = Invoke-Proof tsa-r $rscript @('--vanilla', '-e', 'pkgload::load_all("r/RCMetaR"); testthat::test_file("r/RCMetaR/tests/testthat/test-trial-sequential-analysis.R", reporter="summary", stop_on_failure=TRUE)')
        foreach ($case in @('tsa-smd', 'tsa-hr', 'tsa-rr-mh', 'tsa-md', 'plot-workflow-trial-sequential')) {
            Invoke-Desktop $case
        }
    }
} finally {
    Pop-Location
}
