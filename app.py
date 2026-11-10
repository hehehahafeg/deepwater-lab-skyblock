"""Run: python -m uvicorn app:app --host 127.0.0.1 --port 8765"""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from engine.market import Bazaar
from engine.models import CATALOG, SQUID_SOURCES, sensitivity, rank_methods, payback_hours
from engine.pools import public_catalog, project_pool

ROOT=Path(__file__).resolve().parent
app=FastAPI(title='SkyBlock Fishing Profit Engine',version='0.3.0')
app.mount('/static', StaticFiles(directory=str(ROOT/'static')), name='static')
market=Bazaar()

class CalcRequest(BaseModel):
    params:dict=Field(default_factory=dict)
    manual_prices:dict=Field(default_factory=dict)
    use_live_market:bool=True

class PoolRequest(BaseModel):
    params:dict=Field(default_factory=dict)
    use_live_market:bool=True

class PaybackRequest(BaseModel):
    extra_gear_cost:float
    new_profit:float
    baseline_profit:float

@app.get('/')
def index():
    return FileResponse(ROOT/'static'/'index.html')

@app.get('/api/health')
def health():
    return {'status':'ok','version':'0.3.0','market_requires_network':True,'engine_scope':'8 anytime weighted pools; 18 partial creature drop tables; partial squid model; no proven automated discovery'}

@app.get('/api/methods')
def methods():
    return {'catalog':CATALOG, 'approved_full_profit_methods':[], 'disclaimer':'No complete, price-verified methods yet; ranking intentionally empty.'}

@app.get('/api/prices')
def prices(refresh:bool=False):
    return market.get(refresh)

@app.post('/api/calculate/squid')
def calculate(payload:CalcRequest):
    snapshot=market.get() if payload.use_live_market else {'live':False,'products':{}}
    prices=dict(snapshot['products']) if snapshot['live'] else {}
    # A user can enter prices to perform offline calculations; never label them live.
    for key, val in payload.manual_prices.items():
        if isinstance(val,dict):
            prices[key]=val
    try:
        return sensitivity(payload.params,prices,prices_live=snapshot['live'] and not bool(payload.manual_prices))
    except ValueError as e:
        raise HTTPException(status_code=422,detail=str(e))

@app.get('/api/pools')
def pools():
    return public_catalog()

@app.post('/api/pools/project')
def pools_project(payload:PoolRequest):
    snapshot=market.get() if payload.use_live_market else {'live':False,'products':{}}
    try:
        return project_pool(payload.params,snapshot['products'] if snapshot['live'] else {},prices_live=snapshot['live'])
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc))

@app.post('/api/payback')
def payback(payload:PaybackRequest):
    try:
        return {'hours':payback_hours(payload.extra_gear_cost,payload.new_profit,payload.baseline_profit)}
    except ValueError as e:
        raise HTTPException(status_code=422,detail=str(e))

@app.get('/api/rankings')
def rankings():
    return {'ranked':rank_methods([]),'status':'no-fully-verified-methods','reason':'Prevent misleading profit recommendations until complete drop/market models exist.'}

@app.get('/api/sources')
def sources():
    return {'sources':SQUID_SOURCES, 'pool_catalog':public_catalog()['sources'], 'limitations':['Eight creature spawn pools modeled; only 18 of 55 individual loot tables checked','Partial modeled earnings cannot be treated as total profit','User-reported benchmarks are independent observations','Live API may be unavailable in restricted hosting environments']}

@app.post('/api/experiments/squid')
def experiment_squid(payload:CalcRequest):
    """Enumerate gear variations as *partial* estimates. Never certify a full method."""
    snapshot=market.get() if payload.use_live_market else {'live':False,'products':{}}
    prices=dict(snapshot['products']) if snapshot['live'] else {}
    for key,val in payload.manual_prices.items():
        if isinstance(val,dict):prices[key]=val
    variations=[]
    try:
        for hat in (False,True):
            for hook in (False,True):
                for pet in (False,True):
                    for rain in (False,True):
                        p={**payload.params,'squid_hat':hat,'common_hook':hook,'squid_pet':pet,'rain':rain,'pay_rain':rain and payload.params.get('pay_rain',True)}
                        r=sensitivity(p,prices,prices_live=snapshot['live'] and not bool(payload.manual_prices))
                        variations.append({'label': f"{'Squid Hat' if hat else 'Full armor'} · {'Common Hook' if hook else 'No Hook'} · {'Squid Pet' if pet else 'No Squid Pet'} · {'Rain' if rain else 'Dry'}",'modelled_net':r['modelled_net'],'ink_per_hour':r['ink_per_hour'],'model_status':'partial','full_profit_verified':False,'config':{'squid_hat':hat,'common_hook':hook,'squid_pet':pet,'rain':rain}})
    except ValueError as e:
        raise HTTPException(status_code=422,detail=str(e))
    variations.sort(key=lambda r: (r['modelled_net'] is not None,r['modelled_net'] if r['modelled_net'] is not None else -1), reverse=True)
    return {'variants':variations,'count':len(variations),'ranked_on':'modeled ink+lily+bait+rain only','not_full_profit':True,'prices_live':snapshot['live'] and not bool(payload.manual_prices),'warning':'This is only a within-squid sensitivity lab. Other-method discovery requires more verified mechanics.'}
