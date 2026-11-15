from engine.pools import POOLS, DROPS, project_pool
from engine.pool_coverage import audit_pool_coverage

EXPECTED = {
 'Fried Chicken': {'Magmafish':(1,2,1),'Fried Feather':(1,1,.1),'Carmine Dye':(1,1,1/5_000_000)},
 'Volcanic Snail': {'Magmafish':(2,4,1),'Seared Escargot':(1,1,.04),'Silver Magmafish':(1,1,.01),'Carmine Dye':(1,1,1/5_000_000)},
 'Fireproof Witch': {'Magmafish':(8,16,1),'Gunpowder':(8,8,1),'Enchanted Glowstone Dust':(1,1,.2),'Enchanted Gunpowder':(1,1,.05),'Singed Powder':(1,1,.01),'Enchanted Glowstone':(1,1,.0025),'Fire Protection VI enchanted book':(1,1,.0001),'Carmine Dye':(1,1,1/2_500_000)},
 'Magma Pillar': {'Silver Magmafish':(2,4,1),'Enchanted Magma Cream':(2,4,1),'Pyroclasm VI enchanted book':(1,1,.0005),'Carmine Dye':(1,1,1/2_500_000)},
 'Fiery Scuttler': {'Scorched Crab Stick':(1,1,1),'Silver Magmafish':(8,16,1),'Severed Pincer':(1,1,.002),'Scuttler Shell':(1,1,.001),'Carmine Dye':(1,1,1/50_000)},
 'Ragnarok': {'Silver Magmafish':(16,32,1),"Bobbin' Scriptures":(1,1,.01),'Chain of the End Times':(1,1,.01),'Brimstone Handle':(1,1,.005),'Burnt Texts':(1,1,.0025),'Carmine Dye':(1,1,1/50_000)}
}

def test_all_lava_hotspot_creatures_have_sourced_base_drop_tables():
    names={c.name for c in POOLS['hotspot_lava']['creatures']}
    assert names == set(EXPECTED)
    assert all(name in DROPS for name in names)
    for name in names:
        assert DROPS[name]['source'] == 'https://hypixelskyblock.minecraft.wiki/w/'+name.replace(' ','_')
        drops={d['name']:(d['min_quantity'],d['max_quantity'],d['chance']) for d in DROPS[name]['drops']}
        assert drops == EXPECTED[name]

def test_hotspot_lava_is_still_partial_profit():
    pool=next(p for p in audit_pool_coverage()['pools'] if p['pool_id']=='hotspot_lava')
    assert pool['creatures_with_drop_tables'] == 6
    assert pool['full_profit_coverage_verified'] is False
    result=project_pool({'pool':'hotspot_lava','base_pool':'crimson_lava','hotspot_override_percent':85,'reels_per_hour':100}, {})
    assert result['is_full_method_profit'] is False
