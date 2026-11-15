from engine.pools import DROPS, project_pool
from engine.pool_coverage import audit_pool_coverage

def test_magma_slug_wiki_drop_quantities_and_chances():
    table = DROPS['Magma Slug']
    drops = {x['name']: x for x in table['drops']}
    assert drops['Magmafish']['expected_quantity'] == 5
    assert drops['Lump of Magma']['expected_quantity'] == 1.5
    assert drops['Slug Boots']['chance'] == .02
    assert drops['Carmine Dye']['chance'] == 1 / 5_000_000
    assert all(d['market_id'] is None for d in drops.values())

def test_magma_slug_structural_coverage_not_profit_completeness():
    pool = next(x for x in audit_pool_coverage()['pools'] if x['pool_id'] == 'crimson_lava')
    assert pool['creatures_with_drop_tables'] == 3
    assert pool['full_profit_coverage_verified'] is False
    result = project_pool({'pool':'crimson_lava','reels_per_hour':100}, {}, prices_live=False)
    slug = next(c for c in result['creatures'] if c['name'] == 'Magma Slug')
    assert slug['has_drop_table'] is True
    assert {d['name'] for d in slug['drops']} >= {'Magmafish', 'Lump of Magma', 'Slug Boots'}
    assert result['is_full_method_profit'] is False
