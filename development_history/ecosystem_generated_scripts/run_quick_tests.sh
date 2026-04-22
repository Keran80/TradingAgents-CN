#!/bin/bash

echo "⚡ TradingAgents-CN 快速测试"
python3 -m pytest tests/ -m "not slow and not performance" -v --tb=no
