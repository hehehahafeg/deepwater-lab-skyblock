import pytest
from engine.market import Bazaar, parse_bazaar_product, TTL_SECONDS

PROD={'quick_status':{'buyPrice':2945.1,'sellPrice':2600.2,'buyVolume':111,'sellVolume':222}}


def test_hypixel_sell_price_means_player_instant_sell():
    assert parse_bazaar_product(PROD)['instant_sell']==2600.2
    assert parse_bazaar_product(PROD)['instant_buy']==2945.1

@pytest.mark.parametrize('quick', [None,{}, {'buyPrice':0,'sellPrice':1}, {'buyPrice':-1,'sellPrice':5},
  {'buyPrice':float('nan'),'sellPrice':5}, {'buyPrice':12,'sellPrice':float('inf')}, {'buyPrice':'x','sellPrice':2}])
def test_bogus_products_rejected(quick):
    with pytest.raises((ValueError,KeyError,TypeError)):
        parse_bazaar_product({'quick_status':quick})


def test_cache_has_three_minute_ttl():
    counter=[0]
    clock=[1000]
    def fake():
        counter[0]+=1
        return {'success':True,'lastUpdated':1700000000000,'products':{'INK_SACK':PROD}}
    b=Bazaar(fetcher=fake,clock=lambda:clock[0]);a=b.get();assert a['state']=='live';assert counter==[1]
    clock[0]+=5;second=b.get();assert second['state']=='live-cache';assert counter==[1]
    clock[0]+=TTL_SECONDS+1;b.get();assert counter==[2]


def test_failure_does_not_invent_prices():
    b=Bazaar(fetcher=lambda: (_ for _ in()).throw(ValueError('blocked')),clock=lambda:1000)
    r=b.get();assert r['state']=='unavailable';assert r['products']=={} and not r['live']


def test_failure_keeps_cache_but_marks_unverified():
    call=[0];clock=[100]
    def fetch():
        call[0]+=1
        if call[0]==1:return {'success':True,'products':{'INK_SACK':PROD}}
        raise ValueError('outage')
    b=Bazaar(fetcher=fetch,clock=lambda:clock[0]);assert b.get()['live']
    clock[0]=1000;r=b.get();assert r['state']=='stale' and not r['live']
    assert r['products']['INK_SACK']['instant_sell']==2600.2


def test_bad_success_payload_does_not_count_live():
    b=Bazaar(fetcher=lambda:{'success':False,'products':{'INK_SACK':PROD}})
    assert b.get()['live'] is False


def test_invalid_items_skipped():
    b=Bazaar(fetcher=lambda:{'success':True,'products':{'INK_SACK':PROD,'FAKE':{'quick_status':{}}}})
    r=b.get();assert r['product_count']==1 and 'FAKE' not in r['products']


def test_realistic_live_snapshot_does_not_invert_player_spread():
    # Reproduces the observed Nov 10 2026 screenshot before the fix.
    ink = parse_bazaar_product({'quick_status':{'buyPrice':3071,'sellPrice':2975}})
    bait = parse_bazaar_product({'quick_status':{'buyPrice':548,'sellPrice':289}})
    assert ink == {'instant_sell':2975.0, 'instant_buy':3071.0,
                   'buy_volume':None, 'sell_volume':None}
    assert bait['instant_buy']==548.0
    assert ink['instant_buy'] - ink['instant_sell'] == 96.0
    assert bait['instant_buy'] - bait['instant_sell'] == 259.0

def test_market_payload_matches_player_perspective_and_costs():
    from engine.models import calculate_squid
    b=Bazaar(fetcher=lambda:{'success':True,'products':{
        'INK_SACK':{'quick_status':{'buyPrice':3071,'sellPrice':2975}},
        'WATER_LILY':{'quick_status':{'buyPrice':37,'sellPrice':8}},
        'FISH_BAIT':{'quick_status':{'buyPrice':548,'sellPrice':289}},
    }})
    market=b.get()['products']
    assert market['INK_SACK']['instant_sell']==2975
    assert market['FISH_BAIT']['instant_buy']==548
    r=calculate_squid({'rain':False,'reels_per_hour':100,'bait':'FISH_BAIT','bait_saved_percent':0},market,prices_live=True)
    assert r['cost_bait']==54800
    assert r['gross_ink']==r['ink_per_hour']*2975
