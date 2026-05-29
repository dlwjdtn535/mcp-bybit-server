"""Tests for the safety gates and order-size cap (no live API calls)."""
import pytest

import server
from config import Config


@pytest.fixture(autouse=True)
def reset_flags():
    orig = (Config.TRADING_ENABLED, Config.READONLY_MODE)
    yield
    Config.TRADING_ENABLED, Config.READONLY_MODE = orig


# --- _trading_guard -------------------------------------------------------

def test_guard_blocks_when_trading_disabled():
    Config.TRADING_ENABLED = False
    Config.READONLY_MODE = False
    err = server._trading_guard()
    assert err is not None and "DISABLED" in err["error"]


def test_guard_readonly_takes_precedence_over_trading_enabled():
    Config.TRADING_ENABLED = True
    Config.READONLY_MODE = True
    err = server._trading_guard()
    assert err is not None and "Read-only" in err["error"]


def test_guard_allows_when_enabled_and_not_readonly():
    Config.TRADING_ENABLED = True
    Config.READONLY_MODE = False
    assert server._trading_guard() is None


# --- mutating tools respect the guard ------------------------------------

def test_place_order_blocked_does_not_touch_service(monkeypatch):
    Config.TRADING_ENABLED = False
    Config.READONLY_MODE = False

    def boom(*a, **k):
        raise AssertionError("service.place_order must not be called when blocked")

    monkeypatch.setattr(server.bybit_service, "place_order", boom)
    res = server.place_order("spot", "BTCUSDT", "Buy", "Market", "10")
    assert "error" in res


def test_set_margin_mode_blocked(monkeypatch):
    Config.TRADING_ENABLED = False
    monkeypatch.setattr(server.bybit_service, "set_margin_mode",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("blocked")))
    res = server.set_margin_mode("linear", "BTCUSDT", 0, "10", "10")
    assert "error" in res


def test_set_leverage_blocked(monkeypatch):
    Config.TRADING_ENABLED = False
    monkeypatch.setattr(server.bybit_service, "set_leverage",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("blocked")))
    res = server.set_leverage("linear", "BTCUSDT", "10", "10")
    assert "error" in res


# --- _check_order_size ----------------------------------------------------

def test_spot_market_buy_over_cap():
    err = server._check_order_size("spot", "BTCUSDT", "Buy", "Market", "9999", None)
    assert err is not None and "exceeds MAX_ORDER_SIZE_USDT" in err["error"]


def test_spot_market_buy_under_cap():
    assert server._check_order_size("spot", "BTCUSDT", "Buy", "Market", "10", None) is None


def test_spot_limit_buy_notional_over_cap():
    # 0.01 * 50000 = 500 USDT > 100 cap
    err = server._check_order_size("spot", "BTCUSDT", "Buy", "Limit", "0.01", "50000")
    assert err is not None and "exceeds" in err["error"]


def test_futures_with_price_over_cap():
    # 0.1 * 50000 = 5000 USDT > 100 cap
    err = server._check_order_size("linear", "BTCUSDT", "Buy", "Market", "0.1", "50000")
    assert err is not None


def test_invalid_qty():
    err = server._check_order_size("spot", "BTCUSDT", "Buy", "Market", "abc", None)
    assert err is not None and "Invalid qty" in err["error"]
