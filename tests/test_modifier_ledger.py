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
