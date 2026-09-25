Set WshShell = CreateObject("WScript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
launcherPath = scriptDir & "\start.bat"
WshShell.Run Chr(34) & launcherPath & Chr(34), 0, False
