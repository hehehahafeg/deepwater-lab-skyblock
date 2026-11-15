import pytest
from engine.reward_queue import build_reward_queue

def test_queue_has_no_invented_profit():
    hints = {'unassigned_drop_registry_hints': [
        {'drop': 'Titanoboa Shed', 'uses': [{'creature': 'Titanoboa'}],
         'registry_name_matches': [{'id': 'TITANOBOA_SHED', 'bazaar_listed': False,
                                    'npc_sell_price': None, 'can_auction': True}]},
        {'drop': 'Aquamarine Dye', 'uses': [{'creature': 'Squid'}],
         'registry_name_matches': []}]}
    r = build_reward_queue(hints)
    assert r['reward_count'] == 2
    assert all(x['verified_profit_coins'] is None for x in r['queue'])
    assert all(x['status'] == 'requires-verification' for x in r['queue'])
    assert next(x for x in r['queue'] if x['reward'] == 'Titanoboa Shed')['candidate_route'] == 'auction-candidate-needs-live-price'

def test_queue_marks_bazaar_hints_unverified():
    r = build_reward_queue({'unassigned_drop_registry_hints': [
        {'drop':'Tiki Mask','uses':[{'creature':'Wiki Tiki'}],
         'registry_name_matches':[{'id':'TIKI_MASK','bazaar_listed':True,'npc_sell_price':2}]}]})
    assert r['queue'][0]['candidate_route'] == 'bazaar-candidate-needs-drop-id-verification'
    assert r['queue'][0]['verified_profit_coins'] is None

@pytest.mark.parametrize('bad', [None, {}, {'unassigned_drop_registry_hints':None}])
def test_queue_fails_closed(bad):
    with pytest.raises(ValueError):
        build_reward_queue(bad)

def test_missing_auction_flag_never_implies_auction_eligibility():
    result = build_reward_queue({'unassigned_drop_registry_hints': [
        {'drop':'Tiki Mask','uses':[], 'registry_name_matches':[
            {'id':'TIKI_MASK', 'bazaar_listed':False, 'npc_sell_price':None,
             'can_auction':None, 'soulbound':None}]}]})
    entry = result['queue'][0]
    assert entry['auction_id_hints'] == []
    assert entry['candidate_route'] == 'sale-route-unknown-or-restricted'
    assert entry['market_route_verified'] is False

def test_explicit_auction_permission_still_does_not_verify_sale_route():
    result = build_reward_queue({'unassigned_drop_registry_hints': [
        {'drop':'Tiki Mask','uses':[], 'registry_name_matches':[
            {'id':'TIKI_MASK', 'bazaar_listed':False, 'npc_sell_price':None,
             'can_auction':True, 'soulbound':None}]}]})
    entry = result['queue'][0]
    assert entry['auction_id_hints'] == ['TIKI_MASK']
    assert entry['market_route_verified'] is False

def test_soulbound_blocks_auction_hint():
    result = build_reward_queue({'unassigned_drop_registry_hints': [
        {'drop':'Tiki Mask','uses':[], 'registry_name_matches':[
            {'id':'TIKI_MASK', 'bazaar_listed':False, 'npc_sell_price':None,
             'can_auction':True, 'soulbound':'SOULBOUND'}]}]})
    assert result['queue'][0]['auction_id_hints'] == []

def test_reward_queue_retains_multiple_same_name_drop_rows(monkeypatch):
    import engine.reward_queue as module
    from copy import deepcopy
    source = deepcopy(module.DROPS)
    source['Synthetic Test Creature'] = {'drops':[
        {'name':'Repeated Drop','market_id':None,'tier':'common','chance':1.0,'expected_quantity':2},
        {'name':'Repeated Drop','market_id':None,'tier':'rare','chance':.1,'expected_quantity':3},
    ]}
    monkeypatch.setattr(module,'DROPS',source)
    r=module.build_reward_queue({'unassigned_drop_registry_hints':[
        {'drop':'Repeated Drop','uses':[{'creature':'Synthetic Test Creature'}],'registry_name_matches':[]}
    ]})
    row=r['queue'][0]
    assert len(row['occurrences']) == 2
    assert row['summed_unweighted_expected_units_per_kill'] == pytest.approx(2.3)
    assert row['market_route_verified'] is False
    assert row['verified_profit_coins'] is None

def test_reward_queue_base_ev_units_not_profit():
    r=build_reward_queue({'unassigned_drop_registry_hints':[
        {'drop':'Carmine Dye','uses':[{'creature':'Ragnarok'}],'registry_name_matches':[]}
    ]})
    row=r['queue'][0]
    assert row['summed_unweighted_expected_units_per_kill'] == pytest.approx(1/50_000)
    assert 'NOT expected catches/hour' in row['expected_units_warning']
    assert row['verified_profit_coins'] is None
