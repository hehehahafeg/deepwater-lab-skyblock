from engine.pools import DROPS, project_pool
from engine.pool_coverage import audit_pool_coverage

def test_magma_slug_wiki_drop_quantities_and_chances():
    table = DROPS['Magma Slug']
    drops = {x['name']: x for x in table['drops']}
    assert drops['Magmafish']['expected_quantity'] == 5
    assert drops['Lump of Magma']['expected_quantity'] == 1.5
    assert drops['Slug Boots']['chance'] == .02
    assert drops['Carmine Dye']['chance'] == 1 / 5_000_000
    assert drops['Magmafish']['market_id'] == 'MAGMA_FISH'
    assert all(d['market_id'] is None for d in drops.values() if d['name'] != 'Magmafish')

def test_magma_slug_structural_coverage_not_profit_completeness():
    pool = next(x for x in audit_pool_coverage()['pools'] if x['pool_id'] == 'crimson_lava')
    assert pool['creatures_with_drop_tables'] == 6
    assert pool['full_profit_coverage_verified'] is False
    result = project_pool({'pool':'crimson_lava','reels_per_hour':100}, {}, prices_live=False)
    slug = next(c for c in result['creatures'] if c['name'] == 'Magma Slug')
    assert slug['has_drop_table'] is True
    assert {d['name'] for d in slug['drops']} >= {'Magmafish', 'Lump of Magma', 'Slug Boots'}
    assert result['is_full_method_profit'] is False

def test_moogma_sourced_base_drops():
    drops = {x['name']:x for x in DROPS['Moogma']['drops']}
    assert drops['Magmafish']['expected_quantity'] == 8
    assert drops['Moogma Pelt']['expected_quantity'] == 1.5
    assert drops['Moogma Leggings']['chance'] == .02
    assert drops['Carmine Dye']['chance'] == 1/5_000_000
    assert drops['Magmafish']['market_id'] == 'MAGMA_FISH'
    assert all(x['market_id'] is None for x in drops.values() if x['name'] != 'Magmafish')

def test_lava_leech_source_backed_drops_and_partial_profit():
    drops = {d['name']: d for d in DROPS['Lava Leech']['drops']}
    assert drops['Magmafish']['market_id'] == 'MAGMA_FISH'
    assert drops['Magmafish']['expected_quantity'] == 20
    assert drops['Cup of Blood']['chance'] == 1
    assert drops['Blade of the Volcano']['chance'] == .05
    assert drops["Pitchin' Koi"]['chance'] == .004
    assert drops['Carmine Dye']['chance'] == 1/2_500_000
    result = project_pool({'pool':'crimson_lava','reels_per_hour':100}, {})
    assert result['is_full_method_profit'] is False

def test_pyroclastic_worm_source_rates_and_partial_profit():
    drops = {d['name']: d for d in DROPS['Pyroclastic Worm']['drops']}
    assert drops['Magmafish']['market_id'] == 'MAGMA_FISH'
    assert drops['Magmafish']['expected_quantity'] == 10
    assert drops['Pyroclastic Scale']['chance'] == 1
    assert drops['Charm I enchanted book']['chance'] == .01
    assert drops['Carmine Dye']['chance'] == 1/2_500_000
    assert 'Lootshare' in DROPS['Pyroclastic Worm']['note']
    result = project_pool({'pool':'crimson_lava','reels_per_hour':100}, {})
    assert result['is_full_method_profit'] is False
