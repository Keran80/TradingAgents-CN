# -*- coding: utf-8 -*-
"""
backtest/engine.py 单元测试

测试回测配置和结果类
"""
import pytest

# 条件导入：如果依赖未安装，则跳过整个测试模块
try:
    import pandas as pd
    import numpy as np
    from tradingagents.backtest.engine import (
        BacktestConfig,
        BacktestResult,
        BacktestMode,
        TradeRecord,
    )
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False
    pytest.skip("Required dependencies (pandas/numpy/tradingagents) not installed", allow_module_level=True)


class TestBacktestConfig:
    """BacktestConfig 测试"""

    def test_default_values(self):
        """测试默认配置值"""
        config = BacktestConfig()
        assert config.start_date == "2024-01-01"
        assert config.end_date == "2024-12-31"
        assert config.initial_cash == 1000000.0
        assert config.mode == BacktestMode.EVENT_DRIVEN
        assert config.commission_rate == 0.0003
        assert config.enable_risk is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = BacktestConfig(
            start_date="2023-01-01",
            end_date="2023-06-30",
            initial_cash=500000,
            mode=BacktestMode.VECTORIZED,
            commission_rate=0.0005,
        )
        assert config.start_date == "2023-01-01"
        assert config.initial_cash == 500000
        assert config.mode == BacktestMode.VECTORIZED
        assert config.commission_rate == 0.0005


class TestBacktestResult:
    """BacktestResult 测试"""

    def test_to_dict(self):
        """测试结果字典转换"""
        result = BacktestResult(
            start_date="2024-01-01",
            end_date="2024-06-30",
            initial_cash=1000000,
            final_cash=1100000,
            total_return=0.10,
            annual_return=0.20,
            total_trades=50,
            winning_trades=30,
            losing_trades=20,
            win_rate=0.60,
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["start_date"] == "2024-01-01"
        assert result_dict["total_return"] == "10.00%"
        assert result_dict["annual_return"] == "20.00%"
        assert result_dict["total_trades"] == 50
        assert result_dict["win_rate"] == "60.00%"

    def test_with_trades(self):
        """测试包含交易记录的结果"""
        trades = [
            TradeRecord(
                timestamp="2024-01-02",
                symbol="000001.SZ",
                direction="BUY",
                price=10.5,
                quantity=100,
                commission=3.15,
                slippage=1.05,
            ),
            TradeRecord(
                timestamp="2024-01-10",
                symbol="000001.SZ",
                direction="SELL",
                price=11.0,
                quantity=100,
                commission=3.3,
                slippage=1.1,
            ),
        ]
        
        result = BacktestResult(
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_cash=100000,
            final_cash=101000,
            total_return=0.01,
            annual_return=0.12,
            total_trades=2,
            winning_trades=1,
            losing_trades=1,
            win_rate=0.5,
            trades=trades,
        )
        
        assert len(result.trades) == 2
        assert result.trades[0].direction == "BUY"
        assert result.trades[1].direction == "SELL"

    def test_with_optional_fields_none(self):
        """测试可选字段为None的情况"""
        result = BacktestResult(
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_cash=100000,
            final_cash=101000,
            total_return=0.01,
            annual_return=0.12,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            equity_curve=None,
            daily_returns=None,
        )
        
        assert result.equity_curve is None
        assert result.daily_returns is None

    def test_with_equity_curve(self):
        """测试包含净值曲线的结果"""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity_curve = pd.DataFrame({
            "equity": np.linspace(100000, 110000, 10),
            "cash": np.linspace(100000, 90000, 10),
        }, index=dates)
        
        daily_returns = pd.Series(
            np.random.randn(10) * 0.01,
            index=dates,
        )
        
        result = BacktestResult(
            start_date="2024-01-01",
            end_date="2024-01-10",
            initial_cash=100000,
            final_cash=110000,
            total_return=0.10,
            annual_return=1.2,
            total_trades=5,
            winning_trades=3,
            losing_trades=2,
            win_rate=0.6,
            equity_curve=equity_curve,
            daily_returns=daily_returns,
        )
        
        assert result.equity_curve is not None
        assert len(result.equity_curve) == 10
        assert result.daily_returns is not None
        assert len(result.daily_returns) == 10


class TestTradeRecord:
    """TradeRecord 测试"""

    def test_create_trade(self):
        """测试创建交易记录"""
        trade = TradeRecord(
            timestamp="2024-01-02 10:00:00",
            symbol="000001.SZ",
            direction="BUY",
            price=15.25,
            quantity=200,
            commission=6.1,
            slippage=1.53,
        )
        
        assert trade.symbol == "000001.SZ"
        assert trade.direction == "BUY"
        assert trade.price == 15.25
        assert trade.quantity == 200

    def test_sell_trade(self):
        """测试卖出交易记录"""
        trade = TradeRecord(
            timestamp="2024-01-05",
            symbol="600000.SH",
            direction="SELL",
            price=20.0,
            quantity=100,
            commission=4.0,
            slippage=2.0,
        )
        
        assert trade.direction == "SELL"
        assert trade.quantity == 100
