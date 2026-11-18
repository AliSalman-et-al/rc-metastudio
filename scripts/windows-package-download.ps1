# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

function Invoke-DownloadWithRetry {
    param(
        [string]$Uri,
        [string]$PartialPath,
        [int]$MaxAttempts = 3,
        [int]$RetryDelaySeconds = 2,
        [scriptblock]$DownloadOperation = { param($RequestUri, $Destination) Invoke-WebRequest -Uri $RequestUri -OutFile $Destination -ErrorAction Stop },
        [scriptblock]$SleepOperation = { param($Seconds) Start-Sleep -Seconds $Seconds }
    )
    $lastError = $null
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        if (Test-Path -LiteralPath $PartialPath) { Remove-Item -LiteralPath $PartialPath -Force }
        try {
            & $DownloadOperation $Uri $PartialPath
            return
        }
        catch {
            $lastError = $_
            if (Test-Path -LiteralPath $PartialPath) { Remove-Item -LiteralPath $PartialPath -Force }
            if ($attempt -lt $MaxAttempts) { & $SleepOperation $RetryDelaySeconds }
        }
    }
    throw "Could not download '$Uri' after $MaxAttempts attempts: $($lastError.Exception.Message)"
}
