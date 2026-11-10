import pytest
from fastapi.testclient import TestClient
import app as app_module

client=TestClient(app_module.app)

@pytest.fixture(autouse=True)
def deterministic_market(monkeypatch):
    def fake_market(refresh=False):
        return {'state':'live','live':True,'products':{
          'INK_SACK':{'instant_sell':2000,'instant_buy':2200},
          'WATER_LILY':{'instant_sell':30,'instant_buy':35},
          'FISH_BAIT':{'instant_sell':120,'instant_buy':180}}, 'product_count':3}
    monkeypatch.setattr(app_module.market,'get',fake_market)


def test_homepage_delivered():
    r=client.get('/');assert r.status_code==200;assert 'SkyBlock Fishing Profit Engine' in r.text

def test_health():
    assert client.get('/api/health').json()['status']=='ok'

def test_prices():
    r=client.get('/api/prices');assert r.status_code==200;assert r.json()['products']['INK_SACK']['instant_sell']==2000

def test_catalog_contains_rejections():
    r=client.get('/api/methods').json();assert r['approved_full_profit_methods']==[]
    assert any(m['status']=='user-rejected' for m in r['catalog'])
    assert all(m['anytime'] for m in r['catalog'])

def test_calculate_live_fake_fixture():
    r=client.post('/api/calculate/squid',json={'params':{'reels_per_hour':100,'rain':False}})
    assert r.status_code==200
    j=r.json();assert j['price_complete'];assert j['prices_live'];assert j['modelled_net'] is not None
    assert not j['is_full_method_profit']

def test_manual_override_not_relabelled_live():
    r=client.post('/api/calculate/squid',json={'params':{'rain':False},'manual_prices':{'INK_SACK':{'instant_sell':1000,'instant_buy':1100}}})
    assert r.status_code==200 and not r.json()['prices_live']

def test_invalid_inputs_return_422():
    r=client.post('/api/calculate/squid',json={'params':{'sea_creature_chance':10000}})
    assert r.status_code==422

def test_sixteen_variants_unverified():
    r=client.post('/api/experiments/squid',json={'params':{'rain':False}})
    assert r.status_code==200
    j=r.json();assert j['count']==16 and all(not x['full_profit_verified'] for x in j['variants'])
    assert j['variants'][0]['modelled_net']>=j['variants'][-1]['modelled_net']

def test_rankings_empty():
    j=client.get('/api/rankings').json();assert j['ranked']==[]

def test_payback_endpoint():
    assert client.post('/api/payback',json={'extra_gear_cost':200000000,'new_profit':50000000,'baseline_profit':40000000}).json()['hours']==20

def test_sources_endpoint():
    assert 'squid' in client.get('/api/sources').json()['sources']
