"""Audit market-ID coverage without presenting incomplete loot as full profit."""
from collections import defaultdict
from engine.pools import DROPS, POOLS

def audit_market_ids(products):
    if not isinstance(products, dict):
        raise ValueError("Market products must be a dictionary")
    used = defaultdict(list)
    unassigned = defaultdict(list)
    for mob, table in DROPS.items():
        for drop in table['drops']:
            row = {'creature': mob, 'drop': drop['name']}
            market_id = drop['market_id']
            if market_id is None:
                unassigned[drop['name']].append(row)
            else:
                used[market_id].append(row)
    listed = []
    missing = []
    for market_id, rows in sorted(used.items()):
        entry = {'market_id': market_id, 'uses': rows}
        if market_id in products:
            listed.append(entry)
        else:
            missing.append(entry)
    return {
        'creature_tables': len(DROPS),
        'pool_count': len(POOLS),
        'drop_rows': sum(len(t['drops']) for t in DROPS.values()),
        'unique_candidate_market_ids': len(used),
        'listed_candidate_ids': len(listed),
        'missing_candidate_ids': len(missing),
        'unassigned_drop_rows': sum(len(x) for x in unassigned.values()),
        'listed': listed,
        'missing': missing,
        'unassigned': [{'name': name, 'uses': rows} for name, rows in sorted(unassigned.items())],
        'disclaimer': 'A listed ID confirms only that the Bazaar snapshot contains it. It does not prove the drop mapping, chance, or full reward coverage.'
    }
