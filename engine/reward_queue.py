"""Research queue for unpriced fishing rewards; never automatically values drops.

The queue prioritizes recurring and multi-creature rewards for manual verification.
"""
from engine.pools import DROPS

def build_reward_queue(registry_reconciliation):
    if not isinstance(registry_reconciliation, dict):
        raise ValueError('Registry reconciliation required')
    rows = registry_reconciliation.get('unassigned_drop_registry_hints')
    if not isinstance(rows, list):
        raise ValueError('Missing reward hints')
    drop_metadata = {}
    for mob, table in DROPS.items():
        for drop in table['drops']:
            if drop['market_id'] is None:
                drop_metadata[(mob, drop['name'])] = drop
    queue = []
    for entry in rows:
        hints = entry.get('registry_name_matches', [])
        uses = entry.get('uses', [])
        if not isinstance(hints, list) or not isinstance(uses, list):
            raise ValueError('Invalid reward hints')
        occurrences = []
        for use in uses:
            d = drop_metadata.get((use.get('creature'), entry.get('drop')))
            if d is not None:
                occurrences.append({'creature': use['creature'], 'tier': d['tier'],
                                    'base_chance': d['chance'],
                                    'expected_quantity': d['expected_quantity']})
        bazaar_hints = [h['id'] for h in hints if h.get('bazaar_listed') is True]
        npc_hints = [{'id': h['id'], 'npc_sell_price': h['npc_sell_price']} for h in hints
                     if h.get('npc_sell_price') is not None]
        auction_hints = [h['id'] for h in hints if h.get('can_auction') is not False
                         and not h.get('soulbound')]
        if not hints:
            route = 'unmatched-registry-name'
        elif bazaar_hints:
            route = 'bazaar-candidate-needs-drop-id-verification'
        elif npc_hints:
            route = 'npc-candidate-needs-drop-id-and-sell-verification'
        elif auction_hints:
            route = 'auction-candidate-needs-live-price'
        else:
            route = 'no-confirmed-sale-route'
        score = 10 * len(occurrences)
        score += 20 if any(d['tier'] == 'common' for d in occurrences) else 0
        score += 8 if any(d['tier'] == 'rare' for d in occurrences) else 0
        score += 3 if any(d['tier'] == 'jackpot' for d in occurrences) else 0
        queue.append({'reward': entry['drop'], 'priority_score': score,
                      'candidate_route': route, 'bazaar_id_hints': bazaar_hints,
                      'npc_hints': npc_hints, 'auction_id_hints': auction_hints,
                      'occurrences': occurrences, 'verified_profit_coins': None,
                      'status': 'requires-verification'})
    queue.sort(key=lambda r: (-r['priority_score'], r['reward']))
    return {'reward_count': len(queue), 'queue': queue,
            'disclaimer': 'Priority is based on modeled row frequency and tier, not measured coins/hour. None of these hints are confirmed market values.'}
