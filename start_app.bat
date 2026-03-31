@echo off
cd /d "%~dp0"
echo 启动 TradingAgents Streamlit 应用...
echo.
echo 访问 http://localhost:8501 查看
echo.
echo 按 Ctrl+C 停止服务
python -m streamlit run app_streamlit.py --server.port 8501 --server.headless true
