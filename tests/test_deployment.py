from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_hosted_blueprint_has_free_python_web_server():
    text = (ROOT / 'render.yaml').read_text()
    assert 'type: web' in text
    assert 'runtime: python' in text
    assert 'plan: free' in text
    assert 'uvicorn app:app --host 0.0.0.0 --port $PORT' in text
    assert 'healthCheckPath: /api/health' in text


def test_webpage_uses_same_origin_api():
    js = (ROOT / 'static/app.js').read_text()
    assert "api('/api/prices'" in js
    assert "post('/api/pools/project'" in js
    assert 'setInterval(() =>' in js
    assert '180000' in js


def test_hypixel_api_is_server_side_and_keyless():
    market = (ROOT / 'engine/market.py').read_text()
    assert "https://api.hypixel.net/v2/skyblock/bazaar" in market
    assert "TTL_SECONDS = 180" in market
    assert 'requests.get(URL' in market
    assert 'API_KEY' not in market
