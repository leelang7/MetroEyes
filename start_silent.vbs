' MetroEyes — silent launcher
' 더블클릭 시 cmd/PowerShell 창 한 개도 안 뜸. pythonw.exe + ngrok hidden detached.
' 산출 로그: logs/backend.log, logs/publisher.log, logs/ngrok.log

Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = root

' logs 폴더 보장
If Not fso.FolderExists(root & "\logs") Then fso.CreateFolder root & "\logs"

' WshShell.Run(cmd, windowStyle=0 hidden, waitOnReturn=False)
' /c 종료 후 cmd 닫힘. > 로 stdout/stderr file redirect (pythonw 외부에서도 안전).
sh.Run "cmd /c """"" & root & "\.venv\Scripts\pythonw.exe"" -u -m src.cv.tesla_bev --port 8765 --model yolo11s.pt --imgsz 1280 --conf 0.18 > """ & root & "\logs\backend.log"" 2>&1""", 0, False
sh.Run "cmd /c """"" & root & "\.venv\Scripts\pythonw.exe"" """ & root & "\scripts\feed_video.py"" > """ & root & "\logs\publisher.log"" 2>&1""", 0, False
sh.Run "cmd /c ""ngrok http 8765 > """ & root & "\logs\ngrok.log"" 2>&1""", 0, False
sh.Run "cmd /c """"" & root & "\.venv\Scripts\pythonw.exe"" -m http.server 5173 > """ & root & "\logs\static.log"" 2>&1""", 0, False
