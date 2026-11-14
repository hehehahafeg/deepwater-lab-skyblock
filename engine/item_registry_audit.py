"""Cross-reference Bazaar candidate IDs against Hypixel's public item registry.

Name similarity is a research hint, NEVER an automatic mapping or valuation.
"""
import re

def normalize_name(value):
    return re.sub(r'[^a-z0-9]+', '', str(value).lower())

def reconcile_registry(audit, registry_payload):
    if not isinstance(registry_payload, dict) or registry_payload.get('success') is not True:
        raise ValueError('Item registry unavailable')
    items = registry_payload.get('items')
    if not isinstance(items, list) or not items:
        raise ValueError('Item registry contains no items')
    by_id = {}
    by_name = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str):
            continue
        by_id[item['id']] = item
        if isinstance(item.get('name'), str):
            by_name.setdefault(normalize_name(item['name']), []).append(item)
    def summary(item):
        npc = item.get('npc_sell_price')
        if isinstance(npc, bool) or not isinstance(npc, (int, float)) or not 0 <= npc < float('inf'):
            npc = None
        return {'id': item['id'], 'name': item.get('name'),
                'npc_sell_price': npc,
                'npc_price_evidence': 'registry-field-present' if npc is not None else 'not-provided',
                'can_auction': item.get('can_auction'), 'can_trade': item.get('can_trade'),
                'soulbound': item.get('soulbound'),
                'category': item.get('category')}
    missing = []
    for row in audit['missing']:
        market_id = row['market_id']
        item = by_id.get(market_id)
        missing.append({
            'candidate_market_id': market_id,
            'registry_exact_id': summary(item) if item else None,
            'name_hints': [summary(x) for x in by_name.get(normalize_name(market_id), [])][:10],
            'classification': 'registry-id-exists-bazaar-absent' if item else 'candidate-id-not-in-registry',
        })
    unassigned = []
    for row in audit['unassigned']:
        unassigned.append({
            'drop': row['name'], 'uses': row['uses'],
            'registry_name_matches': [summary(x) for x in by_name.get(normalize_name(row['name']), [])][:10],
            'status': 'unverified-reward-identity',
        })
    return {'registry_item_count': len(by_id), 'missing_candidate_id_reconciliation': missing,
            'unassigned_drop_registry_hints': unassigned,
            'warning': 'Registry names and NPC fields are research leads, not validated reward identities or guaranteed realizable prices.'}
