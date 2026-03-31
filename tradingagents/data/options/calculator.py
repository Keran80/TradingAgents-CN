# -*- coding: utf-8 -*-
"""
期权计算器

提供期权定价和希腊字母计算：
- Black-Scholes 定价
- 希腊字母（Delta、Gamma、Vega、Theta、Rho）
- 隐含波动率计算
- 期权策略盈亏分析
"""

import logging
import math
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

# 使用 numpy 实现正态分布 CDF
def norm_cdf(x):
    """标准正态分布累积分布函数"""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def norm_pdf(x):
    """标准正态分布概率密度函数"""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

logger = logging.getLogger(__name__)


@dataclass
class OptionContract:
    """期权合约"""
    symbol: str
    underlying: str
    strike: float
    expiration: datetime
    option_type: str      # "call" 或 "put"
    exercise_type: str    # "european" 或 "american"
    premium: float = 0.0  # 权利金
    
    
@dataclass
class Greeks:
    """希腊字母"""
    delta: float    # 价格变化率
    gamma: float    # Delta变化率
    vega: float     # 波动率敏感度
    theta: float    # 时间衰减
    rho: float      # 利率敏感度
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "delta": self.delta,
            "gamma": self.gamma,
            "vega": self.vega,
            "theta": self.theta,
            "rho": self.rho,
        }


class OptionsCalculator:
    """
    期权计算器
    
    提供：
    - Black-Scholes 期权定价
    - 希腊字母计算
    - 隐含波动率计算
    - 期权组合分析
    """
    
    def calc_bs_price(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str,
    ) -> float:
        """
        Black-Scholes 期权定价
        
        Args:
            S: 标的资产价格
            K: 行权价
            T: 到期时间（年）
            r: 无风险利率
            sigma: 波动率
            option_type: "call" 或 "put"
            
        Returns:
            期权价格
        """
        if T <= 0:
            # 到期
            if option_type == "call":
                return max(S - K, 0)
            else:
                return max(K - S, 0)
                
        if sigma <= 0:
            sigma = 0.0001
            
        sqrt_T = math.sqrt(T)
        d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T
        
        if option_type == "call":
            price = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
        else:
            price = K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
            
        return price
        
    def calc_greeks(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str,
    ) -> Greeks:
        """
        计算希腊字母
        
        Args:
            S: 标的资产价格
            K: 行权价
            T: 到期时间（年）
            r: 无风险利率
            sigma: 波动率
            option_type: "call" 或 "put"
            
        Returns:
            Greeks 对象
        """
        if T <= 0 or sigma <= 0:
            return Greeks(delta=0, gamma=0, vega=0, theta=0, rho=0)
            
        sqrt_T = math.sqrt(T)
        d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T
        
        # Delta
        if option_type == "call":
            delta = norm_cdf(d1)
        else:
            delta = norm_cdf(d1) - 1
            
        # Gamma（看涨和看跌相同）
        gamma = norm_pdf(d1) / (S * sigma * sqrt_T)
        
        # Vega（看涨和看跌相同）
        vega = S * sqrt_T * norm_pdf(d1) / 100
        
        # Theta
        term1 = -S * norm_pdf(d1) * sigma / (2 * sqrt_T)
        if option_type == "call":
            theta = (term1 - r * K * math.exp(-r * T) * norm_cdf(d2)) / 365
        else:
            theta = (term1 + r * K * math.exp(-r * T) * norm_cdf(-d2)) / 365
            
        # Rho
        if option_type == "call":
            rho = K * T * math.exp(-r * T) * norm_cdf(d2) / 100
        else:
            rho = -K * T * math.exp(-r * T) * norm_cdf(-d2) / 100
            
        return Greeks(
            delta=delta,
            gamma=gamma,
            vega=vega,
            theta=theta,
            rho=rho,
        )
        
    def calc_implied_volatility(
        self,
        option_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str,
        tol: float = 1e-6,
        max_iter: int = 100,
    ) -> Optional[float]:
        """
        计算隐含波动率
        
        使用牛顿法迭代求解
        
        Args:
            option_price: 期权市场价格
            S: 标的资产价格
            K: 行权价
            T: 到期时间（年）
            r: 无风险利率
            option_type: "call" 或 "put"
            tol: 收敛容差
            max_iter: 最大迭代次数
            
        Returns:
            隐含波动率，失败返回 None
        """
        # 初始估计
        sigma = 0.3
        
        for _ in range(max_iter):
            try:
                price = self.calc_bs_price(S, K, T, r, sigma, option_type)
                greeks = self.calc_greeks(S, K, T, r, sigma, option_type)
                
                diff = price - option_price
                
                if abs(diff) < tol:
                    return sigma
                    
                # 牛顿法更新
                if greeks.vega != 0:
                    sigma = sigma - diff / greeks.vega * 100
                    
                sigma = max(0.01, min(sigma, 5.0))  # 限制范围
                
            except Exception:
                break
                
        # 尝试二分法
        return self._bisection_iv(
            option_price, S, K, T, r, option_type, tol
        )
        
    def _bisection_iv(
        self,
        option_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str,
        tol: float,
    ) -> Optional[float]:
        """二分法计算隐含波动率"""
        low, high = 0.001, 5.0
        
        for _ in range(100):
            mid = (low + high) / 2
            price = self.calc_bs_price(S, K, T, r, mid, option_type)
            
            if abs(price - option_price) < tol:
                return mid
                
            if price > option_price:
                high = mid
            else:
                low = mid
                
        return None
        
    def calc_portfolio_greeks(
        self,
        positions: List[Tuple[OptionContract, int]],
        S: float,
        T: float,
        r: float,
        sigma: float,
    ) -> Greeks:
        """
        计算期权组合的希腊字母
        
        Args:
            positions: [(合约, 数量), ...]，数量正数为买入，负数为卖出
            S: 标的资产价格
            T: 到期时间（年）
            r: 无风险利率
            sigma: 波动率
            
        Returns:
            组合希腊字母
        """
        total_delta = 0.0
        total_gamma = 0.0
        total_vega = 0.0
        total_theta = 0.0
        total_rho = 0.0
        
        for contract, quantity in positions:
            greeks = self.calc_greeks(
                S,
                contract.strike,
                T,
                r,
                sigma,
                contract.option_type,
            )
            
            multiplier = quantity  # 数量（正买入，负卖出）
            
            total_delta += greeks.delta * multiplier
            total_gamma += greeks.gamma * multiplier
            total_vega += greeks.vega * multiplier
            total_theta += greeks.theta * multiplier
            total_rho += greeks.rho * multiplier
            
        return Greeks(
            delta=total_delta,
            gamma=total_gamma,
            vega=total_vega,
            theta=total_theta,
            rho=total_rho,
        )
        
    def calc_strategy_pnl(
        self,
        strategy: List[Tuple[OptionContract, int, float]],
        S_final: float,
    ) -> float:
        """
        计算期权策略的盈亏
        
        Args:
            strategy: [(合约, 数量, 开仓价), ...]
            S_final: 到期标的价格
            
        Returns:
            总盈亏
        """
        total_pnl = 0.0
        
        for contract, quantity, entry_price in strategy:
            # 计算到期价值
            if contract.option_type == "call":
                payoff = max(S_final - contract.strike, 0)
            else:
                payoff = max(contract.strike - S_final, 0)
                
            # 盈亏 = 平仓价值 - 开仓成本
            pnl = (payoff - entry_price) * quantity
            total_pnl += pnl
            
        return total_pnl
        
    def calc_breakeven(
        self,
        strategy: List[Tuple[OptionContract, int, float]],
    ) -> List[float]:
        """
        计算盈亏平衡点
        
        Args:
            strategy: [(合约, 数量, 开仓价), ...]
            
        Returns:
            盈亏平衡点列表
        """
        breakevens = []
        
        # 简单情况：单腿策略
        if len(strategy) == 1:
            contract, quantity, entry_price = strategy[0]
            
            if contract.option_type == "call":
                be = contract.strike + entry_price / quantity if quantity != 0 else 0
            else:
                be = contract.strike - entry_price / quantity if quantity != 0 else 0
                
            breakevens.append(be)
            
        # 复杂策略需要数值求解
        # 此处简化处理
        
        return breakevens
        
    def calc_max_profit_loss(
        self,
        strategy: List[Tuple[OptionContract, int, float]],
    ) -> Dict[str, float]:
        """
        计算最大盈利/亏损
        
        Args:
            strategy: [(合约, 数量, 开仓价), ...]
            
        Returns:
            {"max_profit": float, "max_loss": float, "upside": float, "downside": float}
        """
        result = {
            "max_profit": float("inf") if len(strategy) > 1 else 0,
            "max_loss": 0,
            "upside": 0,
            "downside": 0,
        }
        
        # 简化处理：假设标的价格从0到无穷大
        # 实际需要考虑合约到期价值和行权价
        
        return result
