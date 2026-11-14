"""Fail-closed Bazaar snapshot and order-book depth checks.

This module is opt-in: existing app estimates are not silently changed.
"""
import math
import time

MAX_AGE_SECONDS = 300

def validate_snapshot(payload, now=None, max_age_seconds=MAX_AGE_SECONDS):
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise ValueError("Bazaar response was unsuccessful")
    if not isinstance(payload.get("products"), dict) or not payload["products"]:
        raise ValueError("Bazaar products missing")
    timestamp = payload.get("lastUpdated")
    if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
        raise ValueError("Bazaar timestamp missing")
    # Hypixel Bazaar lastUpdated is Unix milliseconds, including in synthetic tests.
    timestamp = float(timestamp) / 1000
    now = time.time() if now is None else now
    if not math.isfinite(timestamp) or not isinstance(now, (int, float)) or not math.isfinite(now):
        raise ValueError("Bazaar timestamp invalid")
    if timestamp > now + 30 or now - timestamp > max_age_seconds:
        raise ValueError("Bazaar snapshot stale or future-dated")
    return payload["products"]

def executable_quote(products, product_id, quantity, action):
    """Return depth-weighted price for a player instant_sell or instant_buy.

    Hypixel buy_summary represents standing BUY orders (player instant sell).
    Hypixel sell_summary represents standing SELL orders (player instant buy).
    Refuse quantities exceeding published order depth.
    """
    if action not in ("instant_sell", "instant_buy"):
        raise ValueError("Invalid transaction direction")
    if isinstance(quantity, bool) or not isinstance(quantity, (int, float)) or not math.isfinite(quantity) or quantity <= 0:
        raise ValueError("Quantity must be positive and finite")
    if product_id not in products:
        raise ValueError("Product absent from Bazaar snapshot")
    side = "buy_summary" if action == "instant_sell" else "sell_summary"
    orders = products[product_id].get(side)
    if not isinstance(orders, list) or not orders:
        raise ValueError("Order-book side unavailable")
    # Sort by executable price rather than assuming the API supplies ordered levels.
    # Validate the entire book before using any level, even if the requested fill
    # would otherwise complete at the first level.
    levels = []
    for order in orders:
        if not isinstance(order, dict):
            raise ValueError("Invalid order-book level")
        price, amount = order.get("pricePerUnit"), order.get("amount")
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0 for x in (price, amount)):
            raise ValueError("Invalid order-book price or quantity")
        levels.append((float(price), float(amount)))
    levels.sort(key=lambda level: level[0], reverse=action == "instant_sell")
    remaining = float(quantity)
    total = 0.0
    for price, amount in levels:
        fill = min(remaining, amount)
        total += fill * price
        remaining -= fill
        if remaining <= 1e-9:
            return {"product_id": product_id, "action": action, "quantity": quantity,
                    "total_coins": total, "unit_price": total / quantity,
                    "quote_type": "published_order_depth"}
    raise ValueError("Insufficient published order-book depth")
