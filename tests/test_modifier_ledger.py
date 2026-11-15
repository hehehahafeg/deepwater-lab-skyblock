import pytest
from engine.modifier_ledger import build_modifier_ledger, MODIFIER_CHANNELS, REWARD_CHANNELS

def test_modifier_ledger_exhaustive_channels_and_no_automatic_profit():
    ledger = build_modifier_ledger()
    assert len(ledger['entries']) == sum(map(len, MODIFIER_CHANNELS.values()))
    assert ledger['unverified_count'] == len(ledger['entries'])
    assert ledger['verified_profit_modifier_count'] == 0
    assert all(not row['included_in_verified_profit'] for row in ledger['entries'])
    assert {'fishing_treasure','creature_hunting_shards','conditional_shards','lootshare_items'} <= set(REWARD_CHANNELS)

def test_drone_moltenfish_eligibility_not_assumed():
    ledger = build_modifier_ledger()
    rows = {(r['modifier'],r['reward_channel']):r for r in ledger['entries']}
    for pair in [('precursor_drone_extra_treasure','conditional_shards'),
                 ('precursor_drone_extra_treasure','fishing_treasure'),
                 ('moltenfish_shard','fishing_treasure')]:
        assert rows[pair]['status'] == 'unverified'
        assert rows[pair]['included_in_verified_profit'] is False

def test_evidence_record_is_not_automatic_verified_profit():
    r = build_modifier_ledger({'precursor_drone_extra_treasure':{'fishing_treasure':{
        'source_url':'https://example.org/research', 'mechanic':'extra roll',
        'timing':'reel', 'eligibility':'unknown','numerical_rule':'hypothesis only'}}})
    row=next(x for x in r['entries'] if x['modifier']=='precursor_drone_extra_treasure' and x['reward_channel']=='fishing_treasure')
    assert row['status']=='evidence-recorded-needs-independent-validation'
    assert not row['included_in_verified_profit']
    assert r['verified_profit_modifier_count']==0

@pytest.mark.parametrize('bad', [None, '', {'source_url':'ftp://example.org','mechanic':'x','timing':'x','eligibility':'x','numerical_rule':'x'}])
def test_incomplete_evidence_rejected(bad):
    if bad is None:
        bad={'source_url':'https://example.org'}
    with pytest.raises(ValueError):
        build_modifier_ledger({'looting':{'direct_kill_items':bad}})

def test_unknown_modifier_or_channel_rejected():
    with pytest.raises(ValueError):
        build_modifier_ledger({'imaginary':{}})
    with pytest.raises(ValueError):
        build_modifier_ledger({'looting':{'fishing_treasure':{}}})

def test_project_pool_surfaces_unverified_modifier_provenance():
    from engine.pools import project_pool
    r=project_pool({'pool':'crimson_lava','looting_level':5,'magic_find':250,'reels_per_hour':100}, {})
    assert r['modifier_eligibility_verified'] is False
    assert r['modifier_ledger_summary']['tracked_interactions'] == sum(map(len,MODIFIER_CHANNELS.values()))
    assert r['modifier_ledger_summary']['verified_profit_modifier_count'] == 0
    leech=next(x for x in r['creatures'] if x['name']=='Lava Leech')
    magmafish=next(x for x in leech['drops'] if x['name']=='Magmafish')
    dye=next(x for x in leech['drops'] if x['name']=='Carmine Dye')
    assert magmafish['modifier_calculation_provenance']=='generalized-unverified-heuristic'
    assert magmafish['modifier_eligibility_status']['looting']=='unverified'
    assert dye['modifier_calculation_provenance']=='base-chance-no-generalized-modifier'
    assert dye['modifier_eligibility_status']['magic_find']=='unverified'
    assert r['is_full_method_profit'] is False

def test_base_counterfactual_separates_unverified_looting_and_magic_find():
    from engine.pools import project_pool
    p={'pool':'crimson_lava','reels_per_hour':100,'looting_level':5,'magic_find':250}
    prices={'MAGMA_FISH':{'instant_sell':100}}
    r=project_pool(p,prices)
    leech=next(x for x in r['creatures'] if x['name']=='Lava Leech')
    magma=next(x for x in leech['drops'] if x['name']=='Magmafish')
    assert magma['base_no_looting_mf_expected_units']==pytest.approx(leech['expected_kills_per_hour']*20)
    assert magma['expected_units']==pytest.approx(magma['base_no_looting_mf_expected_units']*1.75)
    assert magma['heuristic_modifier_delta_units']==pytest.approx(magma['expected_units']-magma['base_no_looting_mf_expected_units'])
    assert r['base_no_looting_mf_priced_subtotal'] < r['known_subtotal']
    assert r['is_full_method_profit'] is False

def test_unpriced_counterfactual_does_not_invent_coins():
    from engine.pools import project_pool
    r=project_pool({'pool':'crimson_lava','reels_per_hour':100,'looting_level':5}, {})
    assert r['base_no_looting_mf_priced_subtotal']==0
    assert r['known_subtotal']==0
    assert any(d['base_no_looting_mf_expected_coins'] is None for c in r['creatures'] for d in c['drops'])
    assert 'not verified profit' in r['modifier_scenario_disclaimer']

def test_depth_prices_base_and_modifier_scenarios_independently():
    from engine.pools import project_pool
    p={'pool':'crimson_lava','reels_per_hour':100,'looting_level':5,
       'magic_find':0,'bait':'NONE'}
    prices={'MAGMA_FISH':{'instant_sell':100}}
    book={'MAGMA_FISH':{'buy_summary':[
        {'pricePerUnit':100,'amount':500},
        {'pricePerUnit':10,'amount':1000000}]}}
    result=project_pool(p,prices,prices_live=True,order_books=book,depth_pricing=True)
    magma=[d for c in result['creatures'] for d in c['drops']
           if d['market_id']=='MAGMA_FISH']
    modified=sum(d['expected_units'] for d in magma)
    base=sum(d['base_no_looting_mf_expected_units'] for d in magma)
    assert modified > base > 500
    expected_mod=500*100+(modified-500)*10
    expected_base=500*100+(base-500)*10
    assert sum(d['expected_coins'] for d in magma)==pytest.approx(expected_mod)
    assert sum(d['base_no_looting_mf_expected_coins'] for d in magma)==pytest.approx(expected_base)
    assert result['base_no_looting_mf_priced_subtotal'] <= result['known_subtotal']
    assert result['is_full_method_profit'] is False

def test_missing_table_coverage_is_encounter_weighted():
    from engine.pools import project_pool
    r=project_pool({'pool':'torrhus','reels_per_hour':1000,'fishing_level':50,'bait':'NONE'}, {})
    c=r['reward_coverage']
    expected_missing=sum(m['expected_per_hour'] for m in r['creatures'] if not m['has_drop_table'])
    assert c['expected_creature_encounters_per_hour']==pytest.approx(r['creature_rate'])
    assert c['missing_drop_table_encounters_per_hour']==pytest.approx(expected_missing)
    assert c['missing_drop_table_encounter_share']==pytest.approx(expected_missing/r['creature_rate'])
    assert 0<c['missing_drop_table_encounter_share']<1
    assert c['unpriced_positive_ev_drop_rows']>0
    assert c['full_profit_coverage'] is False
    assert not c['includes_hunting_shards']
    assert not c['includes_treasure']

def test_zero_catches_coverage_share_is_undefined_not_zero_profit():
    from engine.pools import project_pool
    r=project_pool({'pool':'torrhus','reels_per_hour':0,'bait':'NONE'}, {})
    c=r['reward_coverage']
    assert c['expected_creature_encounters_per_hour']==0
    assert c['missing_drop_table_encounter_share'] is None
    assert c['full_profit_coverage'] is False

def test_missing_table_priority_sorted_by_expected_encounters():
    from engine.pools import project_pool
    r=project_pool({'pool':'torrhus','reels_per_hour':1000,'fishing_level':50}, {})
    c=r['reward_coverage']
    q=c['missing_drop_table_research_priority']
    assert len(q)==4
    assert q[0]['creature']=='Brineling'
    assert all(a['expected_encounters_per_hour']>=b['expected_encounters_per_hour']
               for a,b in zip(q,q[1:]))
    assert sum(x['expected_encounters_per_hour'] for x in q)==pytest.approx(
        c['missing_drop_table_encounters_per_hour'])
    assert all(x['profit_impact']=='unknown-until-drops-and-prices-verified' for x in q)
    assert 0<c['top_three_missing_table_encounter_share']<=1

def test_hotspot_missing_table_priority_uses_blended_rates():
    from engine.pools import project_pool
    r=project_pool({'pool':'hotspot_water','base_pool':'bayou','reels_per_hour':1000,
                    'hotspot_override_percent':20}, {})
    q=r['reward_coverage']['missing_drop_table_research_priority']
    assert {x['creature'] for x in q}=={'Snapping Turtle','Manta Ray'}
    assert sum(x['expected_encounters_per_hour'] for x in q)==pytest.approx(
        r['reward_coverage']['missing_drop_table_encounters_per_hour'])

def test_zero_catch_priority_queue_is_empty():
    from engine.pools import project_pool
    r=project_pool({'pool':'torrhus','reels_per_hour':0}, {})
    assert r['reward_coverage']['missing_drop_table_research_priority']==[]
    assert r['reward_coverage']['top_three_missing_table_encounter_share'] is None

def test_haggard_official_loot_table_and_unpriced_routes():
    from engine.pools import DROPS, project_pool
    drops={d['name']:d for d in DROPS['Haggard']['drops']}
    assert len(drops)==7
    assert (drops['Helix Log']['min_quantity'],drops['Helix Log']['max_quantity'])==(8,16)
    assert drops['Enchanted Bone']['chance']==pytest.approx(.02)
    assert drops['Enchanted Helix Log']['chance']==pytest.approx(.05)
    assert drops['Enchanted Ruby Veilshroom']['chance']==pytest.approx(.01)
    assert drops['Aquamarine Dye']['chance']==pytest.approx(1/5_000_000)
    assert all(d['market_id'] is None for d in drops.values())
    r=project_pool({'pool':'torrhus','reels_per_hour':1000}, {})
    assert next(m for m in r['creatures'] if m['name']=='Haggard')['has_drop_table']
    assert 'Haggard' not in {x['creature'] for x in r['reward_coverage']['missing_drop_table_research_priority']}
    assert r['is_full_method_profit'] is False
