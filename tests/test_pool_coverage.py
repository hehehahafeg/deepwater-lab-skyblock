from engine.pool_coverage import audit_pool_coverage
from engine.pools import POOLS, DROPS

def test_every_pool_reported_with_correct_table_counts():
    result = audit_pool_coverage()
    assert {p['pool_id'] for p in result['pools']} == set(POOLS)
    for row in result['pools']:
        creatures = POOLS[row['pool_id']]['creatures']
        assert row['creature_count'] == len(creatures)
        assert row['creatures_with_drop_tables'] + len(row['creatures_missing_drop_tables']) == len(creatures)
        assert row['drop_rows_with_candidate_market_ids'] + row['drop_rows_without_market_ids'] == sum(
            len(DROPS[c.name]['drops']) for c in creatures if c.name in DROPS)
        assert row['full_profit_coverage_verified'] is False

def test_missing_drop_tables_are_never_silently_counted_as_complete():
    result = audit_pool_coverage()
    for row in result['pools']:
        assert isinstance(row['creatures_missing_drop_tables'], list)
        assert isinstance(row['distinct_unassigned_drop_names'], list)
