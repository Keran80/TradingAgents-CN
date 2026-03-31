Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -NoExit -Command cd c:\Users\13905\WorkBuddy\Claw\TradingAgents-CN; echo '' | python -m streamlit run app_streamlit.py --server.port 8501", 0, False
Set WshShell = Nothing
