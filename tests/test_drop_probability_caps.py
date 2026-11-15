"""Regression tests: one drop roll cannot exceed 100% after modifiers."""
import pytest
from engine.pools import project_pool


def _drop(result, mob, name):
    creature = next(c for c in result['creatures'] if c['name'] == mob)
    return next(d for d in creature['drops'] if d['name'] == name)


@pytest.mark.parametrize('looting_level', [0, 1, 3, 5])
def test_guaranteed_lava_magmafish_not_multiplied_by_looting(looting_level):
    result = project_pool({
        'pool':'crimson_lava', 'fishing_level':50,
        'reels_per_hour':100, 'looting_level':looting_level,
        'magic_find':300, 'squid_pet':False
    }, {'MAGMA_FISH':{'instant_sell':100}})
    drop = _drop(result,'Lava Leech','Magmafish')
    creature = next(c for c in result['creatures'] if c['name']=='Lava Leech')
    assert drop['adjusted_chance'] == 1
    assert drop['expected_rolls_per_kill'] == 1
    assert drop['quantity_modifier_multiplier'] == pytest.approx(1+0.15*looting_level)
    assert drop['expected_units'] == pytest.approx(creature['expected_kills_per_hour']*20*(1+0.15*looting_level))
    assert drop['expected_coins'] == pytest.approx(drop['expected_units']*100)


def test_rare_single_roll_cannot_exceed_one():
    result = project_pool({
        'pool':'crimson_lava', 'fishing_level':50,
        'reels_per_hour':100, 'looting_level':5, 'magic_find':500,
    }, {})
    for mob in result['creatures']:
        for drop in mob['drops']:
            assert 0 <= drop['expected_rolls_per_kill'] <= 1
            assert 0 <= drop['adjusted_chance'] <= 1
