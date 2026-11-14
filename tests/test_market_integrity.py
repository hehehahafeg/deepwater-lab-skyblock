import pytest
from engine.market_integrity import validate_snapshot, executable_quote

def test_fresh_snapshot():
    payload = {"success": True, "lastUpdated": 1_000_000, "products": {"INK_SACK:3": {}}}
    assert "INK_SACK:3" in validate_snapshot(payload, now=1000)

def test_stale_snapshot_blocked():
    with pytest.raises(ValueError, match="stale"):
        validate_snapshot({"success": True, "lastUpdated": 1_000_000, "products": {"A": {}}}, now=2000)

def test_missing_timestamp_blocked():
    with pytest.raises(ValueError, match="timestamp"):
        validate_snapshot({"success": True, "products": {"A": {}}}, now=1000)

def test_correct_market_direction_and_depth():
    products = {"INK_SACK:3": {
        "buy_summary": [{"pricePerUnit": 100, "amount": 2}, {"pricePerUnit": 90, "amount": 5}],
        "sell_summary": [{"pricePerUnit": 110, "amount": 3}, {"pricePerUnit": 120, "amount": 5}]}}
    assert executable_quote(products, "INK_SACK:3", 3, "instant_sell")["total_coins"] == 290
    assert executable_quote(products, "INK_SACK:3", 4, "instant_buy")["total_coins"] == 450

def test_depth_shortfall_blocked():
    with pytest.raises(ValueError, match="depth"):
        executable_quote({"A": {"buy_summary": [{"pricePerUnit": 100, "amount": 2}]}},
                         "A", 3, "instant_sell")

def test_invalid_values_blocked():
    with pytest.raises(ValueError):
        executable_quote({"A": {"buy_summary": [{"pricePerUnit": 0, "amount": 2}]}},
                         "A", 1, "instant_sell")
