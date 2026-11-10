import math
import pytest
from engine.models import (
    SQUID_WEIGHT, BASE_OTHER_WEIGHT, BASE_SQUID_CHANCE,
    squid_share, calculate_squid, sensitivity, rank_methods, payback_hours,
)

PRICES = {'INK_SACK':{'instant_sell':10,'instant_buy':11},
          'WATER_LILY':{'instant_sell':2,'instant_buy':3},
          'FISH_BAIT':{'instant_sell':4,'instant_buy':8},
          'SPIKED_BAIT':{'instant_sell':9,'instant_buy':12}}


def test_baseline_squid_chance():
    assert squid_share(squid_hat=False,common_hook=False)==pytest.approx(1200/4296)

def test_squid_hat_increases_relative_weight():
    plain=squid_share(squid_hat=False,common_hook=False)
    hat=squid_share(squid_hat=True,common_hook=False)
    assert hat == pytest.approx(2400/(2400+BASE_OTHER_WEIGHT))
    assert hat>plain

def test_common_hook_increases_other_common_too():
    with_hook=squid_share(squid_hat=True,common_hook=True,other_common_weight=800)
    naive=3000/(3000+BASE_OTHER_WEIGHT)
    assert with_hook < naive
    assert with_hook > squid_share(squid_hat=True,common_hook=False,other_common_weight=800)

def test_common_hook_whole_common_pool_cancels_relative_share():
    a=squid_share(squid_hat=True,common_hook=True,other_common_weight=BASE_OTHER_WEIGHT)
    b=squid_share(squid_hat=True,common_hook=False)
    assert a==pytest.approx(b)

def test_no_reels_no_rain_no_catches():
    r=calculate_squid({'reels_per_hour':0,'rain':False,'bait':'NONE'},PRICES,prices_live=True)
    assert r['modelled_net']==0
    assert r['ink_per_hour']==0
    assert r['natural_squids_per_hour']==0

def test_natural_spawn_ceiling():
    r=calculate_squid({'reels_per_hour':0,'rain':True,'pay_rain':False,'natural_spawn_efficiency':100,'bait':'NONE'},PRICES)
    assert r['natural_squids_per_hour']==pytest.approx(3600/11*(2/3)*1.5)

def test_zero_scc_means_no_fished_squid():
    r=calculate_squid({'sea_creature_chance':0,'rain':False},PRICES)
    assert r['fished_squids_per_hour']==0

def test_double_hook_100_doubles_output():
    p={'rain':False,'reels_per_hour':500,'sea_creature_chance':100,'bait':'NONE'}
    a=calculate_squid({**p,'double_hook_chance':0},PRICES)
    b=calculate_squid({**p,'double_hook_chance':100},PRICES)
    assert b['ink_per_hour']==pytest.approx(a['ink_per_hour']*2)

def test_level_100_squid_pet_doubles_drops_only():
    p={'rain':False,'reels_per_hour':500,'bait':'NONE'}
    a=calculate_squid({**p,'squid_pet':False},PRICES)
    b=calculate_squid({**p,'squid_pet':True},PRICES)
    assert b['ink_per_hour']==pytest.approx(2*a['ink_per_hour'])
    assert b['fished_squids_per_hour']==a['fished_squids_per_hour']

def test_profit_math_uses_instant_sell_and_instant_buy():
    r=calculate_squid({'rain':False,'reels_per_hour':100,'bait':'FISH_BAIT','bait_saved_percent':10},PRICES,prices_live=True)
    assert r['cost_bait']==pytest.approx(90*8)
    assert r['modelled_net']==pytest.approx(r['ink_per_hour']*10+r['lily_pads_per_hour']*2-90*8)

def test_missing_ink_price_blocks_net():
    r=calculate_squid({'rain':False}, {'WATER_LILY':PRICES['WATER_LILY'],'FISH_BAIT':PRICES['FISH_BAIT']})
    assert r['modelled_net'] is None
    assert r['price_complete'] is False
    assert any('INK_SACK' in v for v in r['missing'])

def test_missing_bait_price_blocks_net():
    r=calculate_squid({'rain':False}, {'INK_SACK':PRICES['INK_SACK'],'WATER_LILY':PRICES['WATER_LILY']})
    assert r['modelled_net'] is None
    assert any('FISH_BAIT' in v for v in r['missing'])

def test_no_bait_no_bait_price_required():
    r=calculate_squid({'rain':False,'bait':'NONE'}, {'INK_SACK':PRICES['INK_SACK'],'WATER_LILY':PRICES['WATER_LILY']})
    assert r['modelled_net'] is not None
    assert r['cost_bait']==0

def test_rain_cost():
    paid=calculate_squid({'reels_per_hour':0,'rain':True,'pay_rain':True,'bait':'NONE'},PRICES)
    free=calculate_squid({'reels_per_hour':0,'rain':True,'pay_rain':False,'bait':'NONE'},PRICES)
    assert paid['cost_rain']==300000
    assert free['cost_rain']==0
    assert free['modelled_net']-paid['modelled_net']==300000

@pytest.mark.parametrize('field,invalid', [
  ('reels_per_hour',-1),('reels_per_hour',100000),('sea_creature_chance',101),
  ('double_hook_chance',float('nan')),('double_hook_chance',float('inf')),
  ('bait_saved_percent',-1),('fishing_level',51),('tracking',301),('hydra_kills_per_catch',3),
  ('manual_ink_price',-1),('natural_spawn_efficiency',101),
])
def test_invalid_input_rejected(field,invalid):
    with pytest.raises(ValueError):calculate_squid({field:invalid},PRICES)

def test_unknown_bait_rejected():
    with pytest.raises(ValueError):calculate_squid({'bait':'WHALE_BAIT'},PRICES)

def test_rare_and_other_drops_always_flagged_unmodelled():
    r=calculate_squid({},PRICES,prices_live=True)
    assert r['is_full_method_profit'] is False
    assert any('PARTIAL LOOT' in v for v in r['warnings'])

def test_sensitivity_increases_with_catches_when_bait_is_free():
    s=sensitivity({'rain':False,'bait':'NONE'},PRICES)
    assert s['sensitivity']['low']<s['sensitivity']['base']<s['sensitivity']['high']

def test_rank_methods_rejects_partials_and_stale():
    candidates=[
      {'modelled_net':100000000,'is_full_method_profit':False,'prices_live':True,'anytime':True},
      {'modelled_net':50000000,'is_full_method_profit':True,'prices_live':False,'anytime':True},
      {'modelled_net':90000000,'is_full_method_profit':True,'prices_live':True,'anytime':False},
      {'modelled_net':45000000,'is_full_method_profit':True,'prices_live':True,'anytime':True},
    ]
    assert rank_methods(candidates)==[candidates[-1]]

def test_payback():
    assert payback_hours(200_000_000,50_000_000,40_000_000)==20
    assert payback_hours(100_000_000,30_000_000,40_000_000) is None
    assert payback_hours(100_000_000,40_000_000,40_000_000) is None


def test_ink_breakdown_matches_output_and_pet_not_double_counted():
    r=calculate_squid({'rain':False,'reels_per_hour':500,'squid_pet':True,'bait':'NONE'},PRICES)
    b=r['ink_breakdown']
    assert b['squid_pet_multiplier']==2
    assert b['unverified_extra_multiplier']==1
    assert b['base_ink_from_natural_squids']==0
    assert b['ink_after_pet']==pytest.approx(b['base_ink_from_fished_squids']*2)
    assert r['ink_per_hour']==pytest.approx(b['ink_after_pet'])

def test_extra_ink_is_explicit_hypothesis_not_pet():
    r=calculate_squid({'rain':False,'ink_yield_multiplier':1.5},PRICES)
    assert r['ink_per_hour']==pytest.approx(r['ink_breakdown']['ink_after_pet']*1.5)


def test_main_simulator_uses_fishing_unlocks_not_player_common_weight():
    low = calculate_squid({'fishing_level':1,'reels_per_hour':500,'rain':False,'squid_hat':False,'common_hook':False,'bait':'NONE'},PRICES)
    full = calculate_squid({'fishing_level':50,'reels_per_hour':500,'rain':False,'squid_hat':False,'common_hook':False,'bait':'NONE'},PRICES)
    assert low['squid_share']==pytest.approx(1200/2000)
    assert full['squid_share']==pytest.approx(1200/4296)
    assert len(low['pool_projection']['creatures'])==2
    assert len(full['pool_projection']['creatures'])==10
    # Legacy client input cannot override a sourced weight.
    altered=calculate_squid({'fishing_level':50,'other_common_weight':0,'reels_per_hour':500,'rain':False,'squid_hat':False,'common_hook':False,'bait':'NONE'},PRICES)
    assert altered['squid_share']==full['squid_share']
    assert altered['inputs']['other_common_weight']==800


def test_main_simulator_hydra_two_kills_and_unpriced_ah():
    p={'reels_per_hour':1000,'bait':'NONE','rain':False,'hydra_kills_per_catch':1}
    one=calculate_squid(p,PRICES,prices_live=True)['pool_projection']
    two=calculate_squid({**p,'hydra_kills_per_catch':2},PRICES,prices_live=True)['pool_projection']
    h1=next(c for c in one['creatures'] if c['name']=='Water Hydra')
    h2=next(c for c in two['creatures'] if c['name']=='Water Hydra')
    assert h2['expected_kills_per_hour']==pytest.approx(h1['expected_kills_per_hour']*2)
    head=next(d for d in h2['drops'] if d['name']=='Water Hydra Head')
    assert head['expected_coins'] is None
    assert head['expected_units']==pytest.approx(h2['expected_kills_per_hour']*.14)
    assert any(d['mob']=='Water Hydra' and d['drop']=='Water Hydra Head' for d in two['unpriced'])


def test_itemized_squid_ink_matches_main_model_without_hypothesis():
    r=calculate_squid({'reels_per_hour':500,'rain':True,'squid_pet':True,'bait':'NONE'},PRICES)
    squid=next(c for c in r['pool_projection']['creatures'] if c['name']=='Squid')
    raw=next(d for d in squid['drops'] if d['name']=='Ink Sac')
    assert raw['expected_units']==pytest.approx(r['ink_per_hour'])
    enchant=next(d for d in squid['drops'] if d['name']=='Enchanted Ink Sac')
    assert enchant['expected_units']>0
    assert enchant['expected_coins'] is None
    assert r['pool_projection']['known_subtotal']==pytest.approx(r['pool_projection']['known_common_revenue']+r['pool_projection']['known_rare_base_ev'])


def test_time_of_day_rarity_modifier_round_trip():
    p={'bait':'LIGHT_BAIT','time_of_day':'day','rain':False}
    day=calculate_squid(p,PRICES)
    night=calculate_squid({**p,'time_of_day':'night'},PRICES)
    assert day['squid_share'] < night['squid_share']


def test_squid_pet_rarity_and_level_expected_bonus():
    common=calculate_squid({'rain':False,'reels_per_hour':500,'squid_pet_rarity':'COMMON','squid_pet_level':100,'bait':'NONE'},PRICES)
    rare=calculate_squid({'rain':False,'reels_per_hour':500,'squid_pet_rarity':'RARE','squid_pet_level':100,'bait':'NONE'},PRICES)
    epic50=calculate_squid({'rain':False,'reels_per_hour':500,'squid_pet_rarity':'EPIC','squid_pet_level':50,'bait':'NONE'},PRICES)
    legendary=calculate_squid({'rain':False,'reels_per_hour':500,'squid_pet_rarity':'LEGENDARY','squid_pet_level':100,'bait':'NONE'},PRICES)
    assert common['ink_breakdown']['squid_pet_multiplier']==pytest.approx(1.5)
    assert rare['ink_breakdown']['squid_pet_multiplier']==pytest.approx(1.75)
    assert epic50['ink_breakdown']['squid_pet_multiplier']==pytest.approx(1.5)
    assert legendary['ink_breakdown']['squid_pet_multiplier']==pytest.approx(2.0)
    for r in [common,rare,epic50,legendary]:
        squid=next(c for c in r['pool_projection']['creatures'] if c['name']=='Squid')
        raw=next(d for d in squid['drops'] if d['name']=='Ink Sac')
        assert raw['expected_units']==pytest.approx(r['ink_per_hour'])
