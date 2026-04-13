#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器学习趋势预测器
基于历史价格数据预测股票趋势
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrendPrediction:
    """趋势预测结果"""
    symbol: str
    prediction: float  # 预测变化率，正数表示上涨，负数表示下跌
    confidence: float  # 置信度 0-1
    features_used: List[str]
    prediction_time: datetime
    horizon_days: int = 5  # 预测时间范围（天）
    model_type: str = "random_forest"
    
    def get_action(self) -> str:
        """根据预测结果获取操作建议"""
        if self.prediction > 0.05 and self.confidence > 0.7:
            return "强烈买入"
        elif self.prediction > 0.02 and self.confidence > 0.6:
            return "买入"
        elif self.prediction < -0.05 and self.confidence > 0.7:
            return "强烈卖出"
        elif self.prediction < -0.02 and self.confidence > 0.6:
            return "卖出"
        else:
            return "持有"
    
    def get_risk_level(self) -> str:
        """获取风险等级"""
        if self.confidence > 0.8:
            return "低风险"
        elif self.confidence > 0.6:
            return "中风险"
        else:
            return "高风险"

class MLTrendPredictor:
    """机器学习趋势预测器"""
    
    def __init__(self, model_type: str = "random_forest", config: Optional[Dict] = None):
        self.model_type = model_type
        self.config = config or {
            "n_estimators": 100,
            "max_depth": 10,
            "random_state": 42
        }
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.trained = False
        self.training_metrics = {}
        self.last_training_time = None
        
    def extract_features(self, historical_data: pd.DataFrame) -> Dict[str, float]:
        """从历史数据中提取特征"""
        features = {}
        
        if len(historical_data) < 20:
            logger.warning("历史数据不足，无法提取特征")
            return features
        
        # 价格特征
        prices = historical_data['close'].values
        features['price_mean'] = np.mean(prices[-20:])
        features['price_std'] = np.std(prices[-20:])
        features['price_trend'] = (prices[-1] - prices[-20]) / prices[-20]
        
        # 技术指标特征
        if 'volume' in historical_data.columns:
            volumes = historical_data['volume'].values
            features['volume_mean'] = np.mean(volumes[-20:])
            features['volume_trend'] = (volumes[-1] - volumes[-20]) / (volumes[-20] + 1e-10)
        
        # 波动率特征
        returns = np.diff(prices) / prices[:-1]
        features['volatility'] = np.std(returns[-20:]) if len(returns) >= 20 else 0
        
        # 动量特征
        if len(prices) >= 10:
            features['momentum_5'] = (prices[-1] - prices[-5]) / prices[-5]
            features['momentum_10'] = (prices[-1] - prices[-10]) / prices[-10]
        
        return features
    
    def train(self, training_data: Dict[str, pd.DataFrame]):
        """训练模型"""
        logger.info(f"开始训练 {self.model_type} 模型...")
        
        # 提取特征和标签
        X = []
        y = []
        
        for symbol, data in training_data.items():
            if len(data) < 50:
                continue
                
            features = self.extract_features(data.iloc[:-5])  # 用前N-5天数据
            if not features:
                continue
                
            # 计算未来5天的收益率作为标签
            future_return = (data['close'].iloc[-1] - data['close'].iloc[-5]) / data['close'].iloc[-5]
            
            X.append(list(features.values()))
            y.append(future_return)
        
        if len(X) < 10:
            logger.warning("训练数据不足")
            return False
        
        # 保存特征名称
        self.feature_names = list(next(iter(training_data.values())).keys()) if training_data else []
        
        # 这里应该是真正的模型训练代码
        # 暂时使用模拟训练
        logger.info(f"模拟训练完成，样本数: {len(X)}")
        self.trained = True
        self.last_training_time = datetime.now()
        self.training_metrics = {
            "samples": len(X),
            "features": len(self.feature_names),
            "training_time": self.last_training_time
        }
        
        return True
    
    async def predict(self, feature_data: Dict[str, float], symbol: str) -> TrendPrediction:
        """预测单个股票"""
        if not self.trained:
            logger.warning("模型未训练，使用随机预测")
            return self._random_prediction(symbol)
        
        try:
            # 这里应该是真正的模型预测
            # 暂时使用基于特征的简单逻辑
            prediction = 0.0
            confidence = 0.7
            
            if 'price_trend' in feature_data:
                prediction = feature_data['price_trend'] * 0.5
            
            return TrendPrediction(
                symbol=symbol,
                prediction=prediction,
                confidence=confidence,
                features_used=list(feature_data.keys()),
                prediction_time=datetime.now(),
                horizon_days=5,
                model_type=self.model_type
            )
        except Exception as e:
            logger.error(f"预测失败: {e}")
            return self._random_prediction(symbol)
    
    async def batch_predict(self, symbols: List[str], feature_data: Dict[str, Dict[str, float]]) -> List[TrendPrediction]:
        """批量预测多个股票"""
        tasks = []
        for symbol in symbols:
            if symbol in feature_data:
                tasks.append(self.predict(feature_data[symbol], symbol))
            else:
                logger.warning(f"⚠️  {symbol} 的特征数据缺失")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, TrendPrediction):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"❌ 预测 {symbols[i]} 异常: {result}")
                # 创建失败结果
                valid_results.append(TrendPrediction(
                    symbol=symbols[i],
                    prediction=0.0,
                    confidence=0.0,
                    features_used=[],
                    prediction_time=datetime.now(),
                    horizon_days=5,
                    model_type=self.model_type
                ))
        
        success_count = sum(1 for r in valid_results if r.confidence > 0)
        logger.info(f"✅ 批量预测完成，成功: {success_count}/{len(symbols)}")
        
        return valid_results
    
    def _random_prediction(self, symbol: str) -> TrendPrediction:
        """随机预测（用于测试）"""
        import random
        return TrendPrediction(
            symbol=symbol,
            prediction=random.uniform(-0.1, 0.1),
            confidence=random.uniform(0.5, 0.9),
            features_used=["random"],
            prediction_time=datetime.now(),
            horizon_days=5,
            model_type="random"
        )
    
    def get_training_metrics(self) -> Dict[str, Any]:
        """获取训练指标"""
        return self.training_metrics
    
    def save_model(self, filepath: str):
        """保存模型"""
        if not self.trained:
            logger.warning("⚠️ 模型未训练，无法保存")
            return
        
        import joblib
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'model_type': self.model_type,
                'config': self.config,
                'training_metrics': self.training_metrics,
                'last_training_time': self.last_training_time
            }
            joblib.dump(model_data, filepath)
            logger.info(f"💾 模型已保存到: {filepath}")
        except Exception as e:
            logger.error(f"❌ 保存模型失败: {e}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        import joblib
        try:
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.model_type = model_data['model_type']
            self.config = model_data['config']
            self.training_metrics = model_data['training_metrics']
            self.last_training_time = model_data['last_training_time']
            self.trained = True
            logger.info(f"📂 模型已从 {filepath} 加载")
        except Exception as e:
            logger.error(f"❌ 加载模型失败: {e}")

# 示例使用
async def example_usage():
    """示例用法"""
    print("🚀 ML趋势预测策略示例")
    print("=" * 50)
    
    # 创建预测器
    predictor = MLTrendPredictor(model_type="random_forest")
    
    # 模拟历史数据
    print("生成模拟历史数据...")
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=200, freq='D')
    
    # 创建有趋势的模拟数据
    trend = np.linspace(0, 0.5, 200)  # 上升趋势
    noise = np.random.randn(200) * 0.02
    prices = 100 * (1 + trend + noise.cumsum() / 100)
    
    historical_data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(200) * 0.01),
        'high': prices * (1 + np.random.rand(200) * 0.03),
        'low': prices * (1 - np.random.rand(200) * 0.03),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 200)
    }, index=dates)
    
    # 训练模型
    training_data = {"TEST_STOCK": historical_data}
    predictor.train(training_data)
    
    # 提取特征
    print("提取特征...")
    features = predictor.extract_features(historical_data)
    
    # 单个预测
    print("进行单个预测...")
    prediction = await predictor.predict(features, "TEST_STOCK")
    
    print(f"\n📈 预测结果:")
    print(f"股票: {prediction.symbol}")
    print(f"预测变化: {prediction.prediction:+.2%}")
    print(f"置信度: {prediction.confidence:.2%}")
    print(f"操作建议: {prediction.get_action()}")
    print(f"风险等级: {prediction.get_risk_level()}")
    
    # 批量预测
    print("\n进行批量预测...")
    symbols = ["STOCK_A", "STOCK_B", "STOCK_C", "STOCK_D"]
    
    # 为每个股票生成稍微不同的特征
    feature_data = {}
    for i, symbol in enumerate(symbols):
        symbol_features = features.copy()
        # 添加一些随机变化
        for key in symbol_features:
            if np.random.random() > 0.7:
                symbol_features[key] *= np.random.uniform(0.9, 1.1)
        feature_data[symbol] = symbol_features
    
    batch_results = await predictor.batch_predict(symbols, feature_data)
    
    print("\n📊 批量预测结果:")
    print("=" * 60)
    print(f"{'股票':<8} {'操作':<12} {'预测变化':<12} {'置信度':<12} {'风险等级':<10}")
    print("-" * 60)
    
    for result in batch_results:
        print(f"{result.symbol:<8} {result.get_action():<12} {result.prediction:+.2%} {'':<4} {result.confidence:.2%} {'':<4} {result.get_risk_level():<10}")
    
    print("=" * 60)
    
    # 保存模型
    predictor.save_model("/tmp/ml_trend_predictor_model.joblib")
    
    print("\n✅ 示例完成！")

if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())