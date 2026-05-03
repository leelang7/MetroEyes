' MetroEyes - current status check (no spawn, no kill)
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)

Function PortListening(port)
    Dim out
    out = sh.Exec("cmd /c netstat -ano").StdOut.ReadAll
    PortListening = (InStr(out, "0.0.0.0:" & port & " ") > 0 And InStr(out, "LISTENING") > 0)
End Function

Function ProcessAlive(name)
    Dim out
    out = sh.Exec("cmd /c tasklist /FI ""IMAGENAME eq " & name & """ /NH").StdOut.ReadAll
    ProcessAlive = (InStr(out, name) > 0)
End Function

Function ProcCount(name)
    Dim out, c, lines, line
    c = 0
    out = sh.Exec("cmd /c tasklist /FI ""IMAGENAME eq " & name & """ /NH").StdOut.ReadAll
    lines = Split(out, vbCrLf)
    For Each line In lines
        If InStr(line, name) > 0 Then c = c + 1
    Next
    ProcCount = c
End Function

' 외부 wss 도달 검증 (Cloudflare DNS 1.1.1.1로 해석)
externalOK = "untested"
If ProcessAlive("cloudflared.exe") Then
    Dim res
    res = sh.Run("cmd /c nslookup app.allthatai.kr 1.1.1.1 > """ & root & "\logs\status_dns.tmp"" 2>&1", 0, True)
    Dim t
    t = ""
    If fso.FileExists(root & "\logs\status_dns.tmp") Then
        Set ts = fso.OpenTextFile(root & "\logs\status_dns.tmp", 1)
        If Not ts.AtEndOfStream Then t = ts.ReadAll
        ts.Close
    End If
    If InStr(t, "104.21") > 0 Or InStr(t, "172.67") > 0 Then
        externalOK = "DNS OK (Cloudflare IPs resolved)"
    Else
        externalOK = "DNS FAIL or propagating"
    End If
End If

beStatus = "DEAD"
If PortListening(8765) Then beStatus = "LISTEN :8765"
ssStatus = "DEAD"
If PortListening(5173) Then ssStatus = "LISTEN :5173"
pyN = ProcCount("pythonw.exe")
cfN = ProcCount("cloudflared.exe")

' 마지막 backend 활동 (logs/backend.log mtime 비교)
beAge = "n/a"
If fso.FileExists(root & "\logs\backend.log") Then
    Set bf = fso.GetFile(root & "\logs\backend.log")
    diff = DateDiff("s", bf.DateLastModified, Now)
    beAge = diff & "s ago"
End If

msg = "MetroEyes Status" & vbCrLf & vbCrLf & _
      "Backend (8765)   : " & beStatus & vbCrLf & _
      "Static (5173)    : " & ssStatus & vbCrLf & _
      "pythonw procs    : " & pyN & vbCrLf & _
      "cloudflared      : " & cfN & " procs" & vbCrLf & _
      "Last backend log : " & beAge & vbCrLf & _
      "External DNS     : " & externalOK & vbCrLf & vbCrLf & _
      "Demo URL: https://leelang7.github.io/MetroEyes/" & vbCrLf & _
      "Logs: " & root & "\logs\"

icon = 64
If beStatus = "DEAD" Then icon = 48
MsgBox msg, icon, "MetroEyes - Status"
