"""Actual documented-pool tests, not self-fulfilling model tests only."""
import math
import pytest
from engine.pools import POOLS,DROPS,catalog_summary,public_catalog,rarity_weighted_pool,project_pool
from engine.models import squid_share
from fastapi.testclient import TestClient
from app import app

client=TestClient(app)

@pytest.mark.parametrize('id, expected_names, expected_total',[
 ('basic_water',10,4296),('bayou',6,10000),('lotus',6,10000),
 ('moonglade',6,10000),('torrhus',6,10000),('crimson_lava',9,4648),
 ('hotspot_water',6,10000),('hotspot_lava',6,10000)
])
def test_wiki_pool_sizes_weights(id,expected_names,expected_total):
    items=POOLS[id]['creatures']
    assert len(items)==expected_names
    assert sum(c.base_weight for c in items)==expected_total

@pytest.mark.parametrize('pool_id',list(POOLS))
def test_probabilities_normalized_at_fishing50(pool_id):
    items=rarity_weighted_pool(pool_id,tracking=30,bait='LIGHT_BAIT',time_of_day='day',common_hook=False) if False else rarity_weighted_pool(pool_id,tracking=30,bait='LIGHT_BAIT',time_of_day='day')
    assert sum(m['probability'] for m in items)==pytest.approx(1)
    assert all(0<m['probability']<=1 for m in items)

def test_birch_squid_and_hook_use_exact_other_common_weight():
    plain=rarity_weighted_pool('basic_water')
    squid=next(x for x in plain if x['name']=='Squid')
    assert squid['probability']==pytest.approx(1200/4296)
    withhook=rarity_weighted_pool('basic_water',hook='COMMON_HOOK',squid_hat=True)
    squid_withhook=next(x for x in withhook if x['name']=='Squid')
    assert squid_withhook['modified_weight']==3000
    assert squid_withhook['probability']==pytest.approx(squid_share(squid_hat=True,common_hook=True,other_common_weight=800))

def test_tracking_renormalizes_entire_pool():
    no=rarity_weighted_pool('bayou',tracking=0)
    yes=rarity_weighted_pool('bayou',tracking=100)
    titan0=next(x for x in no if x['name']=='Titanoboa')
    titan1=next(x for x in yes if x['name']=='Titanoboa')
    assert titan1['modified_weight']==50
    assert titan1['probability']>titan0['probability']
    trash0=next(x for x in no if x['name']=='Trash Gobbler')
    trash1=next(x for x in yes if x['name']=='Trash Gobbler')
    assert trash1['modified_weight']==trash0['modified_weight']==5000
    assert trash1['probability']<trash0['probability']

def test_light_day_dark_night_modifiers():
    plain=rarity_weighted_pool('bayou',bait='NONE')
    night_light=rarity_weighted_pool('bayou',bait='LIGHT_BAIT',time_of_day='night')
    day_light=rarity_weighted_pool('bayou',bait='LIGHT_BAIT',time_of_day='day')
    night_dark=rarity_weighted_pool('bayou',bait='DARK_BAIT',time_of_day='night')
    wt=lambda x:next(m['modified_weight'] for m in x if m['name']=='Titanoboa')
    assert wt(plain)==wt(night_light)==25
    assert wt(day_light)==wt(night_dark)==31.25
    # Base weight of 400 is NOT boosted.
    pyro=rarity_weighted_pool('crimson_lava',bait='LIGHT_BAIT',time_of_day='day')
    assert next(x['modified_weight'] for x in pyro if x['name']=='Pyroclastic Worm')==400

def test_puddle_jumper_hook_specific_only():
    p=rarity_weighted_pool('lotus',hook='PUDDLE_JUMPER_HOOK')
    assert next(x['modified_weight'] for x in p if x['name']=='Puddle Jumper')==500
    assert next(x['modified_weight'] for x in p if x['name']=='Frog Prince')==25

def test_fishing_unlocks_and_jawbus_trophy_gate():
    base=rarity_weighted_pool('crimson_lava',fishing_level=45,novice_trophy_fisher=False,adept_trophy_fisher=False)
    assert 'Thunder' not in [c['name'] for c in base]
    assert 'Lord Jawbus' not in [c['name'] for c in base]
    low=rarity_weighted_pool('crimson_lava',fishing_level=35)
    assert 'Thunder' not in [c['name'] for c in low]
    assert 'Lord Jawbus' not in [c['name'] for c in low]
    assert 'Taurus' in [c['name'] for c in low]

def test_hotspot_mix_is_not_100pct_hotspot():
    a=project_pool({'pool':'hotspot_water','base_pool':'bayou','hotspot_override_percent':85,'reels_per_hour':1000,'double_hook_chance':0}, {})
    rows={x['name']:x for x in a['creatures']}
    assert len(rows)==12
    assert sum(x['probability'] for x in rows.values())==pytest.approx(1)
    assert sum(x['probability'] for x in rows.values() if x['name'] in ('Frog Man','Inkling','Snapping Turtle','Manta Ray','Blue Ringed Octopus','Wiki Tiki'))==pytest.approx(.85)
    assert rows['Wiki Tiki']['expected_per_hour']==pytest.approx(1000*.85*.0025)
    assert rows['Titanoboa']['expected_per_hour']==pytest.approx(1000*.15*.0025)

def test_hotspot_max_85_and_liquid_compatibility():
    with pytest.raises(ValueError):project_pool({'pool':'hotspot_water','hotspot_override_percent':100},{})
    with pytest.raises(ValueError):project_pool({'pool':'hotspot_water','base_pool':'crimson_lava'},{})

def test_accurate_thunder_flash_drops_included_and_unpriced():
    result=project_pool({'pool':'crimson_lava','reels_per_hour':1000,'double_hook_chance':0,'tracking':0,'bait':'NONE'}, {})
    thunder=next(x for x in result['creatures'] if x['name']=='Thunder')
    flash=next(x for x in thunder['drops'] if x['name']=='Flash I book')
    assert flash['base_chance']==pytest.approx(.015)
    assert flash['expected_units']==pytest.approx(thunder['expected_per_hour']*.015)
    assert flash['expected_coins'] is None
    assert any(x['drop']=='Flash I book' for x in result['unpriced'])

def test_wiki_tiki_mask_drop_base_probability():
    mask=next(x for x in DROPS['Wiki Tiki']['drops'] if x['name']=='Tiki Mask')
    assert mask['chance']==pytest.approx(.001)

def test_manual_market_prices_distinct_from_verified_live():
    result=project_pool({'pool':'basic_water','reels_per_hour':1000,'double_hook_chance':0,'bait':'NONE',
                        'manual_item_prices':{'Squid Boots':1000000}},
                       {'INK_SACK':{'instant_sell':3000,'instant_buy':3200}},prices_live=False)
    squid=next(x for x in result['creatures'] if x['name']=='Squid')
    boots=next(x for x in squid['drops'] if x['name']=='Squid Boots')
    assert boots['price_source']=='manual-unverified'
    assert boots['expected_coins'] == pytest.approx(boots['expected_units']*1000000)
    assert result['is_full_method_profit'] is False
    assert result['unpriced']
    assert result['unmodelled']

def test_missing_bait_price_never_says_zero_cost():
    result=project_pool({'pool':'bayou','bait':'HOTSPOT_BAIT','reels_per_hour':500}, {})
    assert result['bait_cost'] is None
    assert result['known_subtotal_after_bait'] is None

def test_bait_cost_instant_buy_and_saved():
    result=project_pool({'pool':'bayou','bait':'HOTSPOT_BAIT','reels_per_hour':500,
                         'bait_saved_percent':20}, {'HOTSPOT_BAIT':{'instant_sell':2,'instant_buy':10}},prices_live=True)
    assert result['bait_cost']==pytest.approx(500*.8*10)

def test_rare_and_jackpot_not_double_counted():
    p={'pool':'hotspot_water','base_pool':'bayou','hotspot_override_percent':85,
       'reels_per_hour':1000,'double_hook_chance':0,
       'manual_item_prices':{'Tiki Mask':100000000,'Blue Ring':1000}}
    r=project_pool(p,{})
    assert r['known_jackpot_base_ev']>0
    assert r['known_subtotal']==pytest.approx(r['known_common_revenue']+r['known_rare_base_ev'])
    assert r['known_subtotal_after_bait']==pytest.approx(r['known_subtotal'])
    assert r['known_subtotal']<r['known_subtotal']+r['known_jackpot_base_ev']

def test_event_methods_are_not_sneaked_in():
    names=' '.join(n['name'] for n in public_catalog()['pools'])
    assert 'Shark Festival' not in names
    assert 'Spooky Festival' not in names

def test_catalog_source_metadata_and_missing_creatures():
    summary=catalog_summary()
    assert summary['anytime_pools']==8
    assert summary['creatures']==55
    assert summary['creature_drop_tables']==18
    assert summary['drop_items']==99
    assert summary['source'].startswith('https://')
    assert all(x['source'].startswith('https://') for pool in public_catalog()['pools'] for x in pool['creatures'])

def test_pool_api_and_projection_api():
    cat=client.get('/api/pools');assert cat.status_code==200
    assert cat.json()['summary']['creatures']==55
    res=client.post('/api/pools/project',json={'use_live_market':False,'params':{'pool':'bayou','reels_per_hour':100}})
    assert res.status_code==200
    assert res.json()['is_full_method_profit'] is False
    assert len(res.json()['creatures'])==6
    bad=client.post('/api/pools/project',json={'use_live_market':False,'params':{'pool':'bad'}})
    assert bad.status_code==422


def test_bayou_core_loot_tables_are_present_and_sourced():
    names=[c.name for c in POOLS['bayou']['creatures']]
    assert all(n in DROPS for n in names)
    assert all(DROPS[n]['source'].startswith('https://') for n in names)
    sludge=DROPS['Bayou Sludge']['drops']
    blessing=next(x for x in sludge if x['name']=='Blessing VI enchanted book')
    assert blessing['chance']==pytest.approx(.001)
    assert 'Sludglings' in DROPS['Bayou Sludge']['note']

def test_inkling_hotspot_drops_and_weight_with_squid_hat():
    drops=DROPS['Inkling']['drops']
    assert next(x for x in drops if x['name']=='Ink Splat')['chance']==pytest.approx(.04)
    no=rarity_weighted_pool('hotspot_water')
    yes=rarity_weighted_pool('hotspot_water',squid_hat=True)
    a=next(x for x in no if x['name']=='Inkling')
    b=next(x for x in yes if x['name']=='Inkling')
    assert b['modified_weight']==2*a['modified_weight']
    assert b['probability']>a['probability']
