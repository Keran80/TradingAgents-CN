# TradingAgents-CN 量化交易升级方案

> 目标：实现真正的量化交易能力，从研究框架进化为生产级交易系统
> 制定时间：2026-03-30
> 版本：v1.0

---

## 一、现状评估

### 1.1 当前能力矩阵

| 层级 | 模块 | 状态 | 成熟度 |
|------|------|------|--------|
| **数据层** | AkShare（A股） | ✅ 完善 | ★★★★☆ |
| | TDX 通达信（实时） | ✅ 完善 | ★★★★☆ |
| | Finnhub（美股） | ✅ 可用 | ★★★☆☆ |
| **策略层** | 技术指标（MA/RSI/MACD/BOLL） | ✅ 基础 | ★★★☆☆ |
| | 组合策略 | ✅ 基础 | ★★★☆☆ |
| | 策略回测 | ⚠️ 简单循环 | ★★☆☆☆ |
| **智能体层** | 多角色分析师 | ✅ 完善 | ★★★★☆ |
| | 风险辩论机制 | ✅ 完善 | ★★★★☆ |
| **执行层** | 模拟交易所 | ✅ 已完成 | ★★★★☆ |
| **风控层** | 预警监控 | ⚠️ 仅监控 | ★★☆☆☆ |
| | 实时风控引擎 | ⚠️ 基础 | ★★★☆☆ |

### 1.2 核心差距

```
当前状态                    目标状态
┌─────────────┐            ┌─────────────┐
│  信号生成    │     →     │  订单执行    │  ← 关键差距
│  (已完成)    │            │  (需开发)    │
└─────────────┘            └─────────────┘

缺少的核心组件：
1. 交易执行接口（券商API对接）
2. 订单管理系统（订单生命周期）
3. 账户资金管理（持仓/余额）
4. 实时风控引擎（事前/事中/事后）
5. 事件驱动架构（当前是简单循环）
```

---

## 二、升级路线图

```
Phase 1        Phase 2        Phase 3        Phase 4
基础交易 ──── 策略框架 ──── 风控体系 ──── 生产部署
(2-4周)       (4-6周)       (4-6周)       (2-4周)
  │             │             │             │
  ▼             ▼             ▼             ▼
┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐
│模拟 │      │事件 │      │实时 │      │监控 │
│交易 │      │驱动 │      │风控 │      │日志 │
│接口 │      │架构 │      │引擎 │      │告警 │
└─────┘      └─────┘      └─────┘      └─────┘
```

---

## 三、Phase 1：基础交易功能（优先级最高）

### 3.1 目标
实现最小可行交易系统，完成从"信号生成"到"订单执行"的闭环。

### 3.2 新增模块

#### 3.2.1 交易接口层 `tradingagents/execution/`

```
tradingagents/execution/
├── __init__.py
├── broker.py              # 券商适配器基类
├── simulators/            # 模拟交易
│   ├── __init__.py
│   ├── order_manager.py   # 订单管理
│   ├── account.py         # 账户管理
│   └── portfolio.py       # 持仓管理
├── brokers/               # 真实券商（未来扩展）
│   ├── __init__.py
│   ├── base.py
│   └── tdx_broker.py      # 通达信券商接口
└── router.py              # 交易路由（模拟/实盘切换）
```

#### 3.2.2 核心类设计

**OrderManager（订单管理器）**

```python
class OrderManager:
    """订单生命周期管理"""
    
    def __init__(self, broker: BrokerInterface):
        self.broker = broker
        self.pending_orders: Dict[str, Order] = {}
        self.filled_orders: List[Order] = []
        self.order_history: List[dict] = []
    
    def place_order(self, order: Order) -> str:
        """下单，返回订单ID"""
        # 1. 订单预处理（合并/拆分）
        # 2. 提交到broker
        # 3. 跟踪订单状态
        # 4. 返回订单ID
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
    
    def get_order_status(self, order_id: str) -> OrderStatus:
        """查询订单状态"""
    
    def match_orders(self) -> List[Trade]:
        """撮合（模拟盘）/ 轮询实盘成交状态"""
```

**Account（账户管理）**

```python
class Account:
    """账户资金管理"""
    
    def __init__(self, initial_capital: float = 1000000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.frozen_cash = 0.0
        self.margin = 0.0
        self.positions: Dict[str, Position] = {}
    
    def update_position(self, symbol: str, quantity: int, avg_cost: float):
        """更新持仓"""
    
    def get_available_cash(self) -> float:
        """可用资金 = 现金 - 冻结资金"""
        return self.cash - self.frozen_cash
    
    def calculate_equity(self, market_prices: Dict[str, float]) -> float:
        """计算账户净值（市值 + 现金）"""
```

**Portfolio（持仓管理）**

```python
@dataclass
class Position:
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.avg_cost) * self.quantity
    
    @property
    def return_pct(self) -> float:
        if self.avg_cost == 0:
            return 0.0
        return (self.current_price - self.avg_cost) / self.avg_cost * 100

class Portfolio:
    """组合持仓管理"""
    
    def __init__(self, account: Account):
        self.account = account
        self.positions: Dict[str, Position] = {}
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
    
    def get_all_positions(self) -> List[Position]:
        """获取所有持仓"""
    
    def calculate_total_value(self, prices: Dict[str, float]) -> float:
        """计算组合总市值"""
```

### 3.3 模拟交易执行器

```python
# tradingagents/execution/simulators/simulator.py

class SimulatorBroker(BrokerInterface):
    """
    模拟交易券商
    - 模拟订单撮合
    - 支持市价单、限价单
    - 模拟滑点和手续费
    """
    
    def __init__(
        self,
        commission_rate: float = 0.0003,    # 佣金万三
        slippage: float = 0.001,           # 滑点 0.1%
        price_limit_ratio: float = 0.10    # 涨跌停 10%
    ):
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.price_limit_ratio = price_limit_ratio
    
    def place_order(self, order: Order) -> OrderResult:
        # 1. 验证订单合法性
        # 2. 检查涨跌停
        # 3. 计算成交价（加入滑点）
        # 4. 扣除手续费
        # 5. 更新账户
        # 6. 返回成交结果
    
    def get_realtime_quote(self, symbol: str) -> Quote:
        """获取实时行情用于撮合"""
```

### 3.4 与现有系统集成

```python
# tradingagents/execution/trading_engine.py

class TradingEngine:
    """
    交易引擎 - 整合信号生成与订单执行
    """
    
    def __init__(
        self,
        broker: BrokerInterface,
        risk_manager: RiskManager,
        data_source: DataSource
    ):
        self.broker = broker
        self.risk_manager = risk_manager
        self.data_source = data_source
        self.order_manager = OrderManager(broker)
        self.account = Account()
        self.portfolio = Portfolio(self.account)
    
    def execute_signal(self, signal: Signal) -> ExecutionResult:
        """
        执行交易信号
        1. 风险检查
        2. 生成订单
        3. 提交执行
        4. 记录日志
        """
        # 前置风控检查
        if not self.risk_manager.pre_check(signal, self.portfolio):
            return ExecutionResult(status="REJECTED", reason="RISK_CHECK_FAILED")
        
        # 生成订单
        order = self._signal_to_order(signal)
        
        # 提交订单
        order_id = self.order_manager.place_order(order)
        
        # 返回执行结果
        return ExecutionResult(order_id=order_id, status="SUBMITTED")
    
    def sync_positions(self):
        """同步持仓（收盘后或启动时调用）"""
    
    def get_portfolio_status(self) -> dict:
        """获取组合状态快照"""
```

---

## 四、Phase 2：策略框架升级

### 4.1 事件驱动架构

```python
# tradingagents/execution/event_engine.py

class Event:
    """事件基类"""
    pass

class TickEvent(Event):
    def __init__(self, symbol: str, price: float, volume: int, timestamp: datetime):
        self.symbol = symbol
        self.price = price
        self.volume = volume
        self.timestamp = timestamp

class OrderEvent(Event):
    def __init__(self, order: Order, event_type: str):
        self.order = order
        self.event_type = event_type  # NEW, PARTIAL, FILLED, CANCELLED

class SignalEvent(Event):
    def __init__(self, signal: Signal):
        self.signal = signal

class EventEngine:
    """
    事件驱动引擎
    - 事件队列
    - 事件分发
    - 事件处理器注册
    """
    
    def __init__(self):
        self.queue = queue.Queue()
        self.handlers: Dict[Type[Event], List[Callable]] = defaultdict(list)
    
    def register(self, event_type: Type[Event], handler: Callable):
        """注册事件处理器"""
        self.handlers[event_type].append(handler)
    
    def put(self, event: Event):
        """放入事件"""
        self.queue.put(event)
    
    def run(self):
        """事件循环"""
        while self.running:
            event = self.queue.get()
            for handler in self.handlers[type(event)]:
                handler(event)
```

### 4.2 策略模板库

```python
# tradingagents/strategies/templates.py

class StrategyTemplate(ABC):
    """策略基类"""
    
    @abstractmethod
    def on_init(self):
        """策略初始化"""
        pass
    
    @abstractmethod
    def on_tick(self, tick: TickEvent):
        """行情数据处理"""
        pass
    
    @abstractmethod
    def on_bar(self, bar: BarData):
        """K线数据处理"""
        pass
    
    def buy(self, symbol: str, price: float, quantity: int):
        """买入"""
    
    def sell(self, symbol: str, price: float, quantity: int):
        """卖出"""
    
    @abstractmethod
    def on_trade(self, trade: Trade):
        """成交回报"""
        pass


class MeanReversionStrategy(StrategyTemplate):
    """均值回归策略模板"""
    
    def __init__(self, symbol: str, lookback: int = 20, std_dev: float = 2.0):
        self.symbol = symbol
        self.lookback = lookback
        self.std_dev = std_dev
        self.prices = []
    
    def on_bar(self, bar: BarData):
        self.prices.append(bar.close)
        if len(self.prices) < self.lookback:
            return
        
        # 计算均值和标准差
        mean = np.mean(self.prices[-self.lookback:])
        std = np.std(self.prices[-self.lookback:])
        
        # 生成信号
        if bar.close < mean - self.std_dev * std:
            self.buy(self.symbol, bar.close, 100)
        elif bar.close > mean + self.std_dev * std:
            self.sell(self.symbol, bar.close, 100)


class MomentumStrategy(StrategyTemplate):
    """动量策略模板"""
    
    def __init__(self, symbol: str, fast: int = 10, slow: int = 30):
        self.symbol = symbol
        self.fast = fast
        self.slow = slow
        self.prices = []
    
    def on_bar(self, bar: BarData):
        self.prices.append(bar.close)
        if len(self.prices) < self.slow:
            return
        
        fast_ma = np.mean(self.prices[-self.fast:])
        slow_ma = np.mean(self.prices[-self.slow:])
        
        if fast_ma > slow_ma and self.position == 0:
            self.buy(self.symbol, bar.close, 100)
        elif fast_ma < slow_ma and self.position > 0:
            self.sell(self.symbol, bar.close, abs(self.position))
```

### 4.3 参数优化框架

```python
# tradingagents/strategies/optimizer.py

class GridOptimizer:
    """网格搜索优化器"""
    
    def __init__(self, strategy_class: Type[Strategy], param_grid: dict):
        self.strategy_class = strategy_class
        self.param_grid = param_grid
    
    def optimize(self, data: pd.DataFrame, metric: str = "sharpe_ratio") -> dict:
        """
        参数优化
        返回最优参数组合和回测结果
        """
        results = []
        
        for params in self._generate_param_combinations():
            strategy = self.strategy_class(**params)
            result = self._backtest(strategy, data)
            results.append({**params, **result})
        
        # 返回最优
        return max(results, key=lambda x: x[metric])


class GeneticOptimizer:
    """遗传算法优化器（高级）"""
    
    def __init__(self, strategy_class: Type[Strategy], param_ranges: dict):
        self.strategy_class = strategy_class
        self.param_ranges = param_ranges
        self.population_size = 50
        self.generations = 100
        self.mutation_rate = 0.1
        self.crossover_rate = 0.7
    
    def optimize(self, data: pd.DataFrame) -> dict:
        """遗传算法优化"""
        # 初始化种群
        # 评估适应度
        # 选择、交叉、变异
        # 迭代直到收敛
        pass
```

---

## 五、Phase 3：风控体系

### 5.1 三层风控架构

```
┌─────────────────────────────────────────────────────┐
│                   风控体系                            │
├─────────────┬─────────────────┬─────────────────────┤
│  事前风控    │     事中风控     │      事后风控        │
│  (下单前)    │    (下单中)      │     (交易后)         │
├─────────────┼─────────────────┼─────────────────────┤
│ 单笔限额     │ 持仓限额         │ 日盈亏监控           │
│ 日交易次数   │ 资金使用率       │ 回撤监控             │
│ 涨跌停检查   │ 风险敞口        │ VaR计算              │
│ 持仓时间     │ 保证金比例       │ 业绩归因             │
└─────────────┴─────────────────┴─────────────────────┘
```

### 5.2 风控引擎实现

```python
# tradingagents/risk/engine.py

class RiskRule(ABC):
    """风控规则基类"""
    
    @abstractmethod
    def check(self, context: RiskContext) -> RiskResult:
        """执行风控检查"""
        pass


class PositionLimitRule(RiskRule):
    """持仓限额规则"""
    
    def __init__(
        self,
        max_position_per_stock: float = 0.3,  # 单股最大仓位 30%
        max_total_position: float = 0.8        # 总仓位上限 80%
    ):
        self.max_position_per_stock = max_position_per_stock
        self.max_total_position = max_total_position
    
    def check(self, context: RiskContext) -> RiskResult:
        order = context.order
        portfolio = context.portfolio
        
        # 检查单股仓位
        order_value = order.price * order.quantity
        portfolio_value = portfolio.total_value
        new_position_ratio = order_value / portfolio_value
        
        if new_position_ratio > self.max_position_per_stock:
            return RiskResult(
                passed=False,
                reason=f"单股仓位 {new_position_ratio:.1%} 超过限制 {self.max_position_per_stock:.1%}"
            )
        
        # 检查总仓位
        current_position_value = portfolio.total_position_value
        new_total_ratio = (current_position_value + order_value) / portfolio_value
        
        if new_total_ratio > self.max_total_position:
            return RiskResult(
                passed=False,
                reason=f"总仓位 {new_total_ratio:.1%} 超过限制 {self.max_total_position:.1%}"
            )
        
        return RiskResult(passed=True)


class DailyLossLimitRule(RiskRule):
    """日亏损限制规则"""
    
    def __init__(
        self,
        daily_loss_limit: float = 0.05,      # 日亏损上限 5%
        max_consecutive_losses: int = 3       # 最大连续亏损次数
    ):
        self.daily_loss_limit = daily_loss_limit
        self.max_consecutive_losses = max_consecutive_losses
    
    def check(self, context: RiskContext) -> RiskResult:
        account = context.account
        
        # 检查日亏损
        daily_pnl = account.today_pnl
        daily_loss_ratio = daily_pnl / account.initial_capital
        
        if daily_loss_ratio < -self.daily_loss_limit:
            return RiskResult(
                passed=False,
                reason=f"日亏损 {abs(daily_loss_ratio):.1%} 超过限制 {self.daily_loss_limit:.1%}"
            )
        
        # 检查连续亏损
        if account.consecutive_losses >= self.max_consecutive_losses:
            return RiskResult(
                passed=False,
                reason=f"连续亏损 {account.consecutive_losses} 次超过限制"
            )
        
        return RiskResult(passed=True)


class RiskEngine:
    """风控引擎"""
    
    def __init__(self):
        self.rules: List[RiskRule] = []
        self._register_default_rules()
    
    def _register_default_rules(self):
        """注册默认规则"""
        self.rules.append(PositionLimitRule())
        self.rules.append(DailyLossLimitRule())
        self.rules.append(PriceLimitRule())           # 涨跌停检查
        self.rules.append(TradingHoursRule())          # 交易时间检查
        self.rules.append(MarginLevelRule())           # 保证金检查
    
    def pre_check(self, order: Order, portfolio: Portfolio) -> bool:
        """下单前风控检查"""
        context = RiskContext(order=order, portfolio=portfolio)
        
        for rule in self.rules:
            result = rule.check(context)
            if not result.passed:
                logger.warning(f"风控拒绝: {result.reason}")
                return False
        
        return True
    
    def post_check(self, trade: Trade, portfolio: Portfolio) -> RiskReport:
        """成交后风险评估"""
        # 更新风险指标
        # 计算VaR
        # 生成风险报告
        pass
```

### 5.3 止损止盈管理

```python
# tradingagents/risk/stoploss.py

class StopLossManager:
    """止损止盈管理器"""
    
    def __init__(self):
        self.stop_orders: Dict[str, StopOrder] = {}
    
    def add_stop_loss(self, symbol: str, entry_price: float, 
                      stop_pct: float = 0.05):
        """添加止损单"""
        stop_price = entry_price * (1 - stop_pct)
        self.stop_orders[symbol] = StopOrder(
            symbol=symbol,
            stop_price=stop_price,
            order_type="STOP_LOSS",
            trigger_condition="price <= stop_price"
        )
    
    def add_take_profit(self, symbol: str, entry_price: float,
                        target_pct: float = 0.10):
        """添加止盈单"""
        target_price = entry_price * (1 + target_pct)
        self.stop_orders[symbol] = StopOrder(
            symbol=symbol,
            stop_price=target_price,
            order_type="TAKE_PROFIT",
            trigger_condition="price >= target_price"
        )
    
    def add_trailing_stop(self, symbol: str, callback_rate: float = 0.03):
        """添加追踪止损"""
        self.stop_orders[symbol] = StopOrder(
            symbol=symbol,
            callback_rate=callback_rate,
            order_type="TRAILING_STOP"
        )
    
    def check_stops(self, current_prices: Dict[str, float]) -> List[Order]:
        """检查止损单是否触发"""
        triggered = []
        for symbol, stop in self.stop_orders.items():
            if symbol in current_prices:
                if stop.is_triggered(current_prices[symbol]):
                    triggered.append(stop.to_order())
        return triggered
```

---

## 六、Phase 4：生产部署

### 6.1 监控告警系统

```python
# tradingagents/monitoring/alert.py

class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.channels = []  # 邮件、微信、钉钉等
    
    def send_alert(self, level: AlertLevel, message: str, context: dict = None):
        """发送告警"""
        alert = Alert(level=level, message=message, context=context)
        
        if level == AlertLevel.CRITICAL:
            self._send_to_all(alert)
        elif level == AlertLevel.WARNING:
            self._send_to_primary(alert)
        else:
            self._log(alert)


class MonitorDashboard:
    """监控仪表盘"""
    
    def __init__(self, trading_engine: TradingEngine, risk_engine: RiskEngine):
        self.engine = trading_engine
        self.risk_engine = risk_engine
    
    def get_status(self) -> dict:
        """获取系统状态"""
        return {
            "account": {
                "cash": self.engine.account.cash,
                "equity": self.engine.account.equity,
                "daily_pnl": self.engine.account.today_pnl,
            },
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "pnl": p.unrealized_pnl,
                    "return": p.return_pct
                }
                for p in self.engine.portfolio.positions.values()
            ],
            "risk": {
                "daily_loss_used": abs(self.engine.account.today_pnl) / self.engine.account.initial_capital,
                "total_position_ratio": self.engine.portfolio.total_position_value / self.engine.portfolio.total_value
            },
            "orders": {
                "pending": len(self.engine.order_manager.pending_orders),
                "today_filled": len([o for o in self.engine.order_manager.filled_orders 
                                     if o.fill_time.date() == datetime.today().date()])
            }
        }
```

### 6.2 日志审计系统

```python
# tradingagents/monitoring/audit.py

class AuditLogger:
    """交易审计日志"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def log_signal(self, signal: Signal):
        """记录信号"""
        self._insert("signals", {
            "timestamp": datetime.now(),
            "symbol": signal.symbol,
            "signal_type": signal.signal_type.value,
            "confidence": signal.confidence,
            "reason": signal.reason
        })
    
    def log_order(self, order: Order):
        """记录订单"""
        self._insert("orders", {
            "timestamp": datetime.now(),
            "order_id": order.order_id,
            "symbol": order.symbol,
            "direction": order.direction.value,
            "order_type": order.order_type.value,
            "price": order.price,
            "quantity": order.quantity,
            "status": order.status.value
        })
    
    def log_trade(self, trade: Trade):
        """记录成交"""
        self._insert("trades", {
            "timestamp": datetime.now(),
            "trade_id": trade.trade_id,
            "order_id": trade.order_id,
            "symbol": trade.symbol,
            "price": trade.price,
            "quantity": trade.quantity,
            "commission": trade.commission
        })
    
    def log_risk_event(self, event_type: str, details: dict):
        """记录风控事件"""
        self._insert("risk_events", {
            "timestamp": datetime.now(),
            "event_type": event_type,
            "details": json.dumps(details)
        })
```

### 6.3 定时任务

| 任务 | 时间 | 操作 |
|------|------|------|
| 开盘前检查 | 09:15 | 账户状态、风控规则、重置日计数 |
| 盘中监控 | 09:30-11:30, 13:00-15:00 | 实时行情、止损触发检查 |
| 收盘后处理 | 15:05 | 持仓同步、净值计算、日志归档 |
| 夜盘（期货） | 21:00-23:00 | 夜盘行情监控 |

---

## 七、技术债务与优化

### 7.1 依赖升级

| 库 | 当前版本 | 目标版本 | 原因 |
|----|---------|---------|------|
| backtrader | 1.9.78 | 保持 | 稳定可靠 |
| akshare | 最新 | 保持 | 数据源 |
| vnpy (gateway) | - | 2.3.x | 交易接口 |

### 7.2 性能优化

- **数据缓存**：增加 Redis 缓存层，减少 API 调用
- **并行回测**：使用 multiprocessing 加速参数优化
- **事件队列**：用 asyncio 替代 threading

### 7.3 安全加固

- API Key 加密存储
- 操作日志防篡改
- 权限分级（只读、回测下单、实盘交易）

---

## 八、里程碑与验收标准

| 阶段 | 完成标志 | 验收测试 |
|------|---------|---------|
| Phase 1 | 模拟交易闭环 | MA策略连续运行1周，无异常 |
| Phase 2 | 事件驱动架构 | 支持同时运行3个策略 |
| Phase 3 | 风控生效 | 触发止损单，账户净值保护 |
| Phase 4 | 生产就绪 | 7x24监控，无漏单 |

---

## 九、附录

### 9.1 参考项目

- [vnpy](https://github.com/vnpy/vnpy) - 国内量化交易框架标杆
- [backtrader](https://www.backtrader.com/) - 成熟回测框架
- [quantconnect/Lean](https://github.com/QuantConnect/Lean) - 国际化量化引擎

### 9.2 文件结构（升级后）

```
TradingAgents-CN/
├── tradingagents/
│   ├── execution/          # 新增：交易执行层
│   │   ├── broker.py
│   │   ├── order_manager.py
│   │   ├── account.py
│   │   ├── portfolio.py
│   │   ├── simulators/
│   │   └── brokers/
│   ├── strategies/         # 升级：策略框架
│   │   ├── templates.py
│   │   ├── optimizer.py
│   │   └── examples/
│   ├── risk/               # 新增：风控引擎
│   │   ├── engine.py
│   │   ├── rules/
│   │   └── stoploss.py
│   ├── monitoring/         # 新增：监控告警
│   │   ├── alert.py
│   │   ├── dashboard.py
│   │   └── audit.py
│   ├── event_engine.py      # 新增：事件驱动
│   └── trading_engine.py    # 新增：交易引擎
├── tests/
│   ├── test_execution/
│   ├── test_strategies/
│   ├── test_risk/
│   └── test_integration/
└── docs/
    └── upgrade_guide.md
```

---

*本文档为技术规划文档，具体实现请分阶段推进。建议先完成 Phase 1 验证可行性。*

---

## 更新记录

### 2026-03-30 Phase 1 完成

**新增文件结构：**
```
tradingagents/execution/
├── __init__.py           # 模块导出
├── broker.py             # 券商适配器基类（Order/Trade/Quote）
├── account.py            # 账户管理
├── portfolio.py          # 持仓管理
├── order_manager.py      # 订单生命周期管理
├── trading_engine.py     # 交易引擎（信号→订单）
├── simulators/
│   ├── __init__.py
│   └── simulator.py      # 模拟交易券商（撮合引擎）
└── brokers/
    └── __init__.py       # 真实券商接口占位

examples/
├── __init__.py
├── example_simulator.py  # 模拟交易示例
└── example_backtest.py   # 回测示例
```

**核心功能：**
- Order/Trade/Quote 数据类定义
- SimulatorBroker 模拟撮合（支持市价单、限价单、涨跌停、滑点、手续费）
- Account 账户管理（资金冻结/解冻、盈亏计算）
- Portfolio 持仓管理（加仓/减仓/市值计算）
- OrderManager 订单管理（提交/撤销/状态跟踪）
- TradingEngine 信号执行引擎（风控前置检查）

**运行测试：**
```bash
python examples/example_simulator.py
```
