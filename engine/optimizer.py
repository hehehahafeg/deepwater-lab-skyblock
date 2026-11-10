"""Compare sourced gear combinations under an explicit capped-speed assumption."""
from engine.models import bounded_number
from engine.pools import project_pool


def optimize_loadouts(pool, target, cap, params, prices, *, live):
    speed = bounded_number(params.get('speed'), 'Fishing Speed before swapped gear', 0, 1000)
    scc = bounded_number(params.get('scc'), 'SCC before swapped gear', 0, 100)
    dh = bounded_number(params.get('dh'), 'Double Hook Chance', 0, 100)
    reels = bounded_number(params.get('reels'), 'Measured speed-capped reels/hour', 1, 5000)
    hotspot = pool['pool'].startswith('hotspot')
    helmets = [('Magma Lord Helmet', 0, 4.5, 0)]
    if hotspot:
        helmets.append(('Tiki Mask', 10, 6, 2))
    if target in ('Squid', 'Inkling'):
        helmets.append(('Squid Hat', 0, 0, 0))
    rows = []
    for helmet, helmet_speed, helmet_scc, helmet_dh in helmets:
        for necklace, necklace_speed, necklace_scc in [('Magma Lord Necklace', 0, 2.5), ('Backwater Necklace', 2, 1)]:
            for gillsplash in range(4):
                slots = ('Cloak', 'Belt', 'Gloves')
                equipment = [f'{"Gillsplash" if i < gillsplash else "Backwater"} {slot}' for i, slot in enumerate(slots)]
                total_speed = speed + helmet_speed + necklace_speed + 14*gillsplash + 2*(3-gillsplash)
                magma_pieces = 3 + (helmet == 'Magma Lord Helmet') + (necklace == 'Magma Lord Necklace')
                set_scc = {4: 1, 5: 1.5}.get(magma_pieces, 0)
                effective_scc = min(100, scc + helmet_scc + necklace_scc + 3-gillsplash + set_scc)
                effective_dh = min(100, dh + helmet_dh)
                if total_speed < cap or effective_scc < 100:
                    continue
                result = project_pool(dict(
                    pool, reels_per_hour=reels, fishing_level=50, sea_creature_chance=effective_scc,
                    double_hook_chance=effective_dh, squid_hat=helmet == 'Squid Hat',
                    bait='HOTSPOT_BAIT' if hotspot else 'NONE',
                    hook='HOTSPOT_HOOK' if hotspot else ('COMMON_HOOK' if target == 'Squid' else 'NONE'),
                    hotspot_override_percent=85, magic_find=params.get('magic_find', 0),
                    looting_level=params.get('looting_level', 0),
                ), prices, prices_live=live)
                net = result['known_subtotal_after_bait'] if live and result['priced_drop_entries'] else None
                row = dict(helmet=helmet, necklace=necklace, equipment=equipment, speed=total_speed,
                           scc=effective_scc, dh=effective_dh, capped=True, net=net,
                           creatures_per_hour=result['creature_rate'], bait_cost=result['bait_cost'],
                           unpriced=len(result['unpriced']), missing_tables=len(result['unmodelled']))
                rows.append(row)
    rows.sort(key=lambda row: (row['net'] is not None, row['net'] if row['net'] is not None else 0), reverse=True)
    return {'rows': rows, 'speed_cap': cap, 'prices_live': live, 'full_profit_verified': False}
