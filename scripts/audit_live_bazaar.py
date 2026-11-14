"""Fetch a live Hypixel Bazaar snapshot and write an auditable ID coverage report.

Run: python scripts/audit_live_bazaar.py
No credentials required. A failed fetch exits nonzero and writes no success report.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import requests
from engine.market import URL, parse_bazaar_product
from engine.market_integrity import validate_snapshot
from engine.market_audit import audit_market_ids
from engine.item_registry_audit import reconcile_registry

ITEMS_URL = 'https://api.hypixel.net/v2/resources/skyblock/items'

OUTPUT = Path('artifacts/bazaar-market-id-audit.json')

def run():
    response = requests.get(URL, timeout=20, headers={
        'User-Agent': 'DeepwaterLab/0.4 (public Bazaar market coverage audit)'})
    response.raise_for_status()
    payload = response.json()
    products = validate_snapshot(payload)
    valid = {}
    for item_id, product in products.items():
        try:
            valid[item_id] = parse_bazaar_product(product)
        except (ValueError, TypeError, KeyError, OverflowError):
            continue
    if not valid:
        raise ValueError('Live Bazaar response has no valid products')
    result = audit_market_ids(valid)
    registry_response = requests.get(ITEMS_URL, timeout=20, headers={
        'User-Agent': 'DeepwaterLab/0.4 (public item registry audit)'})
    registry_response.raise_for_status()
    result['registry_reconciliation'] = reconcile_registry(result, registry_response.json())
    for entry in result['registry_reconciliation']['missing_candidate_id_reconciliation']:
        for hint in entry['name_hints']:
            hint['bazaar_listed'] = hint['id'] in valid
    for entry in result['registry_reconciliation']['unassigned_drop_registry_hints']:
        for hint in entry['registry_name_matches']:
            hint['bazaar_listed'] = hint['id'] in valid
    result.update({
        'audited_at_utc': datetime.now(timezone.utc).isoformat(),
        'source': URL,
        'source_last_updated_ms': payload['lastUpdated'],
        'bazaar_products_received': len(products),
        'bazaar_products_price_valid': len(valid),
        'validation': 'Live source timestamp validated at fetch time',
    })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('Registry reward coverage:', json.dumps({key: value for key, value in result['registry_reconciliation'].items() if key.startswith('unassigned_') and isinstance(value, int)}, sort_keys=True))
    print('Registry classifications:', json.dumps(result['registry_reconciliation']['missing_candidate_id_reconciliation'], sort_keys=True))
    print('Unassigned registry hints:', json.dumps(result['registry_reconciliation']['unassigned_drop_registry_hints'], sort_keys=True))
    print('Missing Bazaar candidate IDs:', ', '.join(row['market_id'] for row in result['missing']) or '(none)')
    print('Unassigned drop names:', ', '.join(row['name'] for row in result['unassigned']))
    print(json.dumps({
        'bazaar_products_price_valid': len(valid),
        'drop_rows': result['drop_rows'],
        'listed_candidate_ids': result['listed_candidate_ids'],
        'missing_candidate_ids': result['missing_candidate_ids'],
        'unassigned_drop_rows': result['unassigned_drop_rows'],
        'report': str(OUTPUT)
    }, sort_keys=True))

if __name__ == '__main__':
    run()
