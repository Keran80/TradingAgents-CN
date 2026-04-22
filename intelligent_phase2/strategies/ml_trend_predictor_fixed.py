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

class MLTrendPredictor:
    """机器学习趋势预测器"""
    
    def __init__(self, model_type: str = "random_forest"):
        """
        初始化预测器
        
        Args:
            model_type: 模型类型，支持 "random_forest", "xgboost", "lightgbm"
        """
        self.model_type = model_type
        self.model = None
        self.feature_columns = []
        self.is_trained = False
        
    async def train(self, historical_data: pd.DataFrame, target_column: str = "return_5d"):
        """
        训练模型
        
        Args:
            historical_data: 历史数据，包含特征和目标列
            target_column: 目标列名
        """
        logger.info(f"开始训练 {self.model_type} 模型")
        
        # 准备特征和目标
        feature_cols = [col for col in historical_data.columns if col != target_column]
        self.feature_columns = feature_cols
        
        X = historical_data[feature_cols].values
        y = historical_data[target_column].values
        
        # 根据模型类型选择算法
        if self.model_type == "random_forest":
            from sklearn.ensemble import RandomForestRegressor
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif self.model_type == "xgboost":
            from xgboost import XGBRegressor
            self.model = XGBRegressor(n_estimators=100, random_state=42)
        elif self.model_type == "lightgbm":
            from lightgbm import LGBMRegressor
            self.model = LGBMRegressor(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        # 训练模型
        self.model.fit(X, y)
        self.is_trained = True
        
        logger.info(f"{self.model_type} 模型训练完成")
        return self
    
    async def predict(self, features: pd.DataFrame) -> TrendPrediction:
        """
        预测趋势
        
        Args:
            features: 特征数据
            
        Returns:
            TrendPrediction: 预测结果
        """
        if not self.is_trained:
            raise ValueError("模型未训练，请先调用 train() 方法")
        
        # 确保特征列匹配
        missing_cols = set(self.feature_columns) - set(features.columns)
        if missing_cols:
            raise ValueError(f"缺少特征列: {missing_cols}")
        
        X = features[self.feature_columns].values
        
        # 进行预测
        prediction = float(self.model.predict(X)[0])
        
        # 计算置信度（使用模型的不确定性估计）
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(X)[0]
            confidence = float(max(proba))
        else:
            # 对于回归模型，使用预测值的标准化
            confidence = 0.7  # 默认置信度
        
        result = TrendPrediction(
            symbol=features.get('symbol', 'unknown')[0] if 'symbol' in features.columns else 'unknown',
            prediction=prediction,
            confidence=confidence,
            features_used=self.feature_columns,
            prediction_time=datetime.now(),
            horizon_days=5,
            model_type=self.model_type
        )
        
        return result
    
    async def predict_batch(self, features_list: List[pd.DataFrame]) -> List[TrendPrediction]:
        """
        批量预测
        
        Args:
            features_list: 特征数据列表
            
        Returns:
            List[TrendPrediction]: 预测结果列表
        """
        predictions = []
        for features in features_list:
            try:
                prediction = await self.predict(features)
                predictions.append(prediction)
            except Exception as e:
                logger.error(f"预测失败: {e}")
                continue
        
        return predictions
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        获取特征重要性
        
        Returns:
            Dict[str, float]: 特征重要性字典
        """
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            return dict(zip(self.feature_columns, importances))
        else:
            logger.warning(f"{self.model_type} 模型不支持特征重要性")
            return {col: 0.0 for col in self.feature_columns}
    
    def save_model(self, filepath: str):
        """
        保存模型
        
        Args:
            filepath: 模型文件路径
        """
        import joblib
        joblib.dump({
            'model': self.model,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type,
            'is_trained': self.is_trained
        }, filepath)
        logger.info(f"模型已保存到 {filepath}")
    
    def load_model(self, filepath: str):
        """
        加载模型
        
        Args:
            filepath: 模型文件路径
        """
        import joblib
        data = joblib.load(filepath)
        self.model = data['model']
        self.feature_columns = data['feature_columns']
        self.model_type = data['model_type']
        self.is_trained = data['is_trained']
        logger.info(f"模型已从 {filepath} 加载")

# 示例使用
async def main():
    """示例主函数"""
    # 创建预测器
    predictor = MLTrendPredictor(model_type="random_forest")
    
    # 生成示例数据
    np.random.seed(42)
    n_samples = 1000
    historical_data = pd.DataFrame({
        'feature1': np.random.randn(n_samples),
        'feature2': np.random.randn(n_samples),
        'feature3': np.random.randn(n_samples),
        'return_5d': np.random.randn(n_samples) * 0.1  # 5天收益率
    })
    
    # 训练模型
    await predictor.train(historical_data)
    
    # 进行预测
    test_features = pd.DataFrame({
        'feature1': [0.5],
        'feature2': [-0.3],
        'feature3': [0.8]
    })
    
    prediction = await predictor.predict(test_features)
    print(f"预测结果: {prediction}")
    
    # 获取特征重要性
    importance = predictor.get_feature_importance()
    print(f"特征重要性: {importance}")

if __name__ == "__main__":
    asyncio.run(main())