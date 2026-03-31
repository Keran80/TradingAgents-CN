@echo off
echo 启动 TradingAgents Dashboard...
echo.
echo 访问地址: http://localhost:8888
echo 按 Ctrl+C 停止
echo.
python -c "import sys; sys.path.insert(0, '.'); from tradingagents.dashboard import run_dashboard; run_dashboard(port=8888, debug=True)"
pause