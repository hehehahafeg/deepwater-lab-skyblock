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
