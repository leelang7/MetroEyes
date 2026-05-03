' MetroEyes - silent launcher with status report
' Double-click: spawns 4 components hidden, then reports each status via MsgBox.

Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = root

If Not fso.FolderExists(root & "\logs") Then fso.CreateFolder root & "\logs"

' 1. backend
sh.Run "cmd /c """"" & root & "\.venv\Scripts\pythonw.exe"" -u -m src.cv.tesla_bev --port 8765 --model yolo11s.pt --imgsz 1280 --conf 0.18 > """ & root & "\logs\backend.log"" 2>&1""", 0, False
' 2. publisher
sh.Run "cmd /c """"" & root & "\.venv\Scripts\pythonw.exe"" """ & root & "\scripts\feed_video.py"" > """ & root & "\logs\publisher.log"" 2>&1""", 0, False
' 3. static server :5173
sh.Run "cmd /c """"" & root & "\.venv\Scripts\pythonw.exe"" -m http.server 5173 > """ & root & "\logs\static.log"" 2>&1""", 0, False
' 4. cloudflared named tunnel (config 있을 때만)
cfRunning = "skipped (no cloudflared-config.yml)"
If fso.FileExists(root & "\cloudflared-config.yml") Then
  cf = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"
  If Not fso.FileExists(cf) Then cf = "cloudflared"
  sh.Run "cmd /c """"" & cf & """ tunnel --config """ & root & "\cloudflared-config.yml"" run > """ & root & "\logs\cloudflared.log"" 2>&1""", 0, False
  cfRunning = "spawned"
End If

' yolo 로딩 대기 — backend listen 시작까지 최대 25초
WScript.Sleep 8000

' 4컴포넌트 상태 검증 (port LISTENING 또는 process check)
Function PortListening(port)
    Dim out, line
    out = sh.Exec("cmd /c netstat -ano").StdOut.ReadAll
    PortListening = (InStr(out, "0.0.0.0:" & port & " ") > 0 And InStr(out, "LISTENING") > 0)
End Function

Function ProcessAlive(name)
    Dim out
    out = sh.Exec("cmd /c tasklist /FI ""IMAGENAME eq " & name & """ /NH").StdOut.ReadAll
    ProcessAlive = (InStr(out, name) > 0)
End Function

' 8765 LISTEN 까지 한 번 더 대기 (yolo 로딩 길면)
For i = 1 To 8
    If PortListening(8765) Then Exit For
    WScript.Sleep 2000
Next

beStatus = "DEAD"
If PortListening(8765) Then beStatus = "LISTEN :8765"
ssStatus = "DEAD"
If PortListening(5173) Then ssStatus = "LISTEN :5173"
pubStatus = "unknown"
' publisher = pythonw 추가 — 8765 client 연결 확인
pubAlive = ProcessAlive("pythonw.exe")
If pubAlive Then pubStatus = "alive (pythonw)"

cfStatus = cfRunning
If fso.FileExists(root & "\cloudflared-config.yml") Then
    If ProcessAlive("cloudflared.exe") Then
        cfStatus = "alive (cloudflared.exe)"
    Else
        cfStatus = "DEAD - check logs\cloudflared.log"
    End If
End If

msg = "MetroEyes Status" & vbCrLf & vbCrLf & _
      "Backend (8765)   : " & beStatus & vbCrLf & _
      "Publisher        : " & pubStatus & vbCrLf & _
      "Static (5173)    : " & ssStatus & vbCrLf & _
      "Cloudflared      : " & cfStatus & vbCrLf & vbCrLf & _
      "Demo URL: https://leelang7.github.io/MetroEyes/" & vbCrLf & _
      "Logs: " & root & "\logs\"

iconInfo = 64  ' info
If beStatus = "DEAD" Or InStr(cfStatus, "DEAD") > 0 Then iconInfo = 48  ' warning
MsgBox msg, iconInfo, "MetroEyes - Start"
