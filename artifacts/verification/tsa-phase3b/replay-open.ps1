param([Parameter(Mandatory)][string]$Checkout)

$ErrorActionPreference = 'Stop'
$test = 'tests/e2e/analysis_settings_workflows.py'
foreach ($revision in @('8b6b68c1', '2d31c8fd')) {
    git -C $Checkout switch --detach $revision
    if ($LASTEXITCODE -ne 0) { throw "Unable to check out $revision" }
    if (git -C $Checkout status --porcelain -- $test) { throw "The desktop test already has changes" }
    $file = Join-Path $Checkout $test
    $source = [IO.File]::ReadAllText($file)
    $continuation = '    window.action_go.trigger()'
    $index = $source.IndexOf($continuation)
    if ($index -lt 0) { throw 'Project-switch checkpoint not found' }
    try {
        $source = $source.Insert($index, "    record('review-second-project-opened', window)`n    return`n")
        [IO.File]::WriteAllText($file, $source)
        $proof = (New-Item -ItemType Directory -Force "$PSScriptRoot/$revision").FullName
        git -C $Checkout diff -- $test | Set-Content "$proof/review-open.patch"
        & "$PSScriptRoot/replay.ps1" -Checkout $Checkout -Label $revision -ReviewOnly -Offscreen
    } finally {
        git -C $Checkout restore -- $test
    }
}
