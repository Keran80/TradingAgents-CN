# -*- coding: utf-8 -*-
"""
event_engine.py 单元测试

测试事件驱动引擎核心类
"""
import pytest
from datetime import datetime
from tradingagents.event_engine import (
    Event,
    EventType,
    TickEvent,
    BarEvent,
    OrderEvent,
    TradeEvent,
)


class TestEvent:
    """Event 基类测试"""

    def test_create_event(self):
        """测试创建基础事件"""
        event = Event(
            timestamp=datetime.now(),
            event_type=EventType.CUSTOM,
            source="test"
        )
        
        assert event.event_type == EventType.CUSTOM
        assert event.source == "test"
        assert isinstance(event.timestamp, datetime)

    def test_event_default_timestamp(self):
        """测试默认时间戳"""
        event = Event()
        assert event.event_type == EventType.CUSTOM
        assert event.source == ""
        assert isinstance(event.timestamp, datetime)

    def test_event_with_none_timestamp(self):
        """测试None时间戳自动修正"""
        event = Event(timestamp=None)
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)


class TestTickEvent:
    """TickEvent 测试"""

    def test_create_tick(self):
        """测试创建Tick事件"""
        tick = TickEvent(
            symbol="000001.SZ",
            last_price=10.50,
            volume=1000000,
        )
        
        assert tick.symbol == "000001.SZ"
        assert tick.last_price == 10.50
        assert tick.volume == 1000000
        assert tick.event_type == EventType.TICK

    def test_tick_default_values(self):
        """测试Tick默认值"""
        tick = TickEvent()
        assert tick.symbol == ""
        assert tick.last_price == 0.0
        assert tick.volume == 0


class TestBarEvent:
    """BarEvent 测试"""

    def test_create_bar(self):
        """测试创建Bar事件"""
        bar = BarEvent(
            symbol="600000.SH",
            open=20.0,
            high=21.5,
            low=19.8,
            close=21.0,
            volume=5000000,
        )
        
        assert bar.symbol == "600000.SH"
        assert bar.close == 21.0
        assert bar.high == 21.5
        assert bar.event_type == EventType.BAR


class TestOrderEvent:
    """OrderEvent 测试"""

    def test_create_buy_order(self):
        """测试创建买入订单"""
        order = OrderEvent(
            symbol="000001.SZ",
            side="BUY",
            quantity=100,
            price=15.50,
            order_type="LIMIT",
        )
        
        assert order.symbol == "000001.SZ"
        assert order.side == "BUY"
        assert order.quantity == 100
        assert order.price == 15.50
        assert order.event_type == EventType.ORDER

    def test_create_sell_order(self):
        """测试创建卖出订单"""
        order = OrderEvent(
            symbol="600000.SH",
            side="SELL",
            quantity=200,
            price=25.00,
        )
        
        assert order.side == "SELL"
        assert order.quantity == 200


class TestTradeEvent:
    """TradeEvent 测试"""

    def test_create_trade(self):
        """测试创建成交事件"""
        trade = TradeEvent(
            symbol="000001.SZ",
            side="BUY",
            quantity=100,
            price=15.50,
            commission=4.65,
        )
        
        assert trade.symbol == "000001.SZ"
        assert trade.quantity == 100
        assert trade.commission == 4.65
        assert trade.event_type == EventType.TRADE
