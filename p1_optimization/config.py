# -*- coding: utf-8 -*-
"""
集中配置管理 - P1 优化项
支持多环境配置
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import os
import json


@dataclass
class APISettings:
    """API 配置"""
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://api.example.com"
    timeout: int = 30
    retry_count: int = 3
    
    @classmethod
    def from_env(cls) -> "APISettings":
        return cls(
            api_key=os.getenv("TRADING_API_KEY", ""),
            api_secret=os.getenv("TRADING_API_SECRET", ""),
            base_url=os.getenv("TRADING_API_URL", "https://api.example.com")
        )


@dataclass
class DatabaseSettings:
    """数据库配置"""
    url: str = "sqlite:///trading.db"
    pool_size: int = 10
    echo: bool = False
    
    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        return cls(
            url=os.getenv("DATABASE_URL", "sqlite:///trading.db"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10"))
        )


@dataclass
class StrategySettings:
    """策略配置"""
    default_strategy: str = "momentum"
    risk_free_rate: float = 0.02
    initial_capital: float = 100000.0
    max_position_size: float = 0.1  # 最大仓位 10%
    stop_loss: float = 0.05  # 止损 5%
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategySettings":
        return cls(**data)


@dataclass
class LogSettings:
    """日志配置"""
    level: str = "INFO"
    file: Optional[str] = "trading.log"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def from_env(cls) -> "LogSettings":
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file=os.getenv("LOG_FILE", "trading.log")
        )


@dataclass
class Settings:
    """集中配置管理"""
    api: APISettings = field(default_factory=APISettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    strategy: StrategySettings = field(default_factory=StrategySettings)
    log: LogSettings = field(default_factory=LogSettings)
    
    @classmethod
    def load(cls, config_file: Optional[str] = None) -> "Settings":
        """
        加载配置
        
        优先级：
        1. 配置文件
        2. 环境变量
        3. 默认值
        """
        settings = cls()
        
        # 从配置文件加载
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'api' in config:
                    settings.api = APISettings.from_dict(config['api'])
                if 'database' in config:
                    settings.database = DatabaseSettings.from_dict(config['database'])
                if 'strategy' in config:
                    settings.strategy = StrategySettings.from_dict(config['strategy'])
        
        # 从环境变量加载 (覆盖配置文件)
        settings.api = APISettings.from_env()
        settings.database = DatabaseSettings.from_env()
        settings.log = LogSettings.from_env()
        
        return settings
    
    def save(self, config_file: str) -> None:
        """保存配置到文件"""
        config = {
            'api': {
                'api_key': self.api.api_key,
                'base_url': self.api.base_url,
                'timeout': self.api.timeout
            },
            'database': {
                'url': self.database.url,
                'pool_size': self.database.pool_size
            },
            'strategy': {
                'default_strategy': self.strategy.default_strategy,
                'initial_capital': self.strategy.initial_capital,
                'max_position_size': self.strategy.max_position_size
            },
            'log': {
                'level': self.log.level,
                'file': self.log.file
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)


# ========== 使用示例 ==========

# 加载配置
# settings = Settings.load("config.json")

# 访问配置
# api_key = settings.api.api_key
# db_url = settings.database.url
# strategy = settings.strategy.default_strategy

# 保存配置
# settings.save("config.json")
