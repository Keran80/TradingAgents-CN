# -*- coding: utf-8 -*-
"""
账户同步器

同步实盘账户与本地持仓记录
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict

from .broker import LiveBroker, Account, Position

logger = logging.getLogger(__name__)


@dataclass
class SyncState:
    """同步状态"""
    last_sync_time: datetime = field(default_factory=datetime.now)
    last_account: Optional[Account] = None
    last_positions: List[Position] = field(default_factory=list)
    sync_errors: int = 0
    
    
class AccountSync:
    """
    账户同步器
    
    功能：
    - 定时同步账户余额
    - 定时同步持仓数据
    - 检测持仓变化
    - 推送更新通知
    """
    
    def __init__(
        self,
        broker: LiveBroker,
        sync_interval: float = 30.0,
        on_account_update: Optional[Callable] = None,
        on_position_update: Optional[Callable] = None,
    ):
        """
        初始化同步器
        
        Args:
            broker: 券商接口
            sync_interval: 同步间隔（秒）
            on_account_update: 账户更新回调 (account: Account)
            on_position_update: 持仓更新回调 (positions: List[Position])
        """
        self.broker = broker
        self.sync_interval = sync_interval
        
        self._on_account_update = on_account_update
        self._on_position_update = on_position_update
        
        # 同步状态
        self._state = SyncState()
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        
    def set_callbacks(
        self,
        on_account_update: Optional[Callable] = None,
        on_position_update: Optional[Callable] = None,
    ):
        """设置回调函数"""
        self._on_account_update = on_account_update
        self._on_position_update = on_position_update
        
    def start(self):
        """启动同步"""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("AccountSync started")
        
    def stop(self):
        """停止同步"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("AccountSync stopped")
        
    def sync_now(self) -> bool:
        """
        立即同步
        
        Returns:
            同步是否成功
        """
        try:
            # 同步账户
            account = self.broker.get_account()
            
            # 同步持仓
            positions = self.broker.get_positions()
            
            # 检测变化
            account_changed = self._detect_account_change(account)
            positions_changed = self._detect_positions_change(positions)
            
            # 更新状态
            with self._lock:
                self._state.last_sync_time = datetime.now()
                self._state.last_account = account
                self._state.last_positions = positions
                
            # 推送更新
            if account_changed and self._on_account_update:
                self._on_account_update(account)
                
            if positions_changed and self._on_position_update:
                self._on_position_update(positions)
                
            logger.debug(f"Sync completed: account_changed={account_changed}, "
                        f"positions_changed={positions_changed}")
            
            return True
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            with self._lock:
                self._state.sync_errors += 1
            return False
            
    def get_state(self) -> SyncState:
        """获取同步状态"""
        with self._lock:
            return self._state
            
    def get_account(self) -> Optional[Account]:
        """获取最新账户信息"""
        with self._lock:
            return self._state.last_account
            
    def get_positions(self) -> List[Position]:
        """获取最新持仓"""
        with self._lock:
            return self._state.last_positions.copy()
            
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取指定持仓"""
        positions = self.get_positions()
        return next((p for p in positions if p.symbol == symbol), None)
        
    def _run_loop(self):
        """同步循环"""
        while self._running:
            try:
                self.sync_now()
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                
            time.sleep(self.sync_interval)
            
    def _detect_account_change(
        self,
        new_account: Account,
    ) -> bool:
        """检测账户变化"""
        with self._lock:
            old_account = self._state.last_account
            
        if old_account is None:
            return True
            
        # 比较关键字段
        if (abs(old_account.cash - new_account.cash) > 0.01 or
            abs(old_account.total_assets - new_account.total_assets) > 0.01):
            return True
            
        return False
        
    def _detect_positions_change(
        self,
        new_positions: List[Position],
    ) -> bool:
        """检测持仓变化"""
        with self._lock:
            old_positions = self._state.last_positions
            
        if not old_positions:
            return len(new_positions) > 0
            
        # 转换为字典便于比较
        old_dict = {p.symbol: p for p in old_positions}
        new_dict = {p.symbol: p for p in new_positions}
        
        # 检查新增/删除
        if set(old_dict.keys()) != set(new_dict.keys()):
            return True
            
        # 检查数量变化
        for symbol, old_pos in old_dict.items():
            new_pos = new_dict.get(symbol)
            if new_pos:
                if (old_pos.quantity != new_pos.quantity or
                    abs(old_pos.avg_cost - new_pos.avg_cost) > 0.001):
                    return True
                    
        return False


class PortfolioSync(AccountSync):
    """
    组合同步器（扩展版）
    
    在 AccountSync 基础上增加：
    - 净值计算
    - 盈亏统计
    - 风险指标
    """
    
    def __init__(self, broker: LiveBroker, sync_interval: float = 30.0):
        super().__init__(broker, sync_interval)
        
        # 初始资金（用于计算收益率）
        self._initial_cash = broker.get_account().cash
        
    def get_portfolio_stats(self) -> Dict[str, Any]:
        """
        获取组合统计
        
        Returns:
            组合统计数据
        """
        account = self.get_account()
        positions = self.get_positions()
        
        if not account:
            return {}
            
        # 计算持仓盈亏
        total_pnl = 0.0
        total_position_value = 0.0
        
        for pos in positions:
            pnl = pos.unrealized_pnl
            total_pnl += pnl
            total_position_value += pos.market_value
            
        # 计算收益率
        daily_pnl = total_pnl
        total_return = (account.total_assets - self._initial_cash) / self._initial_cash * 100
        
        # 持仓比例
        position_ratio = total_position_value / account.total_assets * 100 if account.total_assets > 0 else 0
        
        return {
            "account_id": account.account_id,
            "total_assets": account.total_assets,
            "cash": account.cash,
            "available_cash": account.available_cash,
            "market_value": total_position_value,
            "position_ratio": position_ratio,
            "total_pnl": total_pnl,
            "daily_pnl": daily_pnl,
            "total_return_pct": total_return,
            "positions_count": len(positions),
            "last_sync": self._state.last_sync_time.isoformat(),
            "sync_errors": self._state.sync_errors,
        }
