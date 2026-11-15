"""Fishing modifier eligibility ledger: no unverified synergy may silently become profit.

This module records *questions*, not answers. Each modifier is split by reward
trigger, and unknown interactions stay excluded from verified profit.
"""
from __future__ import annotations

from typing import Any

REWARD_CHANNELS = (
    'direct_kill_items',
    'lootshare_items',
    'fishing_treasure',
    'creature_hunting_shards',
    'conditional_shards',
    'dyes_and_jackpots',
    'coins_from_kills',
    'catch_frequency',
    'input_costs',
)

MODIFIER_CHANNELS = {
    'looting': ('direct_kill_items', 'lootshare_items', 'dyes_and_jackpots'),
    'magic_find': ('direct_kill_items', 'lootshare_items', 'dyes_and_jackpots'),
    'hunting_fortune': ('creature_hunting_shards', 'conditional_shards'),
    'precursor_drone_extra_treasure': ('fishing_treasure', 'conditional_shards'),
    'moltenfish_shard': ('conditional_shards', 'fishing_treasure'),
    'god_potion': ('catch_frequency', 'direct_kill_items', 'creature_hunting_shards'),
    'potions': ('catch_frequency', 'direct_kill_items', 'creature_hunting_shards'),
    'mason_jar': ('direct_kill_items', 'fishing_treasure', 'conditional_shards'),
    'hotspot_mixin': ('catch_frequency', 'fishing_treasure', 'input_costs'),
    'chum_mixin': ('catch_frequency', 'fishing_treasure', 'input_costs'),
    'bait': ('catch_frequency', 'fishing_treasure', 'input_costs'),
    'hook': ('catch_frequency', 'direct_kill_items'),
    'sinker': ('catch_frequency', 'fishing_treasure'),
    'equipment_attributes': ('catch_frequency', 'direct_kill_items', 'fishing_treasure'),
    'pet_swaps': ('catch_frequency', 'direct_kill_items', 'creature_hunting_shards'),
    'tiki_mask': ('direct_kill_items', 'fishing_treasure'),
    'squid_hat': ('catch_frequency', 'direct_kill_items'),
    'consumables': ('catch_frequency', 'fishing_treasure', 'input_costs'),
}

def build_modifier_ledger(evidence: dict[str, dict[str, dict[str, Any]]] | None = None):
    """Only an explicit sourced record may mark an interaction verified.

    A sourced record must supply an exact evidence URL, mechanic, eligibility,
    timing, and numerical rule. The ledger does not itself apply multipliers.
    """
    evidence = {} if evidence is None else evidence
    if not isinstance(evidence, dict):
        raise ValueError('Evidence must be a dictionary')
    unknown_modifiers = set(evidence) - set(MODIFIER_CHANNELS)
    if unknown_modifiers:
        raise ValueError(f'Unknown modifier(s): {sorted(unknown_modifiers)}')
    rows = []
    for modifier, channels in MODIFIER_CHANNELS.items():
        supplied = evidence.get(modifier, {})
        if not isinstance(supplied, dict) or set(supplied) - set(channels):
            raise ValueError(f'Invalid channels for {modifier}')
        for channel in channels:
            entry = supplied.get(channel)
            if entry is None:
                status, record = 'unverified', None
            else:
                if not isinstance(entry, dict):
                    raise ValueError(f'Invalid evidence for {modifier}/{channel}')
                required = ('source_url', 'mechanic', 'timing', 'eligibility', 'numerical_rule')
                if any(not isinstance(entry.get(key), str) or not entry[key].strip() for key in required):
                    raise ValueError(f'Incomplete evidence for {modifier}/{channel}')
                if not entry['source_url'].startswith(('https://', 'http://')):
                    raise ValueError('Evidence source must be an HTTP(S) URL')
                status, record = 'evidence-recorded-needs-independent-validation', dict(entry)
            rows.append({'modifier': modifier, 'reward_channel': channel,
                         'status': status, 'evidence': record,
                         'included_in_verified_profit': False})
    return {
        'entries': rows, 'unverified_count': sum(r['status']=='unverified' for r in rows),
        'evidence_recorded_count': sum(r['evidence'] is not None for r in rows),
        'verified_profit_modifier_count': 0,
        'warning': 'Evidence records are research leads. No modifier interaction is automatically eligible for profit until independently validated and explicitly implemented.',
    }
