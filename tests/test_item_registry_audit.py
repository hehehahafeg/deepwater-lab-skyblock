import pytest
from engine.item_registry_audit import reconcile_registry

AUDIT = {
    'missing': [{'market_id': 'RAW_SALMON'}, {'market_id': 'FAKE_ID'}],
    'unassigned': [{'name': 'Titanoboa Shed', 'uses': [{'creature': 'Titanoboa'}]}]
}
REGISTRY = {'success': True, 'items': [
    {'id': 'RAW_FISH:1', 'name': 'Raw Salmon', 'npc_sell_price': 5},
    {'id': 'TITANOBOA_SHED', 'name': 'Titanoboa Shed'},
]}

def test_registry_audit_keeps_name_hints_unverified():
    r = reconcile_registry(AUDIT, REGISTRY)
    missing = r['missing_candidate_id_reconciliation']
    assert missing[0]['classification'] == 'candidate-id-not-in-registry'
    assert missing[0]['registry_exact_id'] is None
    assert missing[1]['name_hints'] == []
    assert r['unassigned_drop_registry_hints'][0]['registry_name_matches'][0]['id'] == 'TITANOBOA_SHED'
    assert r['unassigned_drop_registry_hints'][0]['status'] == 'unverified-reward-identity'

def test_registry_exact_id_can_exist_without_bazaar_listing():
    audit = {'missing': [{'market_id': 'RAW_SALMON'}], 'unassigned': []}
    registry = {'success': True, 'items': [{'id': 'RAW_SALMON', 'name': 'Raw Salmon'}]}
    assert reconcile_registry(audit, registry)['missing_candidate_id_reconciliation'][0]['classification'] == 'registry-id-exists-bazaar-absent'

@pytest.mark.parametrize('bad', [None, {}, {'success': False, 'items': []}, {'success': True, 'items': []}])
def test_registry_fails_closed(bad):
    with pytest.raises(ValueError):
        reconcile_registry(AUDIT, bad)

def test_registry_coverage_and_npc_metadata_are_evidence_only():
    audit = {'missing': [], 'unassigned': [
        {'name': 'Titanoboa Shed', 'uses': []},
        {'name': 'Unknown Thing', 'uses': []}
    ]}
    registry = {'success': True, 'items': [
        {'id': 'TITANOBOA_SHED', 'name': 'Titanoboa Shed',
         'npc_sell_price': 42, 'can_auction': False, 'soulbound': 'COOP'}
    ]}
    result = reconcile_registry(audit, registry)
    assert result['unassigned_distinct_names'] == 2
    assert result['unassigned_unique_registry_name_matches'] == 1
    assert result['unassigned_no_registry_name_matches'] == 1
    hint = result['unassigned_drop_registry_hints'][0]['registry_name_matches'][0]
    assert hint['npc_sell_price'] == 42
    assert hint['can_auction'] is False and hint['soulbound'] == 'COOP'
    assert result['unassigned_drop_registry_hints'][0]['status'] == 'unverified-reward-identity'

def test_nonfinite_registry_npc_price_not_reported():
    result = reconcile_registry({'missing':[], 'unassigned':[{'name':'X','uses':[]}]},
       {'success':True,'items':[{'id':'X','name':'X','npc_sell_price':float('nan')}]})
    assert result['unassigned_drop_registry_hints'][0]['registry_name_matches'][0]['npc_sell_price'] is None
