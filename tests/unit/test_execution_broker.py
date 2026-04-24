# -*- coding: utf-8 -*-
"""
券商接口与订单 单元测试

测试范围：
- Order/Trade/Quote 数据类
- 订单属性计算
- 涨跌停判断
- BrokerInterface 抽象类
- SimulatorBrokerConfig
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

try:
    from tradingagents.execution.broker import (
        Order, Trade, Quote, OrderResult,
        OrderType, OrderSide, OrderStatus, PositionEffect,
        BrokerInterface, SimulatorBrokerConfig,
    )
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    pytest.skip("依赖未安装", allow_module_level=True)


class TestOrder:
    """Order 数据类测试"""

    def test_创建市价买入订单(self):
        """测试创建市价买入订单"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,
        )
        assert order.symbol == "000001.SZ"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.quantity == 1000
        assert order.order_id is not None

    def test_创建限价卖出订单(self):
        """测试创建限价卖出订单"""
        order = Order(
            symbol="600000.SH",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=15.50,
            quantity=500,
        )
        assert order.price == 15.50
        assert order.quantity == 500

    def test_创建止损单(self):
        """测试创建止损单"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            price=9.0,
            stop_price=9.5,
            quantity=1000,
        )
        assert order.stop_price == 9.5

    def test_剩余数量_未成交时等于总量(self):
        """测试未成交时剩余数量等于总量"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10.0,
            quantity=1000,
        )
        assert order.remaining_quantity == 1000

    def test_剩余数量_部分成交后减少(self):
        """测试部分成交后剩余数量减少"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10.0,
            quantity=1000,
        )
        order.filled_quantity = 300
        assert order.remaining_quantity == 700

    def test_活跃状态_待提交状态为活跃(self):
        """测试待提交状态为活跃"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10.0,
            quantity=1000,
        )
        assert order.is_active is True

    def test_活跃状态_已提交状态为活跃(self):
        """测试已提交状态为活跃"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10.0,
            quantity=1000,
            status=OrderStatus.SUBMITTED,
        )
        assert order.is_active is True

    def test_活跃状态_部分成交为活跃(self):
        """测试部分成交为活跃"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10.0,
            quantity=1000,
            status=OrderStatus.PARTIAL,
        )
        assert order.is_active is True

    def test_活跃状态_全部成交不活跃(self):
        """测试全部成交不活跃"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10.0,
            quantity=1000,
            status=OrderStatus.FILLED,
        )
        assert order.is_active is False

    def test_活跃状态_已撤销不活跃(self):
        """测试已撤销不活跃"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10.0,
            quantity=1000,
            status=OrderStatus.CANCELLED,
        )
        assert order.is_active is False

    def test_订单金额_限价单有金额(self):
        """测试限价单有订单金额"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10.0,
            quantity=1000,
        )
        assert order.order_value == 10000.0

    def test_订单金额_市价单价格为0金额0(self):
        """测试市价单默认订单金额为0"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,
        )
        assert order.order_value == 0.0

    def test_数量非正数抛出异常(self):
        """测试数量非正数抛出异常"""
        with pytest.raises(ValueError):
            Order(
                symbol="000001.SZ",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0,
            )

    def test_数量负数抛出异常(self):
        """测试数量负数抛出异常"""
        with pytest.raises(ValueError):
            Order(
                symbol="000001.SZ",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=-100,
            )

    def test_限价单价格为正数不抛异常(self):
        """测试限价单正价格不抛异常"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=10.0,
            quantity=1000,
        )
        assert order.price == 10.0

    def test_限价单价格非正数抛出异常(self):
        """测试限价单价格非正数抛异常"""
        with pytest.raises(ValueError):
            Order(
                symbol="000001.SZ",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=0.0,
                quantity=1000,
            )

    def test_默认开仓标识为OPEN(self):
        """测试默认开仓标识为OPEN"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,
        )
        assert order.position_effect == PositionEffect.OPEN

    def test_默认状态为PENDING(self):
        """测试默认状态为PENDING"""
        order = Order(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000,
        )
        assert order.status == OrderStatus.PENDING


class TestTrade:
    """Trade 数据类测试"""

    def test_创建成交记录(self):
        """测试创建成交记录"""
        trade = Trade(
            order_id="order_001",
            symbol="000001.SZ",
            side=OrderSide.BUY,
            price=10.0,
            quantity=1000,
            commission=5.0,
        )
        assert trade.trade_id is not None
        assert trade.order_id == "order_001"
        assert trade.price == 10.0
        assert trade.commission == 5.0

    def test_成交金额_计算正确(self):
        """测试成交金额计算"""
        trade = Trade(
            symbol="000001.SZ",
            side=OrderSide.BUY,
            price=15.0,
            quantity=2000,
        )
        assert trade.trade_value == 30000.0


class TestQuote:
    """Quote 行情数据类测试"""

    def test_创建行情数据_默认值全为0(self):
        """测试创建行情数据-默认值"""
        quote = Quote(symbol="000001.SZ", last_price=10.0)
        assert quote.symbol == "000001.SZ"
        assert quote.last_price == 10.0
        assert quote.volume == 0

    def test_涨停价_计算为最新价110(self):
        """测试涨停价计算"""
        quote = Quote(symbol="000001.SZ", last_price=10.0)
        assert quote.upper_limit == pytest.approx(11.0)

    def test_跌停价_计算为最新价90(self):
        """测试跌停价计算"""
        quote = Quote(symbol="000001.SZ", last_price=10.0)
        assert quote.lower_limit == pytest.approx(9.0)

    def test_涨停价_最新价为0时涨停价为0(self):
        """测试最新价为0时涨停价为0"""
        quote = Quote(symbol="000001.SZ", last_price=0.0)
        assert quote.upper_limit == 0.0

    def test_跌停价_最新价为0时跌停价为0(self):
        """测试最新价为0时跌停价为0"""
        quote = Quote(symbol="000001.SZ", last_price=0.0)
        assert quote.lower_limit == 0.0

    def test_涨停判断_涨停返回True(self):
        """测试涨停判断"""
        quote = Quote(symbol="000001.SZ", last_price=11.0)
        assert quote.is_limit_up(prev_close=10.0) is True

    def test_涨停判断_非涨停返回False(self):
        """测试非涨停判断"""
        quote = Quote(symbol="000001.SZ", last_price=10.5)
        assert quote.is_limit_up(prev_close=10.0) is False

    def test_涨停判断_前收价为0返回False(self):
        """测试前收价为0时返回False"""
        quote = Quote(symbol="000001.SZ", last_price=10.0)
        assert quote.is_limit_up(prev_close=0.0) is False

    def test_跌停判断_跌停返回True(self):
        """测试跌停判断"""
        quote = Quote(symbol="000001.SZ", last_price=9.0)
        assert quote.is_limit_down(prev_close=10.0) is True

    def test_跌停判断_非跌停返回False(self):
        """测试非跌停判断"""
        quote = Quote(symbol="000001.SZ", last_price=9.5)
        assert quote.is_limit_down(prev_close=10.0) is False

    def test_跌停判断_前收价为0返回False(self):
        """测试前收价为0时返回False"""
        quote = Quote(symbol="000001.SZ", last_price=9.0)
        assert quote.is_limit_down(prev_close=0.0) is False


class TestOrderResult:
    """OrderResult 测试"""

    def test_成功结果_创建正确(self):
        """测试成功结果创建"""
        result = OrderResult(success=True, order_id="order_001", message="OK")
        assert result.success is True
        assert result.order_id == "order_001"

    def test_失败结果_创建正确含错误码(self):
        """测试失败结果创建"""
        result = OrderResult(success=False, order_id="order_001", message="Failed", error_code="ERR_001")
        assert result.success is False
        assert result.error_code == "ERR_001"


class TestSimulatorBrokerConfig:
    """SimulatorBrokerConfig 测试"""

    def test_默认配置(self):
        """测试默认配置"""
        config = SimulatorBrokerConfig()
        assert config.commission_rate == 0.0003
        assert config.stamp_tax == 0.001
        assert config.slippage == 0.001
        assert config.price_limit_ratio == 0.10
        assert config.min_commission == 5.0

    def test_自定义配置(self):
        """测试自定义配置"""
        config = SimulatorBrokerConfig(
            commission_rate=0.0001,
            stamp_tax=0.0005,
            slippage=0.0005,
            min_commission=0.0,
        )
        assert config.commission_rate == 0.0001
        assert config.stamp_tax == 0.0005
        assert config.slippage == 0.0005
        assert config.min_commission == 0.0


class TestBrokerInterface:
    """BrokerInterface 抽象基类测试"""

    def test_不能直接实例化抽象基类(self):
        """测试不能直接实例化抽象基类"""
        with pytest.raises(TypeError):
            BrokerInterface()

    def test_子类必须实现所有抽象方法(self):
        """测试子类必须实现所有抽象方法"""
        class IncompleteBroker(BrokerInterface):
            def connect(self):
                return True

            def disconnect(self):
                return True

            # 缺少其他抽象方法

        with pytest.raises(TypeError):
            IncompleteBroker()

    def test_完整子类实例化成功(self):
        """测试完整子类实例化成功"""
        class CompleteBroker(BrokerInterface):
            def connect(self): return True
            def disconnect(self): return True
            def place_order(self, order): return OrderResult(success=True)
            def cancel_order(self, order_id): return OrderResult(success=True)
            def get_order_status(self, order_id): return None
            def get_orders(self, symbol=None, status=None): return []
            def get_trades(self, order_id=None): return []
            def get_positions(self): return []
            def get_account(self): return {}
            def get_quote(self, symbol): return None

        broker = CompleteBroker()
        assert isinstance(broker, BrokerInterface)
        assert broker.is_connected is False

    def test_连接属性初始化时为False(self):
        """测试连接属性初始化时为False"""
        class TestBroker(BrokerInterface):
            def connect(self): return True
            def disconnect(self): return True
            def place_order(self, order): return OrderResult(success=True)
            def cancel_order(self, order_id): return OrderResult(success=True)
            def get_order_status(self, order_id): return None
            def get_orders(self, symbol=None, status=None): return []
            def get_trades(self, order_id=None): return []
            def get_positions(self): return []
            def get_account(self): return {}
            def get_quote(self, symbol): return None

        broker = TestBroker()
        assert broker.is_connected is False

    def test_配置参数初始化可为空(self):
        """测试配置参数初始化可为空"""
        class TestBroker(BrokerInterface):
            def connect(self): return True
            def disconnect(self): return True
            def place_order(self, order): return OrderResult(success=True)
            def cancel_order(self, order_id): return OrderResult(success=True)
            def get_order_status(self, order_id): return None
            def get_orders(self, symbol=None, status=None): return []
            def get_trades(self, order_id=None): return []
            def get_positions(self): return []
            def get_account(self): return {}
            def get_quote(self, symbol): return None

        broker = TestBroker(config=None)
        assert broker.config == {}

    def test_get_required_fields_默认返回空列表(self):
        """测试get_required_fields默认返回空列表"""
        class TestBroker(BrokerInterface):
            def connect(self): return True
            def disconnect(self): return True
            def place_order(self, order): return OrderResult(success=True)
            def cancel_order(self, order_id): return OrderResult(success=True)
            def get_order_status(self, order_id): return None
            def get_orders(self, symbol=None, status=None): return []
            def get_trades(self, order_id=None): return []
            def get_positions(self): return []
            def get_account(self): return {}
            def get_quote(self, symbol): return None

        broker = TestBroker()
        assert broker.get_required_fields() == []


class TestEnums:
    """枚举类型测试"""

    def test_OrderType_枚举值(self):
        """测试订单类型枚举"""
        assert OrderType.MARKET.value == "MARKET"
        assert OrderType.LIMIT.value == "LIMIT"
        assert OrderType.STOP.value == "STOP"

    def test_OrderSide_枚举值(self):
        """测试订单方向枚举"""
        assert OrderSide.BUY.value == "BUY"
        assert OrderSide.SELL.value == "SELL"

    def test_OrderStatus_枚举值(self):
        """测试订单状态枚举"""
        assert OrderStatus.PENDING.value == "PENDING"
        assert OrderStatus.FILLED.value == "FILLED"
        assert OrderStatus.CANCELLED.value == "CANCELLED"

    def test_PositionEffect_枚举值(self):
        """测试持仓效应枚举"""
        assert PositionEffect.OPEN.value == "OPEN"
        assert PositionEffect.CLOSE.value == "CLOSE"
