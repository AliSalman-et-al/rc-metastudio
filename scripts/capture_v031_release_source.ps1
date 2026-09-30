param(
    [Parameter(Mandatory = $true)]
    [string]$ReleaseSourcePath,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$releaseTag = "v0.3.1"
$releaseCommit = "f488ba0c01ec458b5e99fa2b5fc9b539872ae1ec"
$releaseAsset = "RCMetaStudio-windows-x64.zip"
$releaseAssetSha256 = "aeb6c9fdcbf00d8762284260ce3cdd7ffa722207d29599d1a428fa00ef30f7bd"
$releaseAssetUrl = "https://github.com/AliSalman-et-al/rc-metastudio/releases/download/v0.3.1/$releaseAsset"
$expectedCases = @(
    "amino-binary-random",
    "continuous-random",
    "lymph-diagnostic-random-dor",
    "amino-binary-cumulative",
    "amino-binary-leave-one-out",
    "continuous-cumulative",
    "continuous-leave-one-out",
    "amino-binary-meta-regression",
    "continuous-meta-regression",
    "amino-binary-subgroup",
    "continuous-subgroup"
)

function Get-CheckedCommandOutput {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    $output = & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $Command $($Arguments -join ' ')"
    }
    return ($output | Out-String).Trim()
}

function Assert-ExpectedVersion {
    param(
        [string]$Name,
        [string]$Observed,
        [string]$Expected
    )

    if ($Observed -ne $Expected) {
        throw "$Name version mismatch: expected '$Expected', observed '$Observed'."
    }
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).ProviderPath
$releaseSource = (Resolve-Path -LiteralPath $ReleaseSourcePath).ProviderPath
$outputRoot = Join-Path $repoRoot $OutputPath
if ([System.IO.Path]::IsPathRooted($OutputPath)) {
    $outputRoot = $OutputPath
}
$outputRoot = [System.IO.Path]::GetFullPath($outputRoot)
if (Test-Path -LiteralPath $outputRoot) {
    throw "Capture output path already exists; use a fresh path: '$outputRoot'."
}

if ($env:PROCESSOR_ARCHITECTURE -ne "AMD64") {
    throw "Release-source capture requires a Windows x64 runner; found '$env:PROCESSOR_ARCHITECTURE'."
}

$actualCommit = Get-CheckedCommandOutput -Command "git" -Arguments @("-C", $releaseSource, "rev-parse", "HEAD")
$tagCommit = Get-CheckedCommandOutput -Command "git" -Arguments @("-C", $releaseSource, "rev-parse", "$releaseTag^{commit}")
if ($actualCommit -ne $releaseCommit -or $tagCommit -ne $releaseCommit) {
    throw "Pinned $releaseTag source mismatch: expected $releaseCommit, HEAD=$actualCommit, tag=$tagCommit."
}

$rtoolsBin = "C:\rtools45\x86_64-w64-mingw32.static.posix\bin"
foreach ($tool in @("gcc.exe", "g++.exe")) {
    if (-not (Test-Path -LiteralPath (Join-Path $rtoolsBin $tool))) {
        throw "The hosted Windows image is missing Rtools 4.5 compiler '$tool' at '$rtoolsBin'."
    }
}

$null = New-Item -ItemType Directory -Force -Path $outputRoot
$archivePath = Join-Path $outputRoot $releaseAsset
$archiveRoot = Join-Path $outputRoot "archive"
$baselinePath = Join-Path $outputRoot "baseline"
$captureLog = Join-Path $outputRoot "capture.log"

Write-Host "Downloading the SHA-256-pinned v0.3.1 Windows release archive."
$downloaded = $false
for ($attempt = 1; $attempt -le 3; $attempt++) {
    try {
        Invoke-WebRequest -Uri $releaseAssetUrl -OutFile $archivePath -ErrorAction Stop
        $downloaded = $true
        break
    }
    catch {
        if (Test-Path -LiteralPath $archivePath) {
            Remove-Item -LiteralPath $archivePath -Force
        }
        if ($attempt -eq 3) {
            throw "Could not download the published v0.3.1 Windows archive after three attempts: $($_.Exception.Message)"
        }
        Start-Sleep -Seconds 3
    }
}
if (-not $downloaded) {
    throw "The published v0.3.1 Windows archive download did not complete."
}

$observedAssetSha256 = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($observedAssetSha256 -ne $releaseAssetSha256) {
    throw "Published archive hash mismatch: expected $releaseAssetSha256, observed $observedAssetSha256."
}

Write-Host "Archive hash verified; extracting the embedded R runtime and RCMetaR library."
$null = New-Item -ItemType Directory -Force -Path $archiveRoot
Expand-Archive -LiteralPath $archivePath -DestinationPath $archiveRoot
$appRoot = Join-Path $archiveRoot "RCMetaStudio-0.3.1-windows-x64"
$rHome = Join-Path $appRoot "R"
$rLibrary = Join-Path $rHome "library"
$rscript = Join-Path $rHome "bin\Rscript.exe"
$rcmetarDescription = Join-Path $rLibrary "RCMetaR\DESCRIPTION"
foreach ($path in @(
    (Join-Path $appRoot "RCMetaStudio.exe"),
    $rscript,
    $rcmetarDescription
)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Published archive layout is missing required release file '$path'."
    }
}
if ((Get-Content -Raw -LiteralPath $rcmetarDescription) -notmatch "(?m)^Version:\s*0\.3\.1\s*$") {
    throw "Published archive does not contain RCMetaR 0.3.1."
}

$env:R_HOME = $rHome
$env:R_LIBS = $rLibrary
$env:R_LIBS_USER = $rLibrary
$env:RCMS_R_HOME = $rHome
$env:RCMS_R_LIBS = $rLibrary
$env:RPY2_CFFI_MODE = "API"
$env:PATH = "$rtoolsBin;$rHome\bin\x64;$rHome\bin;$env:PATH"
$env:CC = "gcc"
$env:CXX = "g++"
$env:LDSHARED = "gcc -shared"

$runtimeCheckScript = Join-Path $outputRoot "verify-release-runtime.R"
@'
release_package_version <- function(package) {
  version <- utils::packageDescription(
    package,
    fields = "Version",
    lib.loc = Sys.getenv("R_LIBS")
  )
  if (length(version) != 1L || is.na(version)) {
    stop("Could not read the release library Version field for ", package)
  }
  unname(version)
}
versions <- c(
  as.character(getRversion()),
  release_package_version("RCMetaR"),
  release_package_version("mada"),
  release_package_version("metafor"),
  release_package_version("meta")
)
cat(paste(versions, collapse="|"), "\n", sep="")
cat(normalizePath(R.home()), "\n", sep="")
cat(normalizePath(find.package("RCMetaR")), "\n", sep="")
'@ | Set-Content -LiteralPath $runtimeCheckScript -Encoding ASCII
$runtimeCheckOutput = Get-CheckedCommandOutput -Command $rscript -Arguments @("--vanilla", $runtimeCheckScript)
$runtimeCheckLines = @($runtimeCheckOutput -split "\r?\n")
if ($runtimeCheckLines.Count -ne 3) {
    throw "Could not resolve the expected R and bundled package version tuple from the release archive."
}
$runtimeVersions = @($runtimeCheckLines[0] -split "\|")
if ($runtimeVersions.Count -ne 5) {
    throw "The release archive returned an unexpected package-version tuple."
}
Assert-ExpectedVersion -Name "R" -Observed $runtimeVersions[0] -Expected "4.6.1"
Assert-ExpectedVersion -Name "RCMetaR" -Observed $runtimeVersions[1] -Expected "0.3.1"
Assert-ExpectedVersion -Name "mada" -Observed $runtimeVersions[2] -Expected "0.5.12"
Assert-ExpectedVersion -Name "metafor" -Observed $runtimeVersions[3] -Expected "5.0-1"
Assert-ExpectedVersion -Name "meta" -Observed $runtimeVersions[4] -Expected "8.5-0"
$rHomeReportedByR = $runtimeCheckLines[1]
if ([System.IO.Path]::GetFullPath($rHomeReportedByR) -ine [System.IO.Path]::GetFullPath($rHome)) {
    throw "Rscript resolved '$rHomeReportedByR' instead of the release archive runtime '$rHome'."
}
$loadedRcmetarPath = $runtimeCheckLines[2]
if ([System.IO.Path]::GetFullPath($loadedRcmetarPath) -ine [System.IO.Path]::GetFullPath((Join-Path $rLibrary "RCMetaR"))) {
    throw "R loaded RCMetaR from '$loadedRcmetarPath' instead of the release archive library."
}

Write-Host "Embedded R, RCMetaR, and statistical package versions verified."
Write-Host "Installing the v0.3.1 source environment from its locked dependencies."
Get-CheckedCommandOutput -Command "uv" -Arguments @("sync", "--locked", "--python", "3.11.9", "--project", $releaseSource) | Out-Null
$python = Join-Path $releaseSource ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "uv did not create the v0.3.1 source environment at '$python'."
}

Write-Host "Building the API-mode rpy2 bridge against the archive's R headers and DLLs."
Get-CheckedCommandOutput -Command "uv" -Arguments @(
    "pip", "install", "--python", $python, "--reinstall", "--no-binary", "rpy2-rinterface",
    "--config-settings=--global-option=build",
    "--config-settings=--global-option=--compiler=mingw32",
    "rpy2-rinterface==3.6.6"
) | Out-Null

$rpy2Version = Get-CheckedCommandOutput -Command $python -Arguments @(
    "-c", "from importlib.metadata import version; print(version('rpy2'))"
)
Assert-ExpectedVersion -Name "rpy2" -Observed $rpy2Version -Expected "3.6.7"
$rpyRuntimeVersion = Get-CheckedCommandOutput -Command $python -Arguments @(
    "-c", "from rpy2.robjects import r; print(r('as.character(getRversion())')[0])"
)
Assert-ExpectedVersion -Name "rpy2-connected R" -Observed $rpyRuntimeVersion -Expected "4.6.1"
$rpyRuntimeRoot = Get-CheckedCommandOutput -Command $python -Arguments @(
    "-c", "from pathlib import Path; from rpy2.robjects import r; print(Path(str(r('normalizePath(R.home())')[0])).resolve())"
)
if ([System.IO.Path]::GetFullPath($rpyRuntimeRoot) -ine [System.IO.Path]::GetFullPath($rHome)) {
    throw "rpy2 connected to '$rpyRuntimeRoot' instead of the release archive runtime '$rHome'."
}
$pythonVersion = Get-CheckedCommandOutput -Command $python -Arguments @("--version")
$pyqtVersion = Get-CheckedCommandOutput -Command $python -Arguments @(
    "-c", "from importlib.metadata import version; print(version('PyQt6'))"
)
Assert-ExpectedVersion -Name "Python" -Observed $pythonVersion -Expected "Python 3.11.9"
Assert-ExpectedVersion -Name "PyQt6" -Observed $pyqtVersion -Expected "6.11.0"

$null = New-Item -ItemType Directory -Force -Path $baselinePath
$env:RCMS_GOLDEN_CAPTURE_MODE = "local-debug"
$env:RCMS_GOLDEN_CAPTURE_COMMAND = "v0.3.1 tagged-source golden harness against the SHA-256-pinned v0.3.1 Windows release archive's embedded R and RCMetaR"
Push-Location $releaseSource
try {
    Write-Host "Running the 11-case v0.3.1 tagged-source numerical and semantic capture."
    & $python -m rc_metastudio.golden_analysis --comprehensive-baseline $baselinePath *> $captureLog
    if ($LASTEXITCODE -ne 0) {
        Get-Content -LiteralPath $captureLog -Tail 80
        throw "The v0.3.1 comprehensive golden capture failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

$captureManifestPath = Join-Path $baselinePath "manifest.json"
if (-not (Test-Path -LiteralPath $captureManifestPath)) {
    throw "The v0.3.1 source harness did not produce its comprehensive capture manifest."
}
$captureManifest = Get-Content -Raw -LiteralPath $captureManifestPath | ConvertFrom-Json
$captures = @($captureManifest.curated_golden_set)
$observedCases = @($captures | ForEach-Object { $_.id })
if (($observedCases -join "`n") -ne ($expectedCases -join "`n")) {
    throw "Golden case set/order mismatch. Expected '$($expectedCases -join ', ')'; observed '$($observedCases -join ', ')'."
}
if ($captureManifest.passed -ne $true -or @($captures | Where-Object { $_.status -ne "success" }).Count -ne 0) {
    throw "One or more v0.3.1 source-harness cases failed."
}
if (@($captures | Where-Object { -not $_.texts -or -not $_.outputs }).Count -ne 0) {
    throw "A source-harness case completed without both semantic text and parsed numerical outputs."
}
if (@($captures | Where-Object { $_.authoritative -ne $false }).Count -ne 0) {
    throw "A release-source capture was incorrectly marked as package-authoritative by the v0.3.1 helper."
}

Write-Host "All 11 tagged-source cases passed capture validation."
$manifestHash = (Get-FileHash -LiteralPath $captureManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
$provenance = [ordered]@{
    schema_version = 1
    capture_kind = "v0.3.1-tagged-source-harness-with-published-release-R"
    authority_scope = "Numerical and semantic analysis results from the v0.3.1 tagged source harness using the exact published Windows archive's embedded R and RCMetaR. This is not a run of RCMetaStudio.exe and does not establish packaged executable, GUI, or human journey parity."
    release = [ordered]@{
        tag = $releaseTag
        source_commit = $releaseCommit
        asset_name = $releaseAsset
        asset_url = $releaseAssetUrl
        asset_sha256 = $observedAssetSha256
        archive_internal_root = "RCMetaStudio-0.3.1-windows-x64"
    }
    environment = [ordered]@{
        runner_os = $env:RUNNER_OS
        runner_arch = $env:PROCESSOR_ARCHITECTURE
        runner_image_os = $env:ImageOS
        runner_image_version = $env:ImageVersion
        python = $pythonVersion
        pyqt6 = $pyqtVersion
        rpy2 = $rpy2Version
        r = $runtimeVersions[0]
        rcmetar = $runtimeVersions[1]
        embedded_r_home_confirmed = $true
        embedded_rcmetar_library_confirmed = $true
        mada = $runtimeVersions[2]
        metafor = $runtimeVersions[3]
        meta = $runtimeVersions[4]
        embedded_r_library = "archive-relative:R\library"
    }
    capture = [ordered]@{
        harness_commit = $releaseCommit
        command = "python -m rc_metastudio.golden_analysis --comprehensive-baseline <output-dir>"
        helper_capture_mode = "local-debug"
        helper_authoritative = $false
        case_ids = $observedCases
        case_count = $captures.Count
        all_cases_succeeded = $true
        manifest_sha256 = $manifestHash
    }
    workflow = [ordered]@{
        repository = $env:GITHUB_REPOSITORY
        workflow_ref = $env:GITHUB_WORKFLOW_REF
        source_sha = $env:GITHUB_SHA
        run_id = $env:GITHUB_RUN_ID
        run_attempt = $env:GITHUB_RUN_ATTEMPT
        run_url = "https://github.com/$($env:GITHUB_REPOSITORY)/actions/runs/$($env:GITHUB_RUN_ID)"
    }
}
$provenancePath = Join-Path $outputRoot "release-source-provenance.json"
$provenance | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $provenancePath -Encoding utf8

Write-Host "Captured $($captures.Count) v0.3.1 release-source cases."
Write-Host "Published archive SHA-256: $observedAssetSha256"
Write-Host "Source-harness manifest SHA-256: $manifestHash"
Write-Host "Capture evidence: $outputRoot"
