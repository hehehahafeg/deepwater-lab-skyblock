from engine.market_audit import audit_market_ids
from engine.pools import DROPS

def test_market_audit_reconciles_all_drop_rows():
    result = audit_market_ids({})
    assert result['creature_tables'] == len(DROPS)
    assert result['drop_rows'] == sum(len(t['drops']) for t in DROPS.values())
    assert result['listed_candidate_ids'] == 0
    assert result['missing_candidate_ids'] == result['unique_candidate_market_ids']
    assert result['unassigned_drop_rows'] > 0

def test_market_audit_marks_listed_ids_without_claiming_verified_mappings():
    result = audit_market_ids({'INK_SACK': {'instant_sell': 10}})
    assert any(x['market_id'] == 'INK_SACK' for x in result['listed'])
    assert result['listed_candidate_ids'] == 1
    assert 'does not prove' in result['disclaimer']

def test_market_audit_rejects_invalid_market_input():
    import pytest
    with pytest.raises(ValueError):
        audit_market_ids(None)

def test_market_audit_endpoint_fails_closed_on_stale_snapshot(monkeypatch):
    from fastapi.testclient import TestClient
    from app import app, market
    monkeypatch.setattr(market, 'get', lambda: {'live':False})
    response = TestClient(app).get('/api/market/audit')
    assert response.status_code == 503
