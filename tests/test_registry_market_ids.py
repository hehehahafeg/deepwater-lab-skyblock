from engine.pools import DROPS

EXPECTED = {
    'Enchanted Lily Pad': 'ENCHANTED_WATER_LILY',
    'Pufferfish': 'RAW_FISH:3',
    'Raw Salmon': 'RAW_FISH:1',
    'Tropical Fish': 'RAW_FISH:2',
}

def test_corrected_registry_market_ids_for_all_drop_rows():
    seen = set()
    for table in DROPS.values():
        for drop in table['drops']:
            if drop['name'] in EXPECTED:
                seen.add(drop['name'])
                assert drop['market_id'] == EXPECTED[drop['name']]
    assert seen == set(EXPECTED)
