import pytest
from fastapi.testclient import TestClient
from engine.strategies import STRATEGIES, BY_ID, list_strategies, market_observations
from engine.pools import POOLS
from app import app, market

client=TestClient(app)

@pytest.fixture(autouse=True)
def mock_market(monkeypatch):
    monkeypatch.setattr(market,'get',lambda **_: {'live':True, 'products':{
        'INK_SACK':{'instant_sell':2975.,'instant_buy':3071.},
        'FISH_BAIT':{'instant_sell':289.,'instant_buy':548.},
        'ENCHANTED_INK_SACK':{'instant_sell':124091.,'instant_buy':144422.},
    }})

def test_at_least_hundred_distinct_entries():
    assert len(STRATEGIES)>=100
    assert len(STRATEGIES)==len(BY_ID)

def test_default_filter_is_anytime_only():
    result=list_strategies()
    assert result['count']>=100
    assert all(s['availability']=='anytime' for s in result['items'])
    assert result['count']<len(STRATEGIES)

def test_events_are_explicit_opt_in():
    assert list_strategies(availability='event-only')['count']>=3
    assert list_strategies(availability='all')['count']==len(STRATEGIES)

def test_all_pool_creatures_covered_by_a_profile():
    targets={s['target'] for s in STRATEGIES}
    assert all(c.name in targets for p in POOLS.values() for c in p['creatures'])

def test_every_profile_has_all_necessary_fields_and_no_fake_money():
    required=['armor','rod','hook','line','sinker','bait','casting_pet','reeling_pet',
              'kill_pet','weapon','equipment','enchants','stats','autopet']
    for s in STRATEGIES:
        assert all(s['best_documented_setup'].get(k) for k in required),s['id']
        assert len(s['tutorial'])>=4
        assert s['sources'] and all(u.startswith('https://') for u in s['sources'])
        assert not s['global_hypermax_verified']
        assert s['profit_per_hour'] is None
        assert not s['experiment']['verified']
        assert s['confidence']=='mechanics-partial'

def test_hound_wiki_tiki_hypothesis_is_explicitly_unverified():
    s=BY_ID['bayou--wiki-tiki-hound-finder-experiment']
    assert 'Hound' in s['experiment']['name']
    assert 'not' in s['experiment']['reason'].lower()
    assert 'GDrag' in s['best_documented_setup']['kill_pet']
    assert s['profit_per_hour'] is None

def test_user_rejected_crimson_route_kept_but_filtered_out_when_requested():
    rejected=BY_ID['crimson-isle--full-rotation-lava-hotspots']
    assert rejected['status']=='effort-rejected'
    assert rejected['movement']=='long-route'
    assert not any(x['id']==rejected['id'] for x in list_strategies(show_washed=False)['items'])

def test_wooden_treasure_method_uses_treasure_hook():
    s=BY_ID['crystal-hollows--silentdepth-wooden-bait']
    assert 'Treasure Hook' in s['best_documented_setup']['hook']
    assert 'NO' not in s['profit_status'].upper() or s['profit_per_hour'] is None

def test_crimson_has_350_speed_cap_and_no_unobtainable_looting_vii():
    s=BY_ID['crimson-isle--thunder-flash-i-books']
    assert '350' in s['best_documented_setup']['stats']
    assert 'Looting V' in s['best_documented_setup']['enchants']
    assert 'Looting VII' not in str(s)

def test_park_has_300_speed_cap_and_squid_hat():
    s=BY_ID['birch-park--rain-squid--natural-spawns']
    assert 'Squid Hat' in s['best_documented_setup']['armor']
    assert '300' in s['best_documented_setup']['stats']

def test_market_context_price_is_observation_and_rare_unknown_remains_unknown():
    s=BY_ID['the-park--target-squid']
    result=market_observations(s,{'INK_SACK':{'instant_sell':2975}},live=True)
    ink=next(x for x in result['item_prices'] if x['item']=='Ink Sac')
    assert ink['instant_sell']==2975
    assert result['estimated_profit_per_hour'] is None
    assert any(x['instant_sell'] is None for x in result['item_prices'])

def test_url_library_endpoint_and_filters():
    r=client.get('/api/strategies')
    assert r.status_code==200
    assert r.json()['count']==100
    assert len(r.json()['items'])==100
    assert client.get('/api/strategies?availability=all').json()['count']==len(STRATEGIES)
    assert client.get('/api/strategies?query=Hound').json()['count']>=1
    assert client.get('/api/strategies?effort=high').json()['count']>=0

def test_detail_returns_complete_loadout_and_live_prices():
    r=client.get('/api/strategies/the-park--target-squid')
    assert r.status_code==200
    obj=r.json()
    assert obj['strategy']['best_documented_setup']['rod']
    assert obj['market_observations']['market_live']
    assert obj['market_observations']['estimated_profit_per_hour'] is None

def test_unknown_strategy_is_404_and_invalid_queries_422():
    assert client.get('/api/strategies/this-does-not-exist').status_code==404
    assert client.get('/api/strategies?availability=tomorrow').status_code==422
    assert client.get('/api/strategies?limit=0').status_code==422
    assert client.get('/api/strategies?limit=10000').status_code==422

@pytest.mark.parametrize('q', ['Wiki Tiki','Squid','water','Crimson','Hound'])
def test_keyword_search_case_insensitive(q):
    assert list_strategies(query=q)['count']==list_strategies(query=q.upper())['count']

def test_every_location_has_correct_regional_fishing_speed_cap():
    from engine.strategies import regional_speed_cap
    assert regional_speed_cap('Backwater Bayou')==200
    assert regional_speed_cap('Lotus Atoll')==250
    assert regional_speed_cap('Crimson Isle')==350
    assert regional_speed_cap('The Park')==300
    assert regional_speed_cap('Water Hotspots') is None
    for s in STRATEGIES:
        expected=regional_speed_cap(s['region'])
        assert s['fishing_speed_cap']==expected,s['name']
        displayed=s['best_documented_setup']['stats']
        assert (str(expected)+' Fishing Speed cap' if expected is not None else 'Underlying island cap') in displayed,s['name']
        assert s['fishing_speed_cap_source'].endswith('Fishing_Speed')

@pytest.mark.parametrize('strategy_id,rod_fragment,cap', [
    ('crimson-isle--fire-eel-taurus-captures','Hellfire',350),
    ('lotus-atoll--trophy-frog-shard-handling','Rod of the Sea',250),
    ('galatea--tadgang-shard-capture','Rod of the Sea',300),
])
def test_hunting_loadout_preserves_liquid_and_capture_gear(strategy_id,rod_fragment,cap):
    s=BY_ID[strategy_id]
    setup=s['best_documented_setup']
    assert s['fishing_speed_cap']==cap
    assert rod_fragment in setup['rod']
    assert 'Hunting' in setup['equipment']
    assert 'capture' in setup['autopet'].lower()
    assert 'Hunting Fortune' in setup['stats']
    assert 'kill-only' in setup['weapon']
