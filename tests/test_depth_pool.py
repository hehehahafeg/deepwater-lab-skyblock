import pytest
from engine.pools import project_pool

def test_depth_pool_aggregates_identical_drop_ids_and_changes_revenue():
    prices = {'WATER_LILY': {'instant_sell': 100, 'instant_buy': 120}}
    books = {'WATER_LILY': {'buy_summary': [
        {'pricePerUnit': 100, 'amount': 1},
        {'pricePerUnit': 10, 'amount': 100000}
    ]}}
    params = {'pool': 'basic_water', 'reels_per_hour': 100,
              'sea_creature_chance': 100, 'double_hook_chance': 0, 'bait': 'NONE'}
    baseline = project_pool(params, prices, prices_live=True)
    depth = project_pool(params, prices, prices_live=True, order_books=books, depth_pricing=True)
    assert depth['depth_pricing'] is True
    assert depth['known_subtotal'] < baseline['known_subtotal']
    lily_drops = [d for mob in depth['creatures'] for d in mob['drops'] if d['market_id']=='WATER_LILY']
    assert len(lily_drops)>1
    assert len({d['unit_price'] for d in lily_drops}) == 1

def test_depth_pool_refuses_insufficient_order_depth():
    prices = {'WATER_LILY': {'instant_sell': 100, 'instant_buy': 120}}
    books = {'WATER_LILY': {'buy_summary': [{'pricePerUnit': 100, 'amount': 1}]}}
    with pytest.raises(ValueError, match='depth'):
        project_pool({'pool':'basic_water','reels_per_hour':100}, prices,
                     prices_live=True, order_books=books, depth_pricing=True)

def test_depth_pool_requires_live_snapshot():
    with pytest.raises(ValueError, match='fresh'):
        project_pool({'pool':'basic_water'}, {}, prices_live=False,
                     order_books={}, depth_pricing=True)

def test_depth_pool_uses_instant_buy_for_bait():
    prices = {'FISH_BAIT': {'instant_sell': 1, 'instant_buy': 10}}
    books = {'FISH_BAIT': {'sell_summary': [
        {'pricePerUnit': 10, 'amount': 1},
        {'pricePerUnit': 20, 'amount': 10000}
    ]}}
    params = {'pool':'basic_water','reels_per_hour':100,'bait':'FISH_BAIT'}
    baseline = project_pool(params, prices, prices_live=True)
    depth = project_pool(params, prices, prices_live=True, order_books=books, depth_pricing=True)
    assert depth['bait_cost'] > baseline['bait_cost']

def test_depth_pool_rejects_manual_bait_price_without_live_bazaar_quote():
    with pytest.raises(ValueError, match='manual bait prices'):
        project_pool({'pool':'basic_water','reels_per_hour':100,'bait':'FISH_BAIT',
                      'manual_bait_price': 5}, {}, prices_live=True,
                     order_books={}, depth_pricing=True)

def test_depth_pool_rejects_missing_bait_quote():
    with pytest.raises(ValueError, match='live Bazaar bait price'):
        project_pool({'pool':'basic_water','reels_per_hour':100,'bait':'FISH_BAIT'},
                     {}, prices_live=True, order_books={}, depth_pricing=True)

def test_manual_bait_source_is_explicit_in_non_depth_projection():
    result = project_pool({'pool':'basic_water','reels_per_hour':100,
                           'bait':'FISH_BAIT','manual_bait_price':5}, {},
                          prices_live=True)
    assert result['bait_price_source'] == 'manual-unverified'
    assert result['bait_cost'] > 0
