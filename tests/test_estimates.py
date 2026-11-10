import pytest
from engine.estimates import estimate_strategy
from engine.strategies import STRATEGIES
from app import strategy_comparison_pool


def test_optional_stats_and_rate_scale():
    s=next(s for s in STRATEGIES if s['pool']=='basic_water' and s['style']!='squid' and strategy_comparison_pool(s))
    market={'live':True,'products':{'RAW_FISH':{'instant_sell':10,'instant_buy':12}}}
    a=estimate_strategy(s,strategy_comparison_pool(s),market,catches_per_hour=500,magic_find=25)
    b=estimate_strategy(s,strategy_comparison_pool(s),market,catches_per_hour=1000,magic_find=25)
    assert a['status']=='estimated'
    assert a['assumptions']['magic_find']==25
    assert b['coins_per_hour']==pytest.approx(a['coins_per_hour']*2)
    assert a['low'] < a['coins_per_hour'] < a['high']
    assert 'creatures' not in a


def test_no_fabricated_estimates():
    assert estimate_strategy({},None,{'live':True})['status']=='unsupported'
    assert estimate_strategy({}, {'pool':'basic_water'}, {'live':False})['status']=='market_unavailable'
