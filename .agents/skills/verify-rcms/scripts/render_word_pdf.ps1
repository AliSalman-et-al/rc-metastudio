param([string]$InputPath, [string]$OutputPath)
$ErrorActionPreference = 'Stop'
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class RcmsWordProcess {
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);
}
'@
$existingIds = @(Get-Process WINWORD -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$word = $null
$document = $null
$owned = $false
try {
    $word = New-Object -ComObject Word.Application
    $document = $word.Documents.Add()
    [uint32]$wordProcessId = 0
    [void][RcmsWordProcess]::GetWindowThreadProcessId([IntPtr]$document.ActiveWindow.Hwnd, [ref]$wordProcessId)
    $owned = $existingIds -notcontains $wordProcessId
    if (-not $owned) { throw 'Word returned an existing process; its state will not be changed' }
    $word.Visible = $false
    $word.DisplayAlerts = 0
    [object]$discard = 0
    $document.Close([ref]$discard)
    $document = $null
    [object]$source = [string]$InputPath
    [object]$confirm = $false
    [object]$readOnly = $true
    $document = $word.Documents.Open([ref]$source, [ref]$confirm, [ref]$readOnly)
    $document.ExportAsFixedFormat($OutputPath, 17)
    @{renderer='Microsoft Word'; source=$InputPath; output=$OutputPath; pages=$document.ComputeStatistics(2)} | ConvertTo-Json
}
finally {
    [object]$discard = 0
    if ($null -ne $document) { $document.Close([ref]$discard) }
    if ($owned -and $null -ne $word) { $word.Quit([ref]$discard) }
}
