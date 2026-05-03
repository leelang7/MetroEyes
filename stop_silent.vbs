' MetroEyes - stop with status report
Set sh = CreateObject("WScript.Shell")

' Count BEFORE
Function ProcCount(name)
    Dim out, c
    c = 0
    out = sh.Exec("cmd /c tasklist /FI ""IMAGENAME eq " & name & """ /NH").StdOut.ReadAll
    Dim lines, line
    lines = Split(out, vbCrLf)
    For Each line In lines
        If InStr(line, name) > 0 Then c = c + 1
    Next
    ProcCount = c
End Function

pyBefore = ProcCount("pythonw.exe")
cfBefore = ProcCount("cloudflared.exe")

' Kill
sh.Run "cmd /c taskkill /F /IM pythonw.exe /IM cloudflared.exe", 0, True

WScript.Sleep 1500

pyAfter = ProcCount("pythonw.exe")
cfAfter = ProcCount("cloudflared.exe")

msg = "MetroEyes Stop" & vbCrLf & vbCrLf & _
      "pythonw.exe  : " & pyBefore & " -> " & pyAfter & " killed=" & (pyBefore - pyAfter) & vbCrLf & _
      "cloudflared  : " & cfBefore & " -> " & cfAfter & " killed=" & (cfBefore - cfAfter)

MsgBox msg, 64, "MetroEyes - Stop"
