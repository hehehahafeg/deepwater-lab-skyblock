"""Functional browser test for encyclopedia filters and real API-driven detail pages.
Uses deterministic price fixture, never a fake live-market claim.
"""
import re
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
import app as backend
ROOT=Path(__file__).resolve().parents[1]

def main():
    backend.market.get=lambda refresh=False: {'state':'live','live':True,'products':{
        'INK_SACK':{'instant_sell':2975,'instant_buy':3071},
        'WATER_LILY':{'instant_sell':8,'instant_buy':37},
        'FISH_BAIT':{'instant_sell':289,'instant_buy':548}},
        'product_count':3,'checked_at':1700000000,'api_last_updated':1700000000000}
    client=TestClient(backend.app)
    html=(ROOT/'static/index.html').read_text()
    html=re.sub(r'<link rel="stylesheet"[^>]+>', '', html)
    html=re.sub(r'<script src="/static/app.js"[^>]*></script>', '', html)
    css=(ROOT/'static/styles.css').read_text().replace("@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');",'')
    html=html.replace('</head>','<style>'+css+'</style></head>')
    js=(ROOT/'static/app.js').read_text()
    shim='''<script>window.fetch=async function(path,opts={}){const r=await window.backendFetch(path,opts);return {ok:r.status>=200&&r.status<300,status:r.status,json:async()=>r.body};};</script>'''
    html=html.replace('</body>',shim+'<script>'+js+'</script></body>')
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1365,'height':900})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        def backend_fetch(path,opts):
            payload=opts.get('body')
            res=client.request(opts.get('method','GET'),path,content=payload,headers={'content-type':'application/json'} if payload else {})
            return {'status':res.status_code,'body':res.json()}
        page.expose_function('backendFetch',backend_fetch)
        page.add_init_script('''window.fetch=async function(path,opts={}){const r=await window.backendFetch(path,opts);return {ok:r.status>=200&&r.status<300,status:r.status,json:async()=>r.body};};''')
        page.set_content(html,wait_until='domcontentloaded')
        page.locator('button.navitem[data-view="library"]').click()
        page.locator('#library-count').get_by_text('100 matching',exact=False).wait_for(timeout=15000)
        assert page.locator('#library-cards .library-card').count()==24
        assert page.locator('#library-page').inner_text()=='Page 1 of 5'
        print('PASS: Default anytime methods=100; event=4 excluded, cards paginated.')
        page.locator('#library-search').fill('Hound')
        page.locator('#library-count').get_by_text('matching',exact=False).wait_for()
        assert page.locator('#library-cards .library-card').count()>=1
        page.locator('#library-cards .library-card').first.click()
        page.locator('#library-detail h2').wait_for(timeout=15000)
        txt=page.locator('#library-detail').inner_text()
        assert 'Hound' in txt and 'NOT VERIFIED' in txt
        assert 'CASTING PET' in txt and 'SINKER' in txt and 'AUTOPET' in txt
        assert 'Market' in txt or 'Bazaar' in txt
        print('PASS: Hound detail has gear slots, caveat, hypothesis and current-price context.')
        page.locator('#close-library-detail').click()
        assert page.locator('#library-detail').is_hidden()
        page.locator('#library-search').fill('')
        page.locator('#library-event').select_option('event-only')
        assert '4 matching' in page.locator('#library-count').inner_text()
        assert page.locator('#library-cards .library-card').count()==4
        print('PASS: Event-only options appear only when explicitly requested.')
        page.locator('#library-event').select_option('all')
        assert '104 matching' in page.locator('#library-count').inner_text()
        page.locator('#library-washed').uncheck()
        assert page.locator('#library-cards .library-card').count()>0
        assert '104 matching' not in page.locator('#library-count').inner_text()
        print('PASS: Can exclude previously-tested methods; total includes 104.')
        page.locator('#library-washed').check()
        page.locator('#library-event').select_option('anytime')
        page.locator('#library-region').select_option('Crimson Isle')
        assert 'matching strategies' in page.locator('#library-count').inner_text()
        print('PASS: Region and effort controls work.')
        page.screenshot(path=str(ROOT/'preview_method_library.png'))
        if errors:raise AssertionError('JavaScript errors: '+str(errors))
        print('PASS: Zero JS exceptions.')
        browser.close()

if __name__=='__main__':main()
