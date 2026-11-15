"""Structural loot coverage by fishing pool; never asserts economic completeness."""
from engine.pools import POOLS, DROPS

def audit_pool_coverage():
    pools = []
    for pool_id, pool in sorted(POOLS.items()):
        creatures = pool['creatures']
        missing_tables = []
        with_tables = 0
        assigned_rows = 0
        unassigned_rows = 0
        unassigned_names = set()
        for creature in creatures:
            table = DROPS.get(creature.name)
            if table is None:
                missing_tables.append(creature.name)
                continue
            with_tables += 1
            for drop in table['drops']:
                if drop['market_id'] is None:
                    unassigned_rows += 1
                    unassigned_names.add(drop['name'])
                else:
                    assigned_rows += 1
        pools.append({
            'pool_id': pool_id,
            'pool_name': pool['name'],
            'is_override': bool(pool.get('is_override')),
            'creature_count': len(creatures),
            'creatures_with_drop_tables': with_tables,
            'creatures_missing_drop_tables': missing_tables,
            'drop_rows_with_candidate_market_ids': assigned_rows,
            'drop_rows_without_market_ids': unassigned_rows,
            'distinct_unassigned_drop_names': sorted(unassigned_names),
            'full_profit_coverage_verified': False,
        })
    return {
        'pools': pools,
        'warning': 'Table presence is structural only: incomplete drops, chance rules, non-Bazaar sales and reward modifiers prevent verified full profit.',
    }
