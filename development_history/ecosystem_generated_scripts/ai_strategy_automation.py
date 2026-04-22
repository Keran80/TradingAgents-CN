#!/usr/bin/env python3
"""
AI策略开发自动化模块
自动生成和优化AI交易策略
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import inspect

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIStrategyAutomation:
    """AI策略开发自动化"""
    
    def __init__(self, strategies_dir: str = None):
        """初始化自动化模块"""
        self.strategies_dir = strategies_dir or "{PROJECT_DIR}/intelligent_phase3/src/strategies"
        self.templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.strategy_templates = self._load_templates()
        
        # 确保目录存在
        os.makedirs(self.strategies_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        logger.info(f"AI策略开发自动化初始化，策略目录: {self.strategies_dir}")
    
    def _load_templates(self) -> Dict[str, str]:
        """加载策略模板"""
        templates = {}
        
        # 基础模板
        base_template = '''#!/usr/bin/env python3
"""
{strategy_name}
智能阶段3 - AI策略实现
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime

from .ai_strategy_base import AIStrategyBase

logger = logging.getLogger(__name__)

class {class_name}(AIStrategyBase):
    """
    {strategy_description}
    """
    
    def __init__(self):
        """初始化策略"""
        super().__init__(
            name="{strategy_name}",
            version="{version}"
        )
        
        # 默认参数
        self.default_params = {default_params}
    
    def _on_initialize(self):
        """策略初始化逻辑"""
        logger.info(f"{strategy_name}初始化，参数: {self.parameters}")
        
        # 确保所有必要参数都有值
        for key, default_value in self.default_params.items():
            if key not in self.parameters:
                self.parameters[key] = default_value
        
        logger.info("{strategy_name}初始化完成")
    
    async def analyze_market(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场数据
        
        Args:
            data: 市场数据
            
        Returns:
            市场分析结果
        """
        logger.info("开始市场分析...")
        
        # TODO: 实现具体的市场分析逻辑
        # {analysis_instructions}
        
        analysis_result = {{
            "current_price": float(data["close"].iloc[-1]),
            "analysis_time": datetime.now().isoformat(),
            "data_points": len(data),
            "strategy_specific": {{}}
        }}
        
        logger.info("市场分析完成")
        return analysis_result
    
    async def generate_signals(self, analysis_result: Dict[str, Any]) -> List[Dict]:
        """
        生成交易信号
        
        Args:
            analysis_result: 市场分析结果
            
        Returns:
            交易信号列表
        """
        signals = []
        
        # TODO: 实现具体的信号生成逻辑
        # {signal_generation_instructions}
        
        logger.info(f"生成 {{len(signals)}} 个交易信号")
        return signals
    
    def calculate_risk(self, signals: List[Dict], portfolio_value: float) -> Dict[str, float]:
        """
        计算交易风险
        
        Args:
            signals: 交易信号列表
            portfolio_value: 投资组合价值
            
        Returns:
            风险指标字典
        """
        # TODO: 实现具体的风险计算逻辑
        # {risk_calculation_instructions}
        
        risk_metrics = {{
            "total_risk": 0.0,
            "position_risk": 0.0,
            "market_risk": 0.0,
            "signal_quality": 0.0
        }}
        
        return risk_metrics

# 注册策略到工厂
from .ai_strategy_base import StrategyFactory
StrategyFactory.register_strategy("{strategy_key}", {class_name})
'''
        
        templates["base"] = base_template
        
        # RSI策略模板
        rsi_template = '''#!/usr/bin/env python3
"""
RSI策略
基于相对强弱指数的交易策略
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime

from .ai_strategy_base import AIStrategyBase

logger = logging.getLogger(__name__)

class RSIStrategy(AIStrategyBase):
    """
    RSI策略
    
    基于相对强弱指数(RSI)生成交易信号。
    RSI低于30为超卖(买入信号)，高于70为超买(卖出信号)。
    """
    
    def __init__(self):
        """初始化RSI策略"""
        super().__init__(
            name="RSI策略",
            version="1.0.0"
        )
        
        # 默认参数
        self.default_params = {
            "rsi_period": 14,          # RSI计算周期
            "oversold_threshold": 30,   # 超卖阈值
            "overbought_threshold": 70, # 超买阈值
            "position_size": 0.1,       # 仓位大小
            "stop_loss": 0.05,          # 止损比例
            "take_profit": 0.10,        # 止盈比例
            "enable_divergence": True   # 启用背离检测
        }
    
    def _on_initialize(self):
        """策略初始化逻辑"""
        logger.info(f"RSI策略初始化，参数: {self.parameters}")
        
        # 确保所有必要参数都有值
        for key, default_value in self.default_params.items():
            if key not in self.parameters:
                self.parameters[key] = default_value
        
        logger.info("RSI策略初始化完成")
    
    def _calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """
        计算RSI
        
        Args:
            data: 价格数据
            
        Returns:
            RSI序列
        """
        close_prices = data["close"]
        period = self.parameters["rsi_period"]
        
        # 计算价格变化
        delta = close_prices.diff()
        
        # 分离上涨和下跌
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # 计算RS
        rs = gain / loss
        
        # 计算RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    async def analyze_market(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场数据
        
        Args:
            data: 市场数据
            
        Returns:
            市场分析结果
        """
        logger.info("开始RSI市场分析...")
        
        # 计算RSI
        rsi_series = self._calculate_rsi(data)
        current_rsi = rsi_series.iloc[-1] if not rsi_series.empty else None
        
        # 判断市场状态
        if pd.isna(current_rsi):
            rsi_status = "unknown"
        elif current_rsi < self.parameters["oversold_threshold"]:
            rsi_status = "oversold"
        elif current_rsi > self.parameters["overbought_threshold"]:
            rsi_status = "overbought"
        else:
            rsi_status = "neutral"
        
        # 计算RSI趋势
        rsi_trend = "unknown"
        if len(rsi_series) >= 3:
            recent_rsi = rsi_series.iloc[-3:]
            if recent_rsi.is_monotonic_increasing:
                rsi_trend = "rising"
            elif recent_rsi.is_monotonic_decreasing:
                rsi_trend = "falling"
            else:
                rsi_trend = "oscillating"
        
        analysis_result = {
            "current_price": float(data["close"].iloc[-1]),
            "current_rsi": float(current_rsi) if not pd.isna(current_rsi) else None,
            "rsi_status": rsi_status,
            "rsi_trend": rsi_trend,
            "oversold_threshold": self.parameters["oversold_threshold"],
            "overbought_threshold": self.parameters["overbought_threshold"],
            "analysis_time": datetime.now().isoformat(),
            "data_points": len(data)
        }
        
        logger.info(f"RSI分析完成，状态: {rsi_status}, 趋势: {rsi_trend}")
        return analysis_result
    
    async def generate_signals(self, analysis_result: Dict[str, Any]) -> List[Dict]:
        """
        生成交易信号
        
        Args:
            analysis_result: 市场分析结果
            
        Returns:
            交易信号列表
        """
        signals = []
        
        current_rsi = analysis_result.get("current_rsi")
        rsi_status = analysis_result.get("rsi_status")
        current_price = analysis_result.get("current_price")
        
        if current_rsi is None or current_price <= 0:
            return signals
        
        position_size = self.parameters["position_size"]
        
        # 生成信号
        if rsi_status == "oversold":
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",
                "action": "BUY",
                "price": current_price,
                "quantity": position_size,
                "reason": f"RSI超卖: {current_rsi:.1f} < {self.parameters['oversold_threshold']}",
                "confidence": min((self.parameters['oversold_threshold'] - current_rsi) / 30, 0.95),
                "strategy": self.name,
                "parameters": {
                    "rsi_period": self.parameters["rsi_period"],
                    "current_rsi": current_rsi
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 - self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 + self.parameters["take_profit"])
                }
            }
            signals.append(signal)
            
        elif rsi_status == "overbought":
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",
                "action": "SELL",
                "price": current_price,
                "quantity": position_size,
                "reason": f"RSI超买: {current_rsi:.1f} > {self.parameters['overbought_threshold']}",
                "confidence": min((current_rsi - self.parameters['overbought_threshold']) / 30, 0.95),
                "strategy": self.name,
                "parameters": {
                    "rsi_period": self.parameters["rsi_period"],
                    "current_rsi": current_rsi
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 + self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 - self.parameters["take_profit"])
                }
            }
            signals.append(signal)
        
        logger.info(f"生成 {len(signals)} 个RSI交易信号")
        return signals
    
    def calculate_risk(self, signals: List[Dict], portfolio_value: float) -> Dict[str, float]:
        """
        计算交易风险
        
        Args:
            signals: 交易信号列表
            portfolio_value: 投资组合价值
            
        Returns:
            风险指标字典
        """
        if not signals:
            return {
                "total_risk": 0.0,
                "position_risk": 0.0,
                "market_risk": 0.2,  # 默认市场风险
                "signal_quality": 0.0
            }
        
        # 计算信号质量 (基于置信度)
        avg_confidence = np.mean([signal.get("confidence", 0) for signal in signals])
        signal_quality = avg_confidence
        
        # 计算仓位风险
        total_position = sum(signal.get("quantity", 0) for signal in signals)
        position_risk = min(total_position / 0.3, 1.0)  # 最大仓位30%
        
        # 总风险计算
        total_risk = position_risk * 0.4 + 0.2 * 0.4 + (1 - signal_quality) * 0.2
        
        risk_metrics = {
            "total_risk": float(total_risk),
            "position_risk": float(position_risk),
            "market_risk": 0.2,
            "signal_quality": float(signal_quality),
            "avg_confidence": float(avg_confidence),
            "total_position": float(total_position)
        }
        
        return risk_metrics

# 注册策略到工厂
from .ai_strategy_base import StrategyFactory
StrategyFactory.register_strategy("rsi", RSIStrategy)
'''
        
        templates["rsi"] = rsi_template
        
        # 布林带策略模板
        bollinger_template = '''#!/usr/bin/env python3
"""
布林带策略
基于布林带指标的交易策略
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime

from .ai_strategy_base import AIStrategyBase

logger = logging.getLogger(__name__)

class BollingerBandsStrategy(AIStrategyBase):
    """
    布林带策略
    
    基于布林带指标生成交易信号。
    价格触及下轨为买入信号，触及上轨为卖出信号。
    """
    
    def __init__(self):
        """初始化布林带策略"""
        super().__init__(
            name="布林带策略",
            version="1.0.0"
        )
        
        # 默认参数
        self.default_params = {
            "period": 20,           # 移动平均线周期
            "std_dev": 2,           # 标准差倍数
            "position_size": 0.1,   # 仓位大小
            "stop_loss": 0.05,      # 止损比例
            "take_profit": 0.10,    # 止盈比例
            "band_width_threshold": 0.1  # 带宽阈值
        }
    
    def _on_initialize(self):
        """策略初始化逻辑"""
        logger.info(f"布林带策略初始化，参数: {self.parameters}")
        
        # 确保所有必要参数都有值
        for key, default_value in self.default_params.items():
            if key not in self.parameters:
                self.parameters[key] = default_value
        
        logger.info("布林带策略初始化完成")
    
    def _calculate_bollinger_bands(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算布林带
        
        Args:
            data: 价格数据
            
        Returns:
            布林带字典
        """
        close_prices = data["close"]
        period = self.parameters["period"]
        std_dev = self.parameters["std_dev"]
        
        # 计算移动平均线
        middle_band = close_prices.rolling(window=period).mean()
        
        # 计算标准差
        std = close_prices.rolling(window=period).std()
        
        # 计算上下轨
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        # 计算带宽
        band_width = (upper_band - lower_band) / middle_band
        
        return {
            "upper_band": upper_band,
            "middle_band": middle_band,
            "lower_band": lower_band,
            "band_width": band_width
        }
    
    async def analyze_market(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场数据
        
        Args:
            data: 市场数据
            
        Returns:
            市场分析结果
        """
        logger.info("开始布林带市场分析...")
        
        # 计算布林带
        bands = self._calculate_bollinger_bands(data)
        
        current_price = data["close"].iloc[-1]
        upper_band = bands["upper_band"].iloc[-1]
        middle_band = bands["middle_band"].iloc[-1]
        lower_band = bands["lower_band"].iloc[-1]
        band_width = bands["band_width"].iloc[-1]
        
        # 判断价格位置
        if pd.isna(upper_band) or pd.isna(lower_band):
            band_position = "unknown"
        elif current_price <= lower_band:
            band_position = "at_lower_band"
        elif current_price >= upper_band:
            band_position = "at_upper_band"
        elif current_price > middle_band:
            band_position = "above_middle"
        else:
            band_position = "below_middle"
        
        # 判断波动率
        volatility_status = "high" if band_width > self.parameters["band_width_threshold"] else "low"
        
        analysis_result = {
            "current_price": float(current_price),
            "upper_band": float(upper_band) if not pd.isna(upper_band) else None,
            "middle_band": float(middle_band) if not pd.isna(middle_band) else None,
            "lower_band": float(lower_band) if not pd.isna(lower_band) else None,
            "band_width": float(band_width) if not pd.isna(band_width) else None,
            "band_position": band_position,
            "volatility_status": volatility_status,
            "analysis_time": datetime.now().isoformat(),
            "data_points": len(data)
        }
        
        logger.info(f"布林带分析完成，位置: {band_position}, 波动率: {volatility_status}")
        return analysis_result
    
    async def generate_signals(self, analysis_result: Dict[str, Any]) -> List[Dict]:
        """
        生成交易信号
        
        Args:
            analysis_result:
            analysis_result: 市场分析结果
            
        Returns:
            交易信号列表
        """
        signals = []
        
        band_position = analysis_result.get("band_position")
        current_price = analysis_result.get("current_price")
        lower_band = analysis_result.get("lower_band")
        upper_band = analysis_result.get("upper_band")
        
        if band_position == "unknown" or current_price <= 0:
            return signals
        
        position_size = self.parameters["position_size"]
        
        # 生成信号
        if band_position == "at_lower_band" and lower_band is not None:
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",
                "action": "BUY",
                "price": current_price,
                "quantity": position_size,
                "reason": f"价格触及布林带下轨: {current_price:.2f} ≤ {lower_band:.2f}",
                "confidence": 0.7,
                "strategy": self.name,
                "parameters": {
                    "period": self.parameters["period"],
                    "std_dev": self.parameters["std_dev"],
                    "band_width": analysis_result.get("band_width")
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 - self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 + self.parameters["take_profit"])
                }
            }
            signals.append(signal)
            
        elif band_position == "at_upper_band" and upper_band is not None:
            signal = {
                "timestamp": datetime.now().isoformat(),
                "symbol": "EXAMPLE",
                "action": "SELL",
                "price": current_price,
                "quantity": position_size,
                "reason": f"价格触及布林带上轨: {current_price:.2f} ≥ {upper_band:.2f}",
                "confidence": 0.7,
                "strategy": self.name,
                "parameters": {
                    "period": self.parameters["period"],
                    "std_dev": self.parameters["std_dev"],
                    "band_width": analysis_result.get("band_width")
                },
                "risk_metrics": {
                    "stop_loss": current_price * (1 + self.parameters["stop_loss"]),
                    "take_profit": current_price * (1 - self.parameters["take_profit"])
                }
            }
            signals.append(signal)
        
        logger.info(f"生成 {len(signals)} 个布林带交易信号")
        return signals
    
    def calculate_risk(self, signals: List[Dict], portfolio_value: float) -> Dict[str, float]:
        """
        计算交易风险
        
        Args:
            signals: 交易信号列表
            portfolio_value: 投资组合价值
            
        Returns:
            风险指标字典
        """
        if not signals:
            return {
                "total_risk": 0.0,
                "position_risk": 0.0,
                "market_risk": 0.2,
                "signal_quality": 0.0
            }
        
        # 计算信号质量
        avg_confidence = np.mean([signal.get("confidence", 0) for signal in signals])
        signal_quality = avg_confidence
        
        # 计算仓位风险
        total_position = sum(signal.get("quantity", 0) for signal in signals)
        position_risk = min(total_position / 0.3, 1.0)
        
        # 根据波动率调整市场风险
        market_risk = 0.3 if analysis_result.get("volatility_status") == "high" else 0.2
        
        # 总风险计算
        total_risk = position_risk * 0.4 + market_risk * 0.4 + (1 - signal_quality) * 0.2
        
        risk_metrics = {
            "total_risk": float(total_risk),
            "position_risk": float(position_risk),
            "market_risk": float(market_risk),
            "signal_quality": float(signal_quality),
            "avg_confidence": float(avg_confidence),
            "total_position": float(total_position)
        }
        
        return risk_metrics

# 注册策略到工厂
from .ai_strategy_base import StrategyFactory
StrategyFactory.register_strategy("bollinger", BollingerBandsStrategy)
'''
        
        templates["bollinger"] = bollinger_template
        
        return templates
    
    def create_strategy(self, 
                       strategy_type: str,
                       strategy_name: str,
                       strategy_description: str,
                       custom_params: Dict = None) -> str:
        """
        创建新策略
        
        Args:
            strategy_type: 策略类型 (base, rsi, bollinger, 或自定义)
            strategy_name: 策略名称
            strategy_description: 策略描述
            custom_params: 自定义参数
            
        Returns:
            生成的文件路径
        """
        # 确定类名
        class_name = strategy_name.replace(" ", "").replace("-", "") + "Strategy"
        
        # 获取模板
        if strategy_type in self.strategy_templates:
            template = self.strategy_templates[strategy_type]
        else:
            template = self.strategy_templates["base"]
        
        # 准备模板参数
        template_params = {
            "strategy_name": strategy_name,
            "class_name": class_name,
            "strategy_description": strategy_description,
            "version": "1.0.0",
            "default_params": custom_params or {},
            "strategy_key": strategy_name.lower().replace(" ", "_"),
            "analysis_instructions": f"实现{strategy_name}的市场分析逻辑",
            "signal_generation_instructions": f"实现{strategy_name}的信号生成逻辑",
            "risk_calculation_instructions": f"实现{strategy_name}的风险计算逻辑"
        }
        
        # 渲染模板
        strategy_code = template.format(**template_params)
        
        # 生成文件名
        filename = f"{strategy_name.lower().replace(' ', '_')}_strategy.py"
        filepath = os.path.join(self.strategies_dir, filename)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(strategy_code)
        
        logger.info(f"策略创建完成: {filepath}")
        return filepath
    
    def create_rsi_strategy(self, custom_params: Dict = None) -> str:
        """创建RSI策略"""
        return self.create_strategy(
            strategy_type="rsi",
            strategy_name="RSI策略",
            strategy_description="基于相对强弱指数(RSI)的交易策略",
            custom_params=custom_params
        )
    
    def create_bollinger_strategy(self, custom_params: Dict = None) -> str:
        """创建布林带策略"""
        return self.create_strategy(
            strategy_type="bollinger",
            strategy_name="布林带策略",
            strategy_description="基于布林带指标的交易策略",
            custom_params=custom_params
        )
    
    def create_custom_strategy(self,
                              strategy_name: str,
                              strategy_description: str,
                              default_params: Dict,
                              analysis_logic: str = "",
                              signal_logic: str = "",
                              risk_logic: str = "") -> str:
        """创建自定义策略"""
        # 创建自定义模板
        custom_template = self.strategy_templates["base"]
        
        # 准备模板参数
        template_params = {
            "strategy_name": strategy_name,
            "class_name": strategy_name.replace(" ", "").replace("-", "") + "Strategy",
            "strategy_description": strategy_description,
            "version": "1.0.0",
            "default_params": default_params,
            "strategy_key": strategy_name.lower().replace(" ", "_"),
            "analysis_instructions": analysis_logic or f"实现{strategy_name}的市场分析逻辑",
            "signal_generation_instructions": signal_logic or f"实现{strategy_name}的信号生成逻辑",
            "risk_calculation_instructions": risk_logic or f"实现{strategy_name}的风险计算逻辑"
        }
        
        # 渲染模板
        strategy_code = custom_template.format(**template_params)
        
        # 生成文件名
        filename = f"{strategy_name.lower().replace(' ', '_')}_strategy.py"
        filepath = os.path.join(self.strategies_dir, filename)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(strategy_code)
        
        logger.info(f"自定义策略创建完成: {filepath}")
        return filepath
    
    def list_strategies(self) -> List[str]:
        """列出所有策略文件"""
        if not os.path.exists(self.strategies_dir):
            return []
        
        strategies = []
        for filename in os.listdir(self.strategies_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                strategies.append(filename)
        
        return sorted(strategies)
    
    def generate_strategy_report(self) -> Dict[str, Any]:
        """生成策略报告"""
        strategies = self.list_strategies()
        
        report = {
            "report_time": datetime.now().isoformat(),
            "strategies_dir": self.strategies_dir,
            "total_strategies": len(strategies),
            "strategies": strategies,
            "templates_available": list(self.strategy_templates.keys()),
            "recommendations": self._generate_strategy_recommendations(strategies)
        }
        
        return report
    
    def _generate_strategy_recommendations(self, strategies: List[str]) -> List[str]:
        """生成策略开发建议"""
        recommendations = []
        
        strategy_count = len(strategies)
        
        if strategy_count == 0:
            recommendations.append("🚨 没有找到任何策略，建议创建基础策略")
        elif strategy_count < 3:
            recommendations.append(f"📈 当前有 {strategy_count} 个策略，建议创建更多策略以丰富策略库")
        
        # 检查策略类型
        strategy_types = set()
        for filename in strategies:
            if "rsi" in filename.lower():
                strategy_types.add("RSI")
            elif "bollinger" in filename.lower() or "bb" in filename.lower():
                strategy_types.add("Bollinger")
            elif "ma" in filename.lower() or "moving" in filename.lower():
                strategy_types.add("Moving Average")
            elif "macd" in filename.lower():
                strategy_types.add("MACD")
        
        missing_types = []
        for required_type in ["RSI", "Bollinger", "Moving Average", "MACD"]:
            if required_type not in strategy_types:
                missing_types.append(required_type)
        
        if missing_types:
            recommendations.append(f"🔧 缺少以下策略类型: {', '.join(missing_types)}，建议补充")
        
        if not recommendations:
            recommendations.append("✅ 策略库状态良好，建议继续优化现有策略")
        
        return recommendations

# 使用示例
def example_usage():
    """使用示例"""
    print("AI策略开发自动化示例")
    
    # 创建自动化模块
    automation = AIStrategyAutomation()
    
    # 创建RSI策略
    rsi_file = automation.create_rsi_strategy({
        "rsi_period": 14,
        "oversold_threshold": 30,
        "overbought_threshold": 70
    })
    print(f"✅ 创建RSI策略: {rsi_file}")
    
    # 创建布林带策略
    bollinger_file = automation.create_bollinger_strategy({
        "period": 20,
        "std_dev": 2,
        "band_width_threshold": 0.1
    })
    print(f"✅ 创建布林带策略: {bollinger_file}")
    
    # 创建自定义策略
    custom_file = automation.create_custom_strategy(
        strategy_name="动量策略",
        strategy_description="基于价格动量的交易策略",
        default_params={
            "momentum_period": 10,
            "threshold": 0.02,
            "position_size": 0.1
        },
        analysis_logic="计算价格动量指标",
        signal_logic="动量超过阈值时生成交易信号",
        risk_logic="根据动量强度和波动率计算风险"
    )
    print(f"✅ 创建自定义策略: {custom_file}")
    
    # 生成策略报告
    report = automation.generate_strategy_report()
    print(f"\n策略报告:")
    print(f"  总策略数: {report['total_strategies']}")
    print(f"  可用模板: {', '.join(report['templates_available'])}")
    
    print(f"\n优化建议:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    # 列出所有策略
    strategies = automation.list_strategies()
    print(f"\n所有策略文件:")
    for strategy in strategies:
        print(f"  • {strategy}")

if __name__ == "__main__":
    example_usage()
