' MetroEyes — silent launcher
' 더블클릭 시 cmd/PowerShell 창 한 개도 안 뜸.
' 컴포넌트: backend(pythonw) + publisher(pythonw) + 정적서버(pythonw) + cloudflared named tunnel
' 산출 로그: logs/backend.log, logs/publisher.log, logs/cloudflared.log, logs/static.log

Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = root

If Not fso.FolderExists(root & "\logs") Then fso.CreateFolder root & "\logs"

' backend
sh.Run "cmd /c """"" & root & "\.venv\Scripts\pythonw.exe"" -u -m src.cv.tesla_bev --port 8765 --model yolo11s.pt --imgsz 1280 --conf 0.18 > """ & root & "\logs\backend.log"" 2>&1""", 0, False
' publisher
sh.Run "cmd /c """"" & root & "\.venv\Scripts\pythonw.exe"" """ & root & "\scripts\feed_video.py"" > """ & root & "\logs\publisher.log"" 2>&1""", 0, False
' 정적 서버 (5173)
sh.Run "cmd /c """"" & root & "\.venv\Scripts\pythonw.exe"" -m http.server 5173 > """ & root & "\logs\static.log"" 2>&1""", 0, False
' cloudflared named tunnel — config 파일 있으면 실행, 없으면 skip
If fso.FileExists(root & "\cloudflared-config.yml") Then
  sh.Run "cmd /c ""cloudflared tunnel --config """ & root & "\cloudflared-config.yml"" run > """ & root & "\logs\cloudflared.log"" 2>&1""", 0, False
End If
