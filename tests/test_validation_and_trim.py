"""Tests for validate_order, response trimming, and market_snapshot (no live API)."""

import server
import service

# --- validate_order -------------------------------------------------------

def _fake_instrument(monkeypatch, status="Trading", min_qty="0.001"):
    payload = {
        "retCode": 0,
        "result": {"list": [{"status": status, "lotSizeFilter": {"minOrderQty": min_qty}}]},
    }
    monkeypatch.setattr(server.bybit_service, "get_instruments_info", lambda *a, **k: payload)


def test_validate_order_ok(monkeypatch):
    _fake_instrument(monkeypatch)
    res = server.validate_order("spot", "BTCUSDT", "Buy", "Limit", "0.001", "50", "1")
    assert res["valid"] is True
    assert res["errors"] == []


def test_validate_order_missing_price_for_limit(monkeypatch):
    _fake_instrument(monkeypatch)
    res = server.validate_order("spot", "BTCUSDT", "Buy", "Limit", "0.001", None, None)
    assert res["valid"] is False
    assert any("price is required" in e for e in res["errors"])


def test_validate_order_futures_requires_position_idx(monkeypatch):
    _fake_instrument(monkeypatch)
    res = server.validate_order("linear", "BTCUSDT", "Buy", "Limit", "0.001", "50", None)
    assert res["valid"] is False
    assert any("positionIdx" in e for e in res["errors"])


def test_validate_order_unknown_symbol(monkeypatch):
    monkeypatch.setattr(server.bybit_service, "get_instruments_info",
                        lambda *a, **k: {"retCode": 0, "result": {"list": []}})
    res = server.validate_order("spot", "FAKEUSDT", "Buy", "Limit", "0.001", "50", "1")
    assert res["valid"] is False
    assert any("not found" in e for e in res["errors"])


def test_validate_order_size_cap(monkeypatch):
    _fake_instrument(monkeypatch)
    res = server.validate_order("spot", "BTCUSDT", "Buy", "Limit", "1", "50000", "1")
    assert res["valid"] is False
    assert any("exceeds" in e for e in res["errors"])


# --- trim_response --------------------------------------------------------

def _ticker_payload():
    return {
        "retCode": 0,
        "result": {"list": [{
            "symbol": "BTCUSDT", "lastPrice": "50000", "bid1Price": "49999",
            "ask1Price": "50001", "price24hPcnt": "0.01", "volume24h": "100",
            "extraNoise": "drop-me", "anotherField": "drop-me-too",
        }]},
    }


def test_trim_response_minimal(monkeypatch):
    monkeypatch.setattr(service, "RESPONSE_VERBOSITY", "minimal")
    out = service.trim_response(_ticker_payload(), "tickers")
    row = out["result"]["list"][0]
    assert "extraNoise" not in row and "anotherField" not in row
    assert row["symbol"] == "BTCUSDT" and row["lastPrice"] == "50000"


def test_trim_response_normal_is_untouched(monkeypatch):
    monkeypatch.setattr(service, "RESPONSE_VERBOSITY", "normal")
    out = service.trim_response(_ticker_payload(), "tickers")
    assert "extraNoise" in out["result"]["list"][0]


def test_trim_response_unknown_kind_untouched(monkeypatch):
    monkeypatch.setattr(service, "RESPONSE_VERBOSITY", "minimal")
    out = service.trim_response(_ticker_payload(), "unknown")
    assert "extraNoise" in out["result"]["list"][0]


# --- market_snapshot isolates per-section failures ------------------------

def test_market_snapshot_section_isolation(monkeypatch):
    svc = service.BybitService.__new__(service.BybitService)  # skip __init__/HTTP
    monkeypatch.setattr(svc, "get_orderbook", lambda *a, **k: {"retCode": 0, "result": {"b": []}}, raising=False)
    monkeypatch.setattr(svc, "get_tickers", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")), raising=False)
    monkeypatch.setattr(svc, "get_kline", lambda *a, **k: {"retCode": 0, "result": {"list": []}}, raising=False)
    monkeypatch.setattr(svc, "get_instruments_info", lambda *a, **k: {"retCode": 0, "result": {}}, raising=False)
    monkeypatch.setattr(svc, "get_public_trade_history", lambda *a, **k: {"retCode": 0, "result": {}}, raising=False)

    snap = svc.market_snapshot("spot", "BTCUSDT")
    assert snap["symbol"] == "BTCUSDT"
    assert "error" in snap["ticker"]          # failing section captured
    assert "error" not in snap["orderbook"]   # others still succeed
