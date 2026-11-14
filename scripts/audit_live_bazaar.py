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
