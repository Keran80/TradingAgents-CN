# -*- coding: utf-8 -*-
"""
config.py 单元测试

测试配置管理系统
"""
import pytest
import os
from tradingagents.config import (
    APISettings,
    DatabaseSettings,
    StrategySettings,
    LogSettings,
    Settings,
)


class TestAPISettings:
    """APISettings 测试"""

    def test_default_values(self):
        """测试默认值"""
        settings = APISettings()
        assert settings.api_key == ""
        assert settings.api_secret == ""
        assert settings.base_url == "https://api.example.com"
        assert settings.timeout == 30
        assert settings.retry_count == 3

    def test_from_env_with_values(self):
        """测试从环境变量加载（有值）"""
        os.environ["TRADING_API_KEY"] = "test_key"
        os.environ["TRADING_API_SECRET"] = "test_secret"
        os.environ["TRADING_API_URL"] = "https://test.api.com"
        
        try:
            settings = APISettings.from_env()
            assert settings.api_key == "test_key"
            assert settings.api_secret == "test_secret"
            assert settings.base_url == "https://test.api.com"
        finally:
            del os.environ["TRADING_API_KEY"]
            del os.environ["TRADING_API_SECRET"]
            del os.environ["TRADING_API_URL"]

    def test_from_env_empty_values(self):
        """测试从环境变量加载（空值）"""
        # 确保环境变量不存在
        for key in ["TRADING_API_KEY", "TRADING_API_SECRET", "TRADING_API_URL"]:
            if key in os.environ:
                del os.environ[key]
        
        settings = APISettings.from_env()
        assert settings.api_key == ""
        assert settings.base_url == "https://api.example.com"


class TestDatabaseSettings:
    """DatabaseSettings 测试"""

    def test_default_values(self):
        """测试默认值"""
        settings = DatabaseSettings()
        assert settings.url == "sqlite:///trading.db"
        assert settings.pool_size == 10
        assert settings.echo is False

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "url": "postgresql://localhost/test",
            "pool_size": 20,
            "echo": True,
        }
        settings = DatabaseSettings(**data)
        assert settings.url == "postgresql://localhost/test"
        assert settings.pool_size == 20
        assert settings.echo is True


class TestStrategySettings:
    """StrategySettings 测试"""

    def test_default_values(self):
        """测试默认值"""
        settings = StrategySettings()
        assert settings.default_strategy == "momentum"
        assert settings.risk_free_rate == 0.02
        assert settings.initial_capital == 100000.0
        assert settings.max_position_size == 0.1
        assert settings.stop_loss == 0.05

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "default_strategy": "mean_reversion",
            "initial_capital": 500000,
        }
        settings = StrategySettings.from_dict(data)
        assert settings.default_strategy == "mean_reversion"
        assert settings.initial_capital == 500000.0


class TestLogSettings:
    """LogSettings 测试"""

    def test_default_values(self):
        """测试默认值"""
        settings = LogSettings()
        assert settings.level == "INFO"
        assert settings.file == "trading.log"
        assert "%(asctime)s" in settings.format

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "level": "DEBUG",
            "file": "custom.log",
            "format": "%(message)s",
        }
        settings = LogSettings.from_dict(data)
        assert settings.level == "DEBUG"
        assert settings.file == "custom.log"
        assert settings.format == "%(message)s"


class TestSettings:
    """Settings 集成测试"""

    def test_default_load(self):
        """测试默认加载"""
        settings = Settings.load()
        assert settings.api.api_key == ""
        assert settings.database.url == "sqlite:///trading.db"
        assert settings.log.level == "INFO"

    def test_load_with_env_override(self):
        """测试环境变量选择性覆盖"""
        os.environ["TRADING_API_KEY"] = "env_key"
        os.environ["LOG_LEVEL"] = "WARNING"
        
        try:
            settings = Settings.load()
            # 环境变量有值，应该覆盖
            assert settings.api.api_key == "env_key"
            assert settings.log.level == "WARNING"
        finally:
            del os.environ["TRADING_API_KEY"]
            del os.environ["LOG_LEVEL"]

    def test_load_partial_env_does_not_override(self):
        """测试部分环境变量不覆盖配置"""
        # 仅设置API_KEY，不设置其他
        os.environ["TRADING_API_KEY"] = "test_key"
        
        try:
            settings = Settings.load()
            assert settings.api.api_key == "test_key"
            # 其他字段应使用默认值
            assert settings.api.timeout == 30
            assert settings.database.pool_size == 10
        finally:
            del os.environ["TRADING_API_KEY"]
