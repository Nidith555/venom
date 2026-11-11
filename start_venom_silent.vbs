' Venom Silent Background Runner
' Runs the wake listener invisibly with zero terminal windows
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
backendDir = currentDir & "\backend"
WshShell.CurrentDirectory = backendDir
pythonExe = backendDir & "\.venv\Scripts\python.exe"
scriptPath = backendDir & "\venom_wake_service.py"
WshShell.Run """" & pythonExe & """ """ & scriptPath & """", 0, False
