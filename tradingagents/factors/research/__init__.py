# -*- coding: utf-8 -*-
"""
TradingAgents-CN - Factor Research Tools
因子研究工具模块

包含：
- IC/IR 分析
- 因子相关性分析
- 多因子组合优化
- LLM 辅助因子挖掘
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict

from ..base import BaseFactor, FactorCategory, FactorRegistry, get_registry


class FactorResearcher:
    """
    因子研究者 - 负责因子分析、组合优化和因子挖掘
    """
    
    def __init__(self):
        self.registry = get_registry()
        self._factor_cache = {}
    
    # ============== IC/IR 分析 ==============
    
    def calculate_ic(self, factor_data: pd.Series, returns: pd.Series, 
                     method: str = 'spearman') -> pd.DataFrame:
        """
        计算 IC (Information Coefficient) 时间序列
        
        参数:
            factor_data: 因子值序列 (index: ts_code, columns: date)
            returns: 收益率序列
            method: 'spearman' or 'pearson'
        
        返回:
            IC 统计 DataFrame
        """
        from scipy import stats
        
        ic_series = []
        for date in factor_data.columns:
            factor_col = factor_data[date].dropna()
            returns_col = returns[date].dropna()
            
            common = factor_col.index.intersection(returns_col.index)
            if len(common) < 10:
                continue
            
            if method == 'spearman':
                ic, _ = stats.spearmanr(factor_col.loc[common], returns_col.loc[common])
            else:
                ic, _ = stats.pearsonr(factor_col.loc[common], returns_col.loc[common])
            
            ic_series.append({'date': date, 'ic': ic})
        
        ic_df = pd.DataFrame(ic_series).set_index('date')
        
        return pd.DataFrame({
            'IC_Mean': ic_df['ic'].mean(),
            'IC_Std': ic_df['ic'].std(),
            'IC_IR': ic_df['ic'].mean() / ic_df['ic'].std() if ic_df['ic'].std() > 0 else 0,
            'IC_Positive_Ratio': (ic_df['ic'] > 0).mean(),
            'IC_T_Stat': ic_df['ic'].mean() / (ic_df['ic'].std() / np.sqrt(len(ic_df))) if len(ic_df) > 1 else 0,
        }).T
    
    def batch_ic_analysis(self, factors: List[str], 
                          returns: pd.DataFrame) -> pd.DataFrame:
        """
        批量因子 IC 分析
        """
        results = []
        for factor_name in factors:
            factor_data = self.get_factor_data(factor_name)
            if factor_data is None:
                continue
            
            ic_result = self.calculate_ic(factor_data, returns)
            ic_result['factor'] = factor_name
            results.append(ic_result)
        
        return pd.concat(results).reset_index(drop=True)
    
    # ============== 因子相关性分析 ==============
    
    def calculate_correlation(self, factor1: str, factor2: str,
                             data: Optional[pd.DataFrame] = None) -> float:
        """
        计算两个因子的相关性
        """
        f1_data = self.get_factor_data(factor1)
        f2_data = self.get_factor_data(factor2)
        
        if f1_data is None or f2_data is None:
            return 0.0
        
        # 取最新截面数据
        f1_latest = f1_data.iloc[:, -1].dropna()
        f2_latest = f2_data.iloc[:, -1].dropna()
        
        common = f1_latest.index.intersection(f2_latest.index)
        if len(common) < 10:
            return 0.0
        
        return f1_latest.loc[common].corr(f2_latest.loc[common])
    
    def correlation_matrix(self, factors: List[str]) -> pd.DataFrame:
        """
        计算因子相关性矩阵
        """
        n = len(factors)
        corr_matrix = np.zeros((n, n))
        
        for i, f1 in enumerate(factors):
            for j, f2 in enumerate(factors):
                if i == j:
                    corr_matrix[i, j] = 1.0
                else:
                    corr_matrix[i, j] = self.calculate_correlation(f1, f2)
        
        return pd.DataFrame(corr_matrix, index=factors, columns=factors)
    
    def find_high_correlation_pairs(self, factors: List[str],
                                    threshold: float = 0.8) -> List[Tuple[str, str, float]]:
        """
        找出高相关性因子对
        """
        pairs = []
        corr = self.correlation_matrix(factors)
        
        for i, f1 in enumerate(factors):
            for j, f2 in enumerate(factors):
                if i < j:
                    c = corr.loc[f1, f2]
                    if abs(c) > threshold:
                        pairs.append((f1, f2, c))
        
        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)
    
    # ============== 多因子组合优化 ==============
    
    def optimize_portfolio(self, factors: List[str], 
                          returns: pd.DataFrame,
                          method: str = 'equal_weight',
                          constraints: Optional[Dict] = None) -> Dict:
        """
        多因子组合优化
        
        方法:
        - equal_weight: 等权
        - ic_weight: 按 IC 权重
        - risk_parity: 风险平价
        - mean_variance: 均值方差
        """
        if method == 'equal_weight':
            weights = {f: 1.0 / len(factors) for f in factors}
        
        elif method == 'ic_weight':
            ic_results = self.batch_ic_analysis(factors, returns)
            ic_scores = ic_results.set_index('factor')['IC_Mean'].fillna(0)
            # 归一化
            total = ic_scores.abs().sum()
            weights = {f: abs(ic_scores.get(f, 0)) / total for f in factors}
        
        elif method == 'risk_parity':
            # 简化：按因子波动率倒数作为权重
            vols = {}
            for f in factors:
                data = self.get_factor_data(f)
                if data is not None:
                    vols[f] = data.iloc[:, -1].std()
                else:
                    vols[f] = 1.0
            
            total = sum(1.0 / v for v in vols.values())
            weights = {f: (1.0 / vols[f]) / total for f in factors}
        
        else:
            weights = {f: 1.0 / len(factors) for f in factors}
        
        return {
            'weights': weights,
            'method': method,
            'factor_count': len(factors),
        }
    
    def orthogonalize_factors(self, factors: List[str],
                              data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        正交化因子 (施密特正交)
        """
        if data is None:
            # 收集因子数据
            factor_data = []
            for f in factors:
                fd = self.get_factor_data(f)
                if fd is not None:
                    factor_data.append(fd.iloc[:, -1])
            
            if not factor_data:
                return pd.DataFrame()
            
            X = pd.concat(factor_data, axis=1).dropna()
        else:
            X = data[factors].dropna()
        
        # 施密特正交
        n = len(factors)
        orthogonal = pd.DataFrame(index=X.index)
        
        for i in range(n):
            col = X.iloc[:, i].copy()
            
            for j in range(i):
                proj = orthogonal.iloc[:, j]
                col = col - proj * (col.dot(proj) / proj.dot(proj))
            
            orthogonal[factors[i]] = col
        
        return orthogonal
    
    # ============== LLM 辅助因子挖掘 ==============
    
    def suggest_factors_from_llm(self, idea: str, llm_client=None) -> List[Dict]:
        """
        利用 LLM 建议新因子
        
        参数:
            idea: 投资想法描述
            llm_client: LLM 客户端 (可选)
        
        返回:
            因子建议列表
        """
        # 如果有 LLM 客户端，使用它
        if llm_client is not None:
            prompt = f"""
基于以下投资想法，生成 5 个可计算的因子建议：

投资想法: {idea}

要求:
1. 每个因子需要说明计算逻辑
2. 因子应该可以数据验证
3. 说明因子的预期作用

请以 JSON 格式返回:
[
  {{"name": "因子名", "category": "类别", "logic": "计算逻辑", "expected": "预期作用"}}
]
"""
            # 调用 LLM (这里需要实现实际的 LLM 调用)
            # response = llm_client.chat(prompt)
            # return parse_json(response)
            pass
        
        # 默认返回一些通用建议
        return [
            {
                "name": f"{idea}_Momentum",
                "category": "MOMENTUM",
                "logic": f"基于{idea}的动量因子",
                "expected": "捕捉趋势延续性"
            },
            {
                "name": f"{idea}_Reversal", 
                "category": "MOMENTUM",
                "logic": f"基于{idea}的反转因子",
                "expected": "捕捉均值回归"
            },
        ]
    
    # ============== 因子数据管理 ==============
    
    def get_factor_data(self, factor_name: str) -> Optional[pd.DataFrame]:
        """获取因子数据"""
        if factor_name in self._factor_cache:
            return self._factor_cache[factor_name]
        
        # 从注册表获取因子类并计算
        factor_cls = self.registry.get(factor_name)
        if factor_cls is None:
            return None
        
        # 实际使用时，这里应该从数据源获取
        # 这里返回 None 表示需要外部数据源
        return None
    
    def set_factor_data(self, factor_name: str, data: pd.DataFrame):
        """设置因子数据缓存"""
        self._factor_cache[factor_name] = data
    
    def list_available_factors(self, category: Optional[FactorCategory] = None) -> List[str]:
        """列出可用因子"""
        return self.registry.list_factors(category)


# 便捷函数
def create_researcher() -> FactorResearcher:
    """创建因子研究者"""
    return FactorResearcher()


__all__ = [
    "FactorResearcher",
    "create_researcher",
]