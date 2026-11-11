Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonExe = currentDir & "\backend\.venv\Scripts\pythonw.exe"
If Not fso.FileExists(pythonExe) Then
    pythonExe = currentDir & "\backend\.venv\Scripts\python.exe"
End If
WshShell.Run """" & pythonExe & """ """ & currentDir & "\desktop_app.py""", 0, False
