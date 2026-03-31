' Start Flask server in background
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /k cd /d c:\Users\13905\WorkBuddy\Claw\TradingAgents-CN && python web_api.py", 0, False
