"""Server-side, keyless Hypixel Bazaar proxy with strict price direction and TTL."""
import time
import threading
import math
import requests

URL = 'https://api.hypixel.net/v2/skyblock/bazaar'
TTL_SECONDS = 180


def parse_bazaar_product(product: dict) -> dict:
    """Map Hypixel's order-side quick-status prices to player transactions.

    Hypixel's quick_status.sellPrice represents the best BUY orders, so a
    player's INSTANT SELL receives sellPrice. quick_status.buyPrice
    represents the cheapest SELL offers, so a player's INSTANT BUY pays
    buyPrice. Their names describe the order/trade side, not the player's
    instant action. Weighted averages are indicative, not executable quotes.
    """
    if not isinstance(product, dict):
        raise ValueError('Invalid Bazaar product')
    quick = product.get('quick_status')
    if not isinstance(quick, dict):
        raise ValueError('Missing Bazaar quick_status')
    sell = float(quick['sellPrice'])
    buy = float(quick['buyPrice'])
    if not math.isfinite(sell) or not math.isfinite(buy) or sell <= 0 or buy <= 0 or sell > buy * 10:
        raise ValueError('Invalid Bazaar prices')
    return {'instant_sell': sell, 'instant_buy': buy, 'buy_volume': quick.get('buyVolume'), 'sell_volume': quick.get('sellVolume')}


class Bazaar:
    def __init__(self, fetcher=None, clock=None):
        self.fetcher = fetcher or self._network
        self.clock = clock or time.time
        self._lock = threading.Lock()
        self._data = None
        self._checked = 0.0
        self._api_updated = None
        self._last_error = None
        self._failed_at = 0.0

    @staticmethod
    def _network():
        response = requests.get(URL, timeout=8, headers={'User-Agent':'SkyBlockFishingEngine/0.1 (public price calculator)'})
        response.raise_for_status()
        return response.json()

    def get(self, refresh=False):
        with self._lock:
            if not refresh and self._data is not None and self.clock() - self._checked < TTL_SECONDS:
                return self._response('live-cache')
            if not refresh and self._data is None and self._failed_at and self.clock()-self._failed_at < 60:
                return self._response('unavailable')
            try:
                payload = self.fetcher()
                if not isinstance(payload, dict) or payload.get('success') is not True or not isinstance(payload.get('products'), dict):
                    raise ValueError('Hypixel returned invalid or unsuccessful payload')
                data = {}
                for key, item in payload['products'].items():
                    try:
                        data[key] = parse_bazaar_product(item)
                    except (TypeError,ValueError,KeyError):
                        continue
                if not data:
                    raise ValueError('No valid Bazaar product prices')
                self._data = data
                self._checked = self.clock()
                self._api_updated = payload.get('lastUpdated')
                self._last_error = None
                self._failed_at = 0.0
                return self._response('live')
            except (requests.RequestException, KeyError, ValueError, TypeError, OverflowError) as exc:
                self._last_error = str(exc)[:250]
                self._failed_at = self.clock()
                return self._response('stale' if self._data else 'unavailable')

    def _response(self, state):
        # Stale prices must NEVER be treated as verified current prices.
        is_live = state in ('live', 'live-cache')
        return {'state':state, 'live':is_live, 'checked_at':self._checked or None,
                'api_last_updated':self._api_updated, 'age_seconds': round(self.clock()-self._checked) if self._checked else None,
                'last_error': self._last_error, 'products':self._data or {}, 'product_count':len(self._data or {}), 'source':URL}
