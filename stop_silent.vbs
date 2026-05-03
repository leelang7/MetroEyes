' MetroEyes — stop all silently
Set sh = CreateObject("WScript.Shell")
sh.Run "cmd /c taskkill /F /IM pythonw.exe /IM cloudflared.exe", 0, True
