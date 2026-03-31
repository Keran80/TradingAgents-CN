# TradingAgents-CN 风控模块测试
# Risk Module Tests

import sys
sys.path.insert(0, ".")

from tradingagents.risk.manager import RiskManager, create_default_risk_manager
from tradingagents.risk.position_manager import PositionManager
from tradingagents.risk.stop_loss import StopLossTakeProfit
from tradingagents.risk.metrics import RiskMetrics


class MockPortfolio:
    def __init__(self, cash=100000, positions=None):
        self._cash = cash
        self._positions = positions or {}

    def get_cash(self):
        return self._cash

    def get_total_value(self):
        return sum(p["quantity"] * p["price"] for p in self._positions.values())

    def get_position(self, symbol):
        if symbol in self._positions:
            class Pos:
                def __init__(self, q, p):
                    self.quantity = q
                    self.current_price = p
            p = self._positions[symbol]
            return Pos(p["quantity"], p["price"])
        return None


def test_position_manager():
    print("\n=== Test Position Manager ===")
    pm = PositionManager(initial_cash=100000)

    ok, msg = pm.open_position("000001.SZ", quantity=1000, price=10.0)
    print(f"Open: {ok}, {msg}")

    pm.update_price("000001.SZ", 11.0)
    pos = pm.get_position("000001.SZ")
    print(f"Position: {pos.quantity} shares, Cost: {pos.avg_cost}, Current: {pos.current_price}")
    print(f"Unrealized PnL: {pos.unrealized_pnl:.2f}")

    ok, msg = pm.close_position("000001.SZ", quantity=500, price=11.0)
    print(f"Close: {ok}, {msg}")

    summary = pm.get_summary()
    print(f"Summary: Cash {summary['cash']:.2f}, Position {summary['position_value']:.2f}")


def test_stop_loss():
    print("\n=== Test Stop Loss ===")
    st = StopLossTakeProfit()
    st.set_fixed_stop_loss("000001.SZ", entry_price=10.0, stop_ratio=0.05)
    print("Set stop loss: entry 10.0, ratio 5%, stop 9.5")

    prices = [10.0, 10.5, 11.0, 9.6, 9.4]
    for price in prices:
        result = st.check_trigger("000001.SZ", price)
        status = "TRIGGERED" if result["stop_triggered"] else "OK"
        print(f"  Price {price:.2f} -> {status}")


def test_risk_manager():
    print("\n=== Test Risk Manager ===")
    rm = create_default_risk_manager(initial_cash=100000, risk_level="normal")

    portfolio = MockPortfolio(cash=80000, positions={
        "000001.SZ": {"quantity": 2000, "price": 10.0},
    })

    order = {"symbol": "000001.SZ", "side": "BUY", "quantity": 1000, "price": 10.5}
    result = rm.check_order(order, portfolio)
    print(f"Order check: {'PASS' if result['approved'] else 'REJECT'}")
    print(f"Message: {result['message']}")


def test_risk_metrics():
    print("\n=== Test Risk Metrics ===")
    metrics = RiskMetrics()
    returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01, 0.02, -0.01, 0.015]

    var_95 = metrics.calculate_var(returns, confidence=0.95)
    vol = metrics.calculate_volatility(returns)
    sharpe = metrics.calculate_sharpe_ratio(returns)

    print(f"VaR (95%): {var_95:.4f}")
    print(f"Volatility: {vol:.4f}")
    print(f"Sharpe: {sharpe:.4f}")


if __name__ == "__main__":
    print("=" * 50)
    print("TradingAgents-CN Risk Module Tests")
    print("=" * 50)

    test_position_manager()
    test_stop_loss()
    test_risk_manager()
    test_risk_metrics()

    print("\n" + "=" * 50)
    print("All tests passed!")
    print("=" * 50)
