param(
    [switch]$Sync,
    [string]$BuildRoot = "build/qt6-verification",
    [ValidateSet("Full", "Core", "RemainingSurfaces")]
    [string]$Section = "Full"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$remainingSurfaceTests = @(
    "tests/python/gui/test_adaptive_window_policy.py",
    "tests/python/gui/test_compact_transient_layout.py",
    "tests/python/gui/test_parented_wizard_sizing.py",
    "tests/python/gui/test_main_window_data_workflows.py",
    "tests/python/gui/test_main_wizard_workflow_layout.py"
)

function Invoke-NativeSmokeCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string[]]$Command,
        [int]$TimeoutSeconds = 300
    )
    $runnerArguments = @(
        "run", "python", "scripts/run_with_timeout.py",
        "--timeout-seconds", $TimeoutSeconds,
        "--label", $Label,
        "--"
    ) + $Command
    & uv @runnerArguments
    if ($LASTEXITCODE -ne 0) { throw "$Label failed with exit code $LASTEXITCODE." }
}

function Invoke-NativeRemainingSurfaceSmoke {
    Invoke-NativeSmokeCommand -Label "Native Qt6 remaining-surface smoke" -Command @(
        "uv", "run", "python", "scripts/native_remaining_surfaces_smoke.py"
    )
    Invoke-NativeSmokeCommand -Label "Native Qt6 remaining-surface evidence validation" -Command @(
        "uv", "run", "python", "scripts/native_remaining_surfaces_smoke.py", "--validate-only"
    )
}

$previousTypingReceipt = $env:RCMS_TYPING_RECEIPT
Push-Location $repoRoot
try {
    if ($Sync) {
        uv sync --locked
        if ($LASTEXITCODE -ne 0) { throw "uv sync --locked failed." }
    }

    uv run python scripts/build_qt6.py generate --build-root $BuildRoot
    if ($LASTEXITCODE -ne 0) { throw "Qt6 form or resource generation failed." }
    $env:RCMS_QT6_BUILD_ROOT = (Resolve-Path $BuildRoot).Path

    $guiRoot = Join-Path $repoRoot "tests/python/gui"
    $allGuiTests = @(Get-ChildItem -LiteralPath $guiRoot -File -Filter "test_*.py" |
        ForEach-Object { $_.FullName.Substring($repoRoot.Length + 1).Replace("\", "/") })
    $missingRemaining = @($remainingSurfaceTests | Where-Object { $_ -notin $allGuiTests })
    if ($missingRemaining.Count -ne 0) {
        throw "RemainingSurfaces GUI tests are missing: $($missingRemaining -join ', ')"
    }
    $coreGuiTests = @($allGuiTests | Where-Object { $_ -notin $remainingSurfaceTests })
    $overlap = @($coreGuiTests | Where-Object { $_ -in $remainingSurfaceTests })
    if ($overlap.Count -ne 0 -or ($coreGuiTests.Count + $remainingSurfaceTests.Count) -ne $allGuiTests.Count) {
        throw "Core and RemainingSurfaces GUI selections overlap or omit a GUI test."
    }

    # Ty resolves generated modules from their flat build search paths while
    # runtime imports remain package-qualified through rc_metastudio.forms.
    $typingOutput = @(uv run python -c "from scripts.verification_evidence import run_typing; from pathlib import Path; import sys; print(run_typing(Path(sys.argv[1])))" $env:RCMS_QT6_BUILD_ROOT)
    $typingExitCode = $LASTEXITCODE
    $typingOutput | Write-Output
    if ($typingExitCode -ne 0) { throw "Repository-wide strict type verification failed." }
    $env:RCMS_TYPING_RECEIPT = $typingOutput[-1]


    if ($Section -eq "RemainingSurfaces") {
        uv run pytest -W error @remainingSurfaceTests
        if ($LASTEXITCODE -ne 0) { throw "Qt6 remaining-surface tests failed." }

        $previousQpa = $env:QT_QPA_PLATFORM
        $previousFatalWarnings = $env:QT_FATAL_WARNINGS
        Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
        $env:QT_FATAL_WARNINGS = "1"
        try { Invoke-NativeRemainingSurfaceSmoke }
        finally {
            if ($null -ne $previousQpa) { $env:QT_QPA_PLATFORM = $previousQpa }
            else { Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue }
            if ($null -ne $previousFatalWarnings) { $env:QT_FATAL_WARNINGS = $previousFatalWarnings }
            else { Remove-Item Env:QT_FATAL_WARNINGS -ErrorAction SilentlyContinue }
        }
        return
    }

    uv run pytest -W error @coreGuiTests
    if ($LASTEXITCODE -ne 0) { throw "Qt6 core GUI tests failed." }
    if ($Section -eq "Full") {
        uv run pytest -W error @remainingSurfaceTests
        if ($LASTEXITCODE -ne 0) { throw "Qt6 remaining-surface tests failed." }
    }

    $previousQpa = $env:QT_QPA_PLATFORM
    $previousFatalWarnings = $env:QT_FATAL_WARNINGS
    Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    $env:QT_FATAL_WARNINGS = "1"
    try {
        Invoke-NativeSmokeCommand -Label "Native qwindows Qt6 smoke" -Command @(
            "uv", "run", "python", "scripts/build_qt6.py", "native-smoke",
            "--build-root", $BuildRoot, "--exit-after-ms", "100"
        )
        Invoke-NativeSmokeCommand -Label "Native RC MetaStudio Qt6 shell smoke" -Command @(
            "uv", "run", "python", "scripts/native_shell_smoke.py", "--native"
        )
        Invoke-NativeSmokeCommand -Label "Native Qt6 calculator smoke" -Command @(
            "uv", "run", "python", "scripts/native_calculator_smoke.py"
        )
        Invoke-NativeSmokeCommand -Label "Native Qt6 calculator evidence validation" -Command @(
            "uv", "run", "python", "scripts/native_calculator_smoke.py", "--validate-only"
        )
        Invoke-NativeSmokeCommand -Label "Native Qt6 analysis workflow smoke" -Command @(
            "uv", "run", "python", "scripts/native_analysis_smoke.py"
        )
        Invoke-NativeSmokeCommand -Label "Native Qt6 Results fractional-scale smoke" -Command @(
            "uv", "run", "python", "scripts/native_results_smoke.py"
        )
        Invoke-NativeSmokeCommand -Label "Native Qt6 Results evidence validation" -Command @(
            "uv", "run", "python", "scripts/native_results_smoke.py", "--validate-only"
        )
        if ($Section -eq "Full") { Invoke-NativeRemainingSurfaceSmoke }
        Invoke-NativeSmokeCommand -Label "Native R-load teardown smoke" -Command @(
            "uv", "run", "python", "scripts/native_shell_smoke.py", "--failure-stage", "r-load"
        )
        Invoke-NativeSmokeCommand -Label "Native MainWindow teardown smoke" -Command @(
            "uv", "run", "python", "scripts/native_shell_smoke.py", "--failure-stage", "meta-form"
        )
    }
    finally {
        if ($null -ne $previousQpa) { $env:QT_QPA_PLATFORM = $previousQpa }
        else { Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue }
        if ($null -ne $previousFatalWarnings) { $env:QT_FATAL_WARNINGS = $previousFatalWarnings }
        else { Remove-Item Env:QT_FATAL_WARNINGS -ErrorAction SilentlyContinue }
    }
}
finally {
    if ($null -ne $previousTypingReceipt) { $env:RCMS_TYPING_RECEIPT = $previousTypingReceipt }
    else { Remove-Item Env:RCMS_TYPING_RECEIPT -ErrorAction SilentlyContinue }
    Pop-Location
}
