"""Honest fishing models. Do not claim unmodelled loot as 0 earnings."""
import math
from typing import Any

SQUID_SOURCES = {
    "squid": "https://hypixelskyblock.minecraft.wiki/w/Squid",
    "pet": "https://hypixelskyblock.minecraft.wiki/w/Squid_Pet",
    "hook": "https://hypixelskyblock.minecraft.wiki/w/Common_Hook",
    "weights": "https://hypixelskyblock.minecraft.wiki/w/Sea_Creatures",
    "bait": "https://hypixelskyblock.minecraft.wiki/w/Fishing_Bait",
    "rain": "https://hypixelskyblock.minecraft.wiki/w/The_Park",
    "market": "https://api.hypixel.net/v2/skyblock/bazaar",
}

# Exact basic-water weights from the current Sea Creatures table. The only
# other COMMON creature is Sea Walker with base weight 800.
SQUID_WEIGHT = 1200.0
BASE_POOL_WEIGHT = 1200+800+700+550+400+250+160+130+88+18
BASE_SQUID_CHANCE = SQUID_WEIGHT/BASE_POOL_WEIGHT
BASE_OTHER_WEIGHT = BASE_POOL_WEIGHT - SQUID_WEIGHT

CATALOG = [
    {"id": "birch_squid", "name": "Birch Park · Squid density", "region": "The Park", "loop": "Stationary cast → reel → kill + rain spawns", "anytime": True, "movement": "fixed", "status": "partial-model", "reason": "Ink and lily-pad drops modelled. Other loot, exact creature pool and Looting behavior unresolved.", "sources": list(SQUID_SOURCES.values())[:5]},
    {"id": "bayou_hotspot", "name": "Bayou hotspot fishing", "region": "Backwater Bayou", "loop": "Compact hotspot rotation", "anytime": True, "movement": "small", "status": "requires-model", "reason": "Hotspot replacement rules and complete creature-specific loot catalog must be validated before numeric ranking.", "sources": ["https://hypixelskyblock.minecraft.wiki/w/Tutorial:Fishing_Guide"]},
    {"id": "stationary_lava", "name": "Stationary lava sea creatures", "region": "Crimson Isle", "loop": "One lava pool, no hotspot travel", "anytime": True, "movement": "fixed", "status": "requires-model", "reason": "Thunder Flash books and all other major drops must be priced and assigned verified probabilities.", "sources": ["https://hypixelskyblock.minecraft.wiki/w/Sea_Creatures"]},
    {"id": "atoll_puddle", "name": "Lotus Atoll · Puddle Jumper", "region": "Lotus Atoll", "loop": "Compact-area fishing", "anytime": True, "movement": "small", "status": "requires-model", "reason": "Puddle Jumper Hook weight known; full drops and competing weights need validation.", "sources": ["https://hypixelskyblock.minecraft.wiki/w/Rod_Parts"]},
    {"id": "moonglade", "name": "Moonglade Marsh · Elusives", "region": "Galatea", "loop": "Stationary rare-creature fishing", "anytime": True, "movement": "fixed", "status": "user-tested", "reason": "User already tested similar Driptoad Delve loop. Exclude until a distinct profitable variant exists.", "sources": []},
    {"id": "fire_eel", "name": "Fire Eel / Taurus captures", "region": "Crimson Isle", "loop": "Fishing + Hunting", "anytime": True, "movement": "fixed", "status": "user-rejected", "reason": "User tested and found washed; intentionally excluded from recommendations.", "sources": []},
    {"id": "silentdepth", "name": "Silentdepth treasure", "region": "Crystal Hollows", "loop": "Treasure fishing", "anytime": True, "movement": "fixed", "status": "user-rejected", "reason": "User tested and found washed; stale historical prices were misleading.", "sources": []},
    {"id": "lanternfish", "name": "Abyssal Lanternfish treasure", "region": "Dwarven Mines", "loop": "Treasure fishing", "anytime": True, "movement": "fixed", "status": "user-rejected", "reason": "User tested and found washed; stale historical prices were misleading.", "sources": []},
]


def bounded_number(value: Any, label: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number")
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number") from None
    if not math.isfinite(result) or result < minimum or result > maximum:
        raise ValueError(f"{label} must be between {minimum:g} and {maximum:g}")
    return result


def squid_share(*, squid_hat: bool, common_hook: bool, other_common_weight: float = 800) -> float:
    """Squid share using exact basic-water weights unless overridden.

    Other-common weight 800 (Sea Walker) is verified by the current Wiki.
    The input is left editable only for sensitivity experiments.
    """
    common = bounded_number(other_common_weight, "Other common weight", 0, BASE_OTHER_WEIGHT)
    squid = SQUID_WEIGHT * (2 if squid_hat else 1) * (1.25 if common_hook else 1)
    others = common * (1.25 if common_hook else 1) + (BASE_OTHER_WEIGHT - common)
    return squid / (squid + others)


def _lookup(prices: dict, key: str, side: str) -> float | None:
    """Get a validated market price. Never turn missing into 0."""
    if key not in prices or prices[key] is None:
        return None
    record = prices[key]
    if not isinstance(record, dict) or side not in record:
        return None
    try:
        number = float(record[side])
    except (ValueError, TypeError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def calculate_squid(params: dict, prices: dict, *, prices_live: bool = False) -> dict:
    """Calculate modelled loot only, then communicate coverage and missing data.

    This is NOT a prediction of full loot/hour. Important unmodelled loot remains.
    """
    p = {
        "reels_per_hour": bounded_number(params.get("reels_per_hour", 1050), "Reels/hour", 0, 5000),
        "sea_creature_chance": bounded_number(params.get("sea_creature_chance", 100), "Sea Creature Chance", 0, 100),
        "double_hook_chance": bounded_number(params.get("double_hook_chance", 30), "Double Hook Chance", 0, 100),
        "other_common_weight": 800,  # Wiki Sea Walker weight, not a player stat.
        "fishing_level": bounded_number(params.get("fishing_level", 50), "Fishing level", 1, 50),
        "tracking": bounded_number(params.get("tracking", 0), "Tracking", 0, 300),
        "time_of_day": str(params.get("time_of_day", "day")),
        "hydra_kills_per_catch": bounded_number(params.get("hydra_kills_per_catch", 2), "Hydra kills per catch", 1, 2),
        "squid_pet_level": bounded_number(params.get("squid_pet_level", 100), "Squid Pet level", 1, 100),
        "squid_pet_rarity": str(params.get("squid_pet_rarity", "LEGENDARY")).upper(),
        "natural_spawn_efficiency": bounded_number(params.get("natural_spawn_efficiency", 60), "Natural spawn efficiency", 0, 100),
        "bait_saved_percent": bounded_number(params.get("bait_saved_percent", 10), "Bait conservation", 0, 100),
        "ink_yield_multiplier": bounded_number(params.get("ink_yield_multiplier", 1), "Ink yield multiplier", 0, 10),
        "rain_price_per_min": bounded_number(params.get("rain_price_per_min", 5000), "Rain cost/min", 0, 100000),
        "manual_bait_price": bounded_number(params.get("manual_bait_price", 0), "Manual bait price", 0, 1e8),
        "manual_ink_price": bounded_number(params.get("manual_ink_price", 0), "Manual ink price", 0, 1e8),
        "manual_lily_price": bounded_number(params.get("manual_lily_price", 0), "Manual lily price", 0, 1e8),
    }
    for key in ("squid_hat", "common_hook", "squid_pet", "rain", "pay_rain"):
        p[key] = bool(params.get(key, {"squid_hat": True, "common_hook": True, "squid_pet": True, "rain": True, "pay_rain": True}[key]))
    p["bait"] = str(params.get("bait", "FISH_BAIT"))
    if p["squid_pet_rarity"] not in ("COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY"):
        raise ValueError("Unknown Squid Pet rarity")
    if p["time_of_day"] not in ("day", "night"):
        raise ValueError("Time of day must be day or night")
    if p["bait"] not in ("FISH_BAIT", "SPIKED_BAIT", "MINNOW_BAIT", "NONE", "LIGHT_BAIT", "DARK_BAIT", "WHALE_BAIT"):
        raise ValueError("Unsupported bait choice")

    # Supplying 'reels/hour' means actions, NOT already-counted sea creatures.
    sea_creature_reels = p["reels_per_hour"] * p["sea_creature_chance"] / 100
    total_sc = sea_creature_reels * (1 + p["double_hook_chance"] / 100)
    # Use the complete eligible pool, including Fishing unlocks and Tracking.
    from engine.pools import rarity_weighted_pool, project_pool
    weighted = rarity_weighted_pool("basic_water", fishing_level=p["fishing_level"], tracking=p["tracking"],
        bait=p["bait"], time_of_day=p["time_of_day"], hook="COMMON_HOOK" if p["common_hook"] else "NONE", squid_hat=p["squid_hat"])
    share = next(row["probability"] for row in weighted if row["name"] == "Squid")
    fished_squids = total_sc * share
    # Wiki: 66.6% chance for 1–2 natural squids every 11s, conditional on cap.
    # Efficiency is an explicit assumption accounting for spawn cap and clearing.
    natural_ceiling = 3600 / 11 * (2/3) * 1.5
    natural_squids = natural_ceiling * p["natural_spawn_efficiency"] / 100 if p["rain"] else 0
    total_squids = fished_squids + natural_squids
    pet_max_chance={"COMMON": 0.50, "UNCOMMON": 0.75, "RARE": 0.75, "EPIC": 1.0, "LEGENDARY": 1.0}
    pet_mult = 1 + pet_max_chance[p["squid_pet_rarity"]]*p["squid_pet_level"]/100 if p["squid_pet"] else 1
    # 2–3 ink and 1–2 Lily Pad per Wiki Squid. Looting/additional game modifiers
    # unvalidated; user-controlled ink yield multiplier is explicitly an assumption.
    ink_count = total_squids * 2.5 * pet_mult * p["ink_yield_multiplier"]
    lily_count = total_squids * 1.5 * pet_mult
    # Decompose expected ink output. This does not invent an unverified Looting multiplier.
    base_ink_fished = fished_squids * 2.5
    base_ink_natural = natural_squids * 2.5
    ink_after_pet = (base_ink_fished + base_ink_natural) * pet_mult
    spent_bait = 0 if p["bait"] == "NONE" else p["reels_per_hour"] * (1 - p["bait_saved_percent"] / 100)

    ink_price = p["manual_ink_price"] if p["manual_ink_price"] > 0 else _lookup(prices, "INK_SACK", "instant_sell")
    lily_price = p["manual_lily_price"] if p["manual_lily_price"] > 0 else _lookup(prices, "WATER_LILY", "instant_sell")
    bait_price = 0 if p["bait"] == "NONE" else (p["manual_bait_price"] if p["manual_bait_price"] > 0 else _lookup(prices, p["bait"], "instant_buy"))
    missing = []
    if ink_price is None: missing.append("INK_SACK instant-sell price unavailable")
    if lily_price is None: missing.append("WATER_LILY instant-sell price unavailable")
    if bait_price is None: missing.append(f"{p['bait']} instant-buy price unavailable")
    price_complete = not missing
    income_ink = ink_count * ink_price if ink_price is not None else None
    income_lily = lily_count * lily_price if lily_price is not None else None
    cost_bait = spent_bait * bait_price if bait_price is not None else None
    cost_rain = 60 * p["rain_price_per_min"] if p["rain"] and p["pay_rain"] else 0
    # No fake net when any priced modeled component is missing.
    modelled_net = income_ink + income_lily - cost_bait - cost_rain if price_complete else None
    # Always incomplete as full-method revenue: Squid boots, pet treasure, enchanted ink,
    # other sea creatures, non-sea-creature catch loot, rare dyes are not modelled.
    warnings = [
        "PARTIAL LOOT: other sea creatures, treasure, rare dyes, squid pets, inkling and conditional drops are not priced.",
        "POOL MODEL: Wiki weights, Fishing unlocks and applicable modifiers are calculated automatically. Sea Walker is the only other COMMON basic-water creature.",
        "Natural-spawn efficiency and any extra ink yield from Looting are not independently validated; extra yield defaults to 1×.",
    ]
    if not prices_live:
        warnings.append("Live Bazaar prices not verified; any manual values are user assumptions.")
    if not price_complete:
        warnings.append("Missing required market prices. Modelled net is withheld rather than assuming zero.")
    pool_projection = project_pool({
        "pool": "basic_water", "reels_per_hour": p["reels_per_hour"],
        "sea_creature_chance": p["sea_creature_chance"], "double_hook_chance": p["double_hook_chance"],
        "fishing_level": p["fishing_level"], "tracking": p["tracking"],
        "bait": p["bait"], "time_of_day": p["time_of_day"],
        "hook": "COMMON_HOOK" if p["common_hook"] else "NONE",
        "squid_hat": p["squid_hat"], "squid_pet": p["squid_pet"], "squid_pet_multiplier": pet_mult,
        "natural_squids_per_hour": natural_squids,
        "hydra_kills_per_catch": p["hydra_kills_per_catch"],
        "magic_find": params.get("magic_find", 0), "looting_level": params.get("looting_level", 0),
        "bait_saved_percent": p["bait_saved_percent"],
        "manual_bait_price": p["manual_bait_price"],
    }, prices, prices_live=prices_live)
    priced_creature_net = (pool_projection["known_subtotal_after_bait"] - cost_rain
                           if pool_projection["known_subtotal_after_bait"] is not None else None)
    warnings.append("All 10 basic-water creature drop tables included in the creature projection. Bazaar-priced loot is itemized; unpriced AH items, special loot rolls and non-creature catches remain excluded.")
    return {
        "method_id": "birch_squid", "model_status": "partial-model", "is_full_method_profit": False,
        "inputs": p, "squid_share": share,
        "fished_squids_per_hour": fished_squids, "natural_squids_per_hour": natural_squids,
        "sea_creatures_per_hour": total_sc, "ink_per_hour": ink_count, "lily_pads_per_hour": lily_count,
        "ink_breakdown": {"base_ink_from_fished_squids": base_ink_fished, "base_ink_from_natural_squids": base_ink_natural, "squid_pet_multiplier": pet_mult, "ink_after_pet": ink_after_pet, "unverified_extra_multiplier": p["ink_yield_multiplier"], "unit": "regular Ink Sac equivalents", "base_ink_per_squid": 2.5},
        "bait_used_per_hour": spent_bait, "bait_unit_price": bait_price,
        "ink_unit_price": ink_price, "lily_unit_price": lily_price,
        "gross_ink": income_ink, "gross_lily": income_lily,
        "cost_bait": cost_bait, "cost_rain": cost_rain,
        "modelled_net": modelled_net,
        "price_complete": price_complete, "prices_live": prices_live,
        "pool_projection": pool_projection, "priced_creature_net": priced_creature_net,
        "missing": missing, "warnings": warnings,
        "sources": SQUID_SOURCES,
        "validation_target": {"user_observed_total_per_hour": [30_000_000, 35_000_000], "user_observed_ink_per_hour": [20_000_000, 25_000_000], "note": "These are independent observations, not hardcoded predictions."},
    }


def sensitivity(params: dict, prices: dict, *, prices_live: bool = False) -> dict:
    base = calculate_squid(params, prices, prices_live=prices_live)
    variants = {}
    for name, change in (("low", 0.85), ("base", 1.0), ("high", 1.15)):
        p = dict(params)
        p["reels_per_hour"] = base["inputs"]["reels_per_hour"] * change
        variants[name] = calculate_squid(p, prices, prices_live=prices_live)["modelled_net"]
    base["sensitivity"] = variants
    return base


def rank_methods(methods: list[dict]) -> list[dict]:
    """Never rank a method as validated using missing or partial-model profits."""
    eligible = [m for m in methods if m.get("is_full_method_profit") is True and m.get("prices_live") is True and m.get("modelled_net") is not None and m.get("anytime") is True]
    return sorted(eligible, key=lambda m: m["modelled_net"], reverse=True)


def payback_hours(extra_gear_cost: float, new_profit: float, baseline_profit: float) -> float | None:
    for label, v in (("Extra gear cost",extra_gear_cost),("New profit",new_profit),("Baseline",baseline_profit)):
        bounded_number(v,label,0,1e15)
    difference = new_profit - baseline_profit
    return extra_gear_cost / difference if difference > 0 else None
