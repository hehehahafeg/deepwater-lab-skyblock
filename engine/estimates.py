"""Automatic, explicitly hypothetical capped-build scenarios using current prices.

Rates and unmeasured stats are assumptions, not claims of a global maximum.
"""
from copy import deepcopy
from engine.optimizer import optimize_loadouts


def estimate_strategy(strategy, pool, snapshot, *, cache=None, breakdown=False, magic_find=300, catches_per_hour=1050):
    if pool is None:
        return {'status': 'unsupported', 'reason': 'No applicable catch/drop model for this method yet; no defensible coins/hour estimate.'}
    if not snapshot.get('live'):
        return {'status': 'market_unavailable', 'reason': 'Live Bazaar prices unavailable. Refresh when market access returns.'}
    squid = strategy['style'] == 'squid'
    cap = strategy['fishing_speed_cap']
    # This baseline is a declared capped-stat scenario, not an item-derived maximum.
    params = dict(speed=cap, scc=100, dh=30, reels=catches_per_hour, magic_find=magic_find,
                  looting_level=5, squid_pet=squid,
                  natural_squids_per_hour=(3600/11*(2/3)*1.5*.6 if squid else 0))
    key = (tuple(sorted(pool.items())), strategy['target'], cap, squid, magic_find, catches_per_hour)
    cached = cache.get(key) if cache is not None else None
    if cached is None:
        result = optimize_loadouts(pool, strategy['target'], cap, params, snapshot['products'], live=True)
        candidates = [r for r in result['rows'] if r['net'] is not None]
        if not candidates:
            return {'status': 'unpriced', 'reason': 'No priced loot subtotal with known bait costs for this pool.'}
        best = candidates[0]
        rain = 300000 if squid else 0
        endpoints = []
        for rate in (catches_per_hour * 6/7, catches_per_hour * 8/7):
            ranked = optimize_loadouts(pool, strategy['target'], cap, dict(params, reels=rate), snapshot['products'], live=True)
            endpoints.append(max(r['net'] for r in ranked['rows'] if r['net'] is not None)-rain)
        projection = best['projection']
        cached = dict(status='estimated', coins_per_hour=best['net']-rain,
            low=min(endpoints), high=max(endpoints), hypothetical=True,
            label='Capped-build priced loot subtotal',
            assumptions=dict(params, fishing_speed_cap=cap, reels_range=[catches_per_hour * 6/7,catches_per_hour * 8/7], rain_cost=rain),
            setup={k:v for k,v in best.items() if k not in ('projection','net')},
            candidates_compared=len(candidates), unpriced=projection['unpriced'],
            missing_tables=projection['unmodelled'], bait_cost=best['bait_cost'],
            jackpot_ev=projection['known_jackpot_base_ev'],
            checked_at=snapshot.get('checked_at'),
            caveat='±14.3% catch-rate sensitivity, not a confidence interval. 30 base Double Hook is assumed, not a verified maximum. Magic Find and catches/hour use the optional inputs or displayed defaults. Best among modeled gear combinations only. Excludes unpriced loot, missing tables, jackpot EV, treasure, lootshare and unmodeled bonuses; kill downtime is not separately modeled. Methods sharing a pool can share an estimate. Experimental bonuses are not applied.',
            creatures=projection['creatures'])
        if cache is not None:
            cache[key] = cached
    answer = deepcopy(cached)
    if not breakdown:
        answer.pop('creatures', None)
    return answer
