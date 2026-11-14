import pytest
from engine.market import Bazaar

PRODUCT = {
    'quick_status': {'sellPrice': 90, 'buyPrice': 120},
    'buy_summary': [{'pricePerUnit': 100, 'amount': 2}, {'pricePerUnit': 90, 'amount': 3}],
    'sell_summary': [{'pricePerUnit': 110, 'amount': 2}, {'pricePerUnit': 120, 'amount': 3}],
}

def test_depth_quote_from_live_market():
    b = Bazaar(fetcher=lambda: {'success': True, 'lastUpdated': 1000000, 'products': {'INK_SACK:3': PRODUCT}}, clock=lambda: 1000)
    result = b.depth_quote('INK_SACK:3', 3, 'instant_sell')
    assert result['total_coins'] == 290
    assert result['unit_price'] == pytest.approx(290/3)

def test_depth_quote_does_not_use_stale_snapshot():
    b = Bazaar(fetcher=lambda: {'success': True, 'lastUpdated': 100000, 'products': {'INK_SACK:3': PRODUCT}}, clock=lambda: 1000)
    with pytest.raises(ValueError, match='Fresh'):
        b.depth_quote('INK_SACK:3', 3, 'instant_sell')

def test_depth_quote_rejects_insufficient_depth():
    b = Bazaar(fetcher=lambda: {'success': True, 'lastUpdated': 1000000, 'products': {'INK_SACK:3': PRODUCT}}, clock=lambda: 1000)
    with pytest.raises(ValueError, match='depth'):
        b.depth_quote('INK_SACK:3', 6, 'instant_sell')

def test_depth_quote_rejects_missing_product():
    b = Bazaar(fetcher=lambda: {'success': True, 'lastUpdated': 1000000, 'products': {'INK_SACK:3': PRODUCT}}, clock=lambda: 1000)
    with pytest.raises(ValueError, match='absent'):
        b.depth_quote('MISSING', 1, 'instant_buy')
