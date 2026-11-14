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
