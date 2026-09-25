$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$target = Join-Path $root 'start.bat'
$shortcutPath = Join-Path $desktop 'LeadPilot.lnk'

if (-not (Test-Path $target)) {
    throw "Launcher not found: $target"
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = $root
$shortcut.WindowStyle = 1
$shortcut.IconLocation = 'cmd.exe,0'
$shortcut.Save()

Write-Host "Desktop shortcut created: $shortcutPath" -ForegroundColor Green
Read-Host 'Press Enter to exit'
