# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

function Stop-BoundedPackageProcessTree {
    param(
        [int]$ProcessId,
        [int]$TimeoutMilliseconds = 30000,
        [int]$TerminationWaitMilliseconds = 5000
    )
    $cleanup = $null
    $cleanupHandle = $null
    $cleanupTimedOut = $false
    $cleanupTerminationError = $null
    try {
        $cleanup = Start-Process -FilePath taskkill.exe -ArgumentList @(
            "/PID", $ProcessId, "/T", "/F"
        ) -PassThru -WindowStyle Hidden
        $cleanupHandle = $cleanup.Handle
        if ($null -eq $cleanupHandle -or $cleanupHandle -eq [IntPtr]::Zero) {
            throw "Could not acquire a valid taskkill process handle for process $ProcessId."
        }
        if (-not $cleanup.WaitForExit($TimeoutMilliseconds)) {
            $cleanupTimedOut = $true
            try {
                $cleanup.Kill()
            }
            catch {
                throw "taskkill exceeded its $TimeoutMilliseconds-millisecond bound and could not be terminated: $($_.Exception.Message)"
            }
            if (-not $cleanup.WaitForExit($TerminationWaitMilliseconds)) {
                throw "taskkill remained alive after its termination wait of $TerminationWaitMilliseconds milliseconds."
            }
        }
        $cleanup.WaitForExit()
        $cleanup.Refresh()
        $cleanupExitCode = $cleanup.ExitCode
        if ($cleanupTimedOut) {
            throw "taskkill exceeded its $TimeoutMilliseconds-millisecond cleanup bound."
        }
        if ($null -eq $cleanupExitCode -or $cleanupExitCode -ne 0) {
            throw "taskkill failed with exit code '$cleanupExitCode' for process $ProcessId."
        }
    }
    finally {
        if ($null -ne $cleanup) {
            $cleanupStillRunning = $true
            try { $cleanupStillRunning = -not $cleanup.HasExited } catch {}
            if ($cleanupStillRunning) {
                try { $cleanup.Kill() } catch { $cleanupTerminationError = $_ }
                if ($null -eq $cleanupTerminationError) {
                    try {
                        if (-not $cleanup.WaitForExit($TerminationWaitMilliseconds)) {
                            $cleanupTerminationError = "taskkill did not terminate within $TerminationWaitMilliseconds milliseconds."
                        }
                    }
                    catch {
                        $cleanupTerminationError = $_
                    }
                }
            }
            [GC]::KeepAlive($cleanupHandle)
            $cleanup.Dispose()
            if ($null -ne $cleanupTerminationError) {
                throw "Could not release bounded taskkill process: $cleanupTerminationError"
            }
        }
    }
}

function Invoke-BoundedPackageProcess {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList,
        [int]$TimeoutSeconds = 900,
        [string]$StandardOutputPath,
        [string]$StandardErrorPath,
        [switch]$Visible
    )
    $startArguments = @{
        FilePath = $FilePath
        ArgumentList = $ArgumentList
        PassThru = $true
    }
    if ($StandardOutputPath) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StandardOutputPath) | Out-Null
        $startArguments.RedirectStandardOutput = $StandardOutputPath
    }
    if ($StandardErrorPath) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StandardErrorPath) | Out-Null
        $startArguments.RedirectStandardError = $StandardErrorPath
    }
    if (-not $Visible) { $startArguments.WindowStyle = "Hidden" }
    $process = $null
    $processHandle = $null
    $lifecycleCleanupError = $null
    try {
        $process = Start-Process @startArguments
        # Acquire the native handle before the child can exit. Without an open
        # handle, Windows may release its administrative record before PowerShell
        # reads ExitCode, which surfaced as $null for the redirected GUI smoke.
        $processHandle = $process.Handle
        if ($null -eq $processHandle -or $processHandle -eq [IntPtr]::Zero) {
            throw "Could not acquire a valid handle for bounded package process $($process.Id)."
        }
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            Stop-BoundedPackageProcessTree -ProcessId $process.Id
            if (-not $process.WaitForExit(30000)) {
                throw "Packaged process watchdog cleanup failed after taskkill: $FilePath $($ArgumentList -join ' ')"
            }
            throw "Packaged process exceeded its $TimeoutSeconds-second watchdog and its process tree was terminated: $FilePath $($ArgumentList -join ' ')"
        }
        $process.WaitForExit()
        $process.Refresh()
        $exitCode = $process.ExitCode
        if ($null -eq $exitCode) {
            throw "Packaged process exited without a readable exit code: $FilePath $($ArgumentList -join ' ')"
        }
        return [int]$exitCode
    }
    finally {
        if ($null -ne $process) {
            $processStillRunning = $true
            try { $processStillRunning = -not $process.HasExited } catch {}
            if ($processStillRunning) {
                try {
                    Stop-BoundedPackageProcessTree -ProcessId $process.Id
                    if (-not $process.WaitForExit(30000)) {
                        $lifecycleCleanupError = "child did not exit within 30000 milliseconds after taskkill"
                    }
                }
                catch {
                    $lifecycleCleanupError = $_
                }
            }
            [GC]::KeepAlive($processHandle)
            $process.Dispose()
            if ($null -ne $lifecycleCleanupError) {
                throw "Could not release bounded package process: $lifecycleCleanupError"
            }
        }
    }
}
