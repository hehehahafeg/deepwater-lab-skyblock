'use strict';
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = n => n === null || n === undefined || !Number.isFinite(Number(n)) ? '—' : Number(n).toLocaleString('en-US',{maximumFractionDigits:0});
const short = n => n === null || n === undefined || !Number.isFinite(Number(n)) ? 'UNAVAILABLE' : (Math.abs(n)>=1e6 ? (n/1e6).toFixed(2)+'M' : Math.abs(n)>=1e3 ? (n/1e3).toFixed(1)+'K' : money(n));
const fmt = n => Number(n).toLocaleString('en-US',{maximumFractionDigits:2});
const readNum = (id, fallback=0) => $(id)?.value?.trim() === '' ? fallback : Number($(id).value);
const state = {poolCatalog:null, market: null, methods: [], currentView: 'overview', server: false, latestCalculation: null, tests: [], experimental:false, lastMarketPollAt: 0};
const api = async(path, options) => {
  const res = await fetch(path,{cache:'no-store',...options});
  const obj = await res.json().catch(()=>({}));
  if (!res.ok) throw Error(obj.detail || `HTTP ${res.status}`);
  return obj;
};
const post = (path, obj) => api(path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(obj)});
const MARKET_ITEMS = ['INK_SACK','WATER_LILY','FISH_BAIT','SPIKED_BAIT','MINNOW_BAIT','ENCHANTED_INK_SACK','HOTSPOT_BAIT','HOT_BAIT','SHARK_BAIT'];
const shortMethods = [
  {id:'birch_squid',name:'Birch Park · Squid density',region:'The Park',status:'partial-model',reason:'All basic-water creatures included. AH/treasure still incomplete.',movement:'fixed'},
  {id:'bayou_hotspot',name:'Bayou hotspot fishing',region:'Backwater Bayou',status:'requires-model',reason:'Complete creature drops missing.',movement:'small'},
  {id:'stationary_lava',name:'Stationary lava fishing',region:'Crimson Isle',status:'requires-model',reason:'Thunder Flash books and drops not yet validated.',movement:'fixed'},
  {id:'atoll_puddle',name:'Lotus Atoll · Puddle Jumper',region:'Lotus Atoll',status:'requires-model',reason:'Requires validated loot catalog.',movement:'small'}
];

function navigate(view) {
  for(const item of document.querySelectorAll('.view')) item.classList.toggle('hidden',item.id!==`view-${view}`);
  for(const item of document.querySelectorAll('.navitem, .mobileitem')) item.classList.toggle('active',item.dataset.view===view);
  state.currentView = view;
  $('crumb').textContent = view.toUpperCase();
  window.scrollTo({top:0,behavior:'smooth'});
  if(view==='sessions') renderSessions();
  if(view==='markets') renderMarket();
}

document.addEventListener('click',ev=>{const tgt=ev.target.closest('[data-view], [data-goto]');if(tgt)navigate(tgt.dataset.view||tgt.dataset.goto);});

function marketStatus() {
  const m=state.market;
  const status=m?.state||'unavailable';
  const live=Boolean(m?.live);
  $('api-pill').className='pill '+(live?'':m?.state==='stale'?'warn':'bad');
  $('api-pill').innerHTML='<span class="dot"></span>'+esc(live?'LIVE MARKET':status==='stale'?'STALE / UNVERIFIED':'PRICE DATA UNAVAILABLE');
  $('stat-items').textContent=live?money(m.product_count):'—';
  $('stat-items-label').textContent=live?'Verified API response':m?.last_error?'API unavailable':'Server not connected';
  $('market-number').textContent=live?money(m.product_count):'—';
  $('market-header-state').textContent=live?'LIVE API':status.toUpperCase();
  $('market-header-state').className='status '+(live?'status-green':'status-amber');
  $('market-explanation').textContent=live?`Last checked ${new Date(m.checked_at*1000).toLocaleString()}. Hypixel weighted average prices; execution varies.`:`No confirmed live API data. ${m?.last_error||'Start the Python server for real market prices.'} Any manual estimates are explicitly labelled.`;
}
async function loadMarket(refresh=false){
  $('api-pill').innerHTML='<span class="dot"></span> Querying market…';
  try {state.market=await api('/api/prices'+(refresh?'?refresh=true':''));state.server=true;state.lastMarketPollAt=Date.now();}
  catch(err){state.market={live:false,state:'unavailable',products:{},last_error:'App backend not running ('+err.message+')'};state.server=false;}
  marketStatus();renderMarket();
}

function renderMethods(){
  const entries=state.methods.length?state.methods:shortMethods;
  const tags={'partial-model':'PARTIAL MODEL','requires-model':'NOT PRICED','user-tested':'OVERLAP','user-rejected':'EXCLUDED'};
  $('overview-methods').innerHTML=entries.slice(0,3).map(m=>`<div class="method-mini"><strong>${esc(m.name)}</strong><small>${esc(m.region)} · ${esc(tags[m.status]||m.status)}</small></div>`).join('');
  $('method-grid').innerHTML=entries.map(m=>`<div class="method-card"><span class="status ${m.status==='partial-model'?'status-amber':'status-muted'}">${esc(tags[m.status]||m.status)}</span><h3>${esc(m.name)}</h3><div class="meta">${esc(m.region)} · ${esc(m.movement)} movement · Anytime</div><p class="reason">${esc(m.reason)}</p><div class="micro">${m.status==='partial-model'?'PARTIAL OUTPUT ONLY':'NOT ELIGIBLE FOR RANKED PROFITS'}</div></div>`).join('');
}
async function loadMethods(){try{let result=await api('/api/methods');state.methods=result.catalog||[];state.server=true;}catch(err){state.methods=shortMethods;}renderMethods();}

function getParams(){return {
 reels_per_hour:readNum('reels',1050),sea_creature_chance:readNum('scc',100),double_hook_chance:readNum('dh',30),ink_yield_multiplier:1,fishing_level:readNum('fishingLevel',50),tracking:readNum('trackingStat',0),hydra_kills_per_catch:readNum('hydraKills',2),time_of_day:$('fishingTime').value,
 squid_hat:$('squidHat').checked,common_hook:$('commonHook').checked,squid_pet:$('squidPet').checked,squid_pet_rarity:$('squidPetRarity').value,squid_pet_level:readNum('squidPetLevel',100),rain:$('rain').checked,pay_rain:$('payRain').checked,
 magic_find:readNum('squid-mf',0),looting_level:readNum('squid-looting',0),
 natural_spawn_efficiency:readNum('spawnEff',60),bait_saved_percent:readNum('baitSaved',10),bait:$('bait').value
};}
function getOverrides(){const o={};if(readNum('inkPrice')>0)o.INK_SACK={instant_sell:readNum('inkPrice'),instant_buy:readNum('inkPrice')};if(readNum('lilyPrice')>0)o.WATER_LILY={instant_sell:readNum('lilyPrice'),instant_buy:readNum('lilyPrice')};if(readNum('baitPrice')>0 && $('bait').value!=='NONE')o[$('bait').value]={instant_buy:readNum('baitPrice'),instant_sell:readNum('baitPrice')};return o;}
const moneyRow=(label,n,sign='')=>`<div><span>${esc(label)}</span><strong>${n===null?'UNPRICED':sign+money(n)}</strong></div>`;

// All ten ordinary-water creatures are accounted for separately.
// A missing auction price remains UNPRICED rather than being silently counted as 0.
function renderPoolBreakdown(pool){
  if(!pool) return '';
  const grouped=new Map();
  for(const creature of (pool.creatures||[])){
    for(const drop of (creature.drops||[])){
      if(!grouped.has(drop.name)) grouped.set(drop.name,{name:drop.name,units:0,coins:0,priced:true,price:drop.unit_price,tier:drop.tier});
      const item=grouped.get(drop.name);
      item.units+=drop.expected_units||0;
      if(drop.expected_coins===null || drop.expected_coins===undefined) item.priced=false;
      else item.coins+=drop.expected_coins;
      if(drop.tier==='jackpot') item.tier='jackpot';
    }
  }
  const items=[...grouped.values()].sort((a,b)=>(b.priced?b.coins:0)-(a.priced?a.coins:0));
  const itemRows=items.map(item=>'<tr><td>'+esc(item.name)+(item.tier==='jackpot'?' <span class="library-chip warn">JACKPOT</span>':'')+'</td><td>'+fmt(item.units)+'</td><td>'+(item.priced?short(item.coins):'UNPRICED')+'</td></tr>').join('');
  const creatures=(pool.creatures||[]).map(creature=>{
    const drops=(creature.drops||[]).map(drop=>'<div><span>'+esc(drop.name)+' · '+fmt(drop.expected_units)+' / hour'+(drop.tier==='jackpot'?' · jackpot':'')+'</span><strong>'+(drop.expected_coins===null?'UNPRICED':short(drop.expected_coins))+'</strong></div>').join('');
    return '<details class="creature-loot"><summary><span>'+esc(creature.name)+' <small>'+fmt(creature.expected_per_hour)+' catches/hr'+(creature.expected_kills_per_hour!==creature.expected_per_hour?' · '+fmt(creature.expected_kills_per_hour)+' kills/hr':'')+'</small></span><strong>'+fmt(creature.probability*100)+'%</strong></summary><div class="result-list">'+drops+'</div><a href="'+esc(creature.source)+'" target="_blank" rel="noopener noreferrer">Check source drop table ↗</a></details>';
  }).join('');
  const unpriced=(pool.unpriced||[]).length;
  return '<section class="full-loot"><h3>Unlocked basic-water creatures · detailed projection</h3>'
    +'<p class="loot-note">Base drop probabilities for creatures unlocked at your Fishing level. Item totals include direct enchanted drops where documented. Common and rare priced drops are included in the known subtotal; ultra-rare jackpot EV is separated. Existing raw ink converted into enchanted ink must not be counted twice.</p>'
    +'<div class="result-list">'
    +moneyRow('Common Bazaar loot/hour',pool.known_common_revenue)
    +moneyRow('Priced rare-drop base EV/hour',pool.known_rare_base_ev)
    +moneyRow('Ultra-rare jackpot EV (not regular income)',pool.known_jackpot_base_ev)
    +moneyRow('Bait cost/hour',pool.bait_cost)
    +'<div class="cut"><span>Unpriced drop entries</span><strong>'+money(unpriced)+'</strong></div></div>'
    +'<details class="loot-details" open><summary>Expected items per hour ('+money(items.length)+' types)</summary><div class="loot-table-wrap"><table class="loot-table"><thead><tr><th>Drop</th><th>Units/hr</th><th>Known value/hr</th></tr></thead><tbody>'+itemRows+'</tbody></table></div></details>'
    +'<details class="loot-details"><summary>Creature-by-creature catch and drop breakdown ('+money((pool.creatures||[]).length)+')</summary>'+creatures+'</details>'
    +'<p class="loot-note">'+unpriced+' entries still lack trustworthy live Bazaar or Auction House prices. No full-profit figure is claimed; other fishing catches, Looting and Magic Find may add unmodelled returns.</p></section>';
}

function renderCalc(r) {
  state.latestCalculation=r;
  const complete=r.priced_creature_net!==null && r.priced_creature_net!==undefined;
  const val=complete?short(r.priced_creature_net):'BAIT COST UNPRICED';
  $('calc-result').className='';
  $('calc-result').innerHTML=`<div class="result-main"><div class="result-caption">KNOWN PRICED SUBTOTAL · UNLOCKED CREATURES · COINS/HOUR</div><div class="result-value" style="color:${complete?'#98ebce':'#eebc84'}">${esc(val)}</div><div class="result-sub">${complete?'Not full method profit. '+(r.prices_live?'Live Bazaar inputs':'Manual or unverified prices'):'Required bait price missing. Full profit is never claimed.'}</div></div><div class="result-list">
  ${moneyRow('Estimated fished Squids/hour',r.fished_squids_per_hour)}${moneyRow('Natural Squids/hour',r.natural_squids_per_hour)}${moneyRow('Squid share of SC pool (%)',Number((r.squid_share*100).toFixed(2)))}
  ${moneyRow('Base ink from fished squids/hour',r.ink_breakdown?.base_ink_from_fished_squids)}${moneyRow('Base ink from natural squids/hour',r.ink_breakdown?.base_ink_from_natural_squids)}${moneyRow('Squid Pet multiplier (automatic)',r.ink_breakdown?.squid_pet_multiplier)}${moneyRow('Ink after Squid Pet/hour',r.ink_breakdown?.ink_after_pet)}${moneyRow('Looting expected drop factor',r.ink_breakdown?.looting_expected_multiplier)}${moneyRow('Ink after Looting/hour',r.ink_breakdown?.ink_after_looting)}${moneyRow('Total regular ink equivalents/hour',r.ink_per_hour)}${moneyRow('Ink revenue/hour',r.gross_ink)}${moneyRow('Lily Pad revenue/hour',r.gross_lily)}
  ${moneyRow('Bait cost/hour',r.cost_bait)}${moneyRow('Rain cost/hour',r.cost_rain)}
  <div class="cut"><span>Priced creature subtotal after bait and rain</span><strong>${complete?short(r.priced_creature_net):'UNAVAILABLE'}</strong></div>
  </div>${renderPoolBreakdown(r.pool_projection)}<div class="warning-box">◈ ${esc((r.missing||[]).length?'Missing: '+r.missing.join(' · '):'This is a partial model; missing Looting and other drop mechanics are NOT silently estimated.')}<br>${esc(r.warnings?.[1]||'')}</div>
  ${r.sensitivity.low!==null&&r.sensitivity.high!==null?`<div class="result-list"><div><span>Squid-only ±15% reel rate · lower / upper</span><strong>${short(r.sensitivity.low)} – ${short(r.sensitivity.high)}</strong></div></div>`:''}`;
}
async function runCalc(){
 $('calc-result').className='calc-empty';$('calc-result').textContent='Calculating…';
 try{const r=await post('/api/calculate/squid',{params:getParams(),manual_prices:getOverrides()});renderCalc(r);}
 catch(e){$('calc-result').className='';$('calc-result').innerHTML=`<div class="warning-box">Calculation blocked: ${esc(e.message)}. ${state.server?'Correct the input.':'Start the Python backend for verified calculations.'}</div>`;}
}
function resetCalc(){for(const [k,v] of [['reels','1050'],['scc','100'],['dh','30'],['fishingLevel','50'],['trackingStat','0'],['squidPetLevel','100'],['squid-mf','0'],['squid-looting','0'],['spawnEff','60'],['baitSaved','10'],['inkPrice',''],['lilyPrice',''],['baitPrice','']])$(k).value=v;for(const k of ['squidHat','commonHook','squidPet','rain','payRain'])$(k).checked=true;$('bait').value='FISH_BAIT';$('hydraKills').value='2';$('fishingTime').value='day';$('squidPetRarity').value='LEGENDARY';$('spawnEffText').textContent='60%';$('calc-result').innerHTML='<div class="calc-empty"><span class="empty-icon">◈</span><h3>No calculation yet</h3><p>Change assumptions and run the simulator.</p></div>';}

function renderMarket(){
 const m=state.market||{live:false,products:{},state:'unavailable'};
 const search=$('market-search').value.trim().toUpperCase();
 $('market-alert').className='market-alert '+(m.live?'':'error');
 $('market-alert').innerHTML=m.live?`<span>●</span><span>LIVE · ${money(m.product_count)} Bazaar products · API snapshot ${m.api_last_updated?new Date(m.api_last_updated).toLocaleString(): 'time not supplied'}. Values approximate, not execution guarantees.</span>`:`<span>!</span><span>No live prices available. ${esc(m.last_error||'Launch the server and refresh.')} The app will never silently substitute example prices.</span>`;
 const all=Object.entries(m.products||{});
 let filtered=all.filter(([id])=>id.includes(search));
 if(!search)filtered.sort((a,b)=> (MARKET_ITEMS.indexOf(a[0])===-1?100:MARKET_ITEMS.indexOf(a[0]))-(MARKET_ITEMS.indexOf(b[0])===-1?100:MARKET_ITEMS.indexOf(b[0])) || a[0].localeCompare(b[0]));
 const rows=filtered.slice(0,75);
 $('market-count').textContent=`${money(filtered.length)} matches${filtered.length>75?' · first 75 shown':''}`;
 $('market-rows').innerHTML=rows.length?rows.map(([id,item])=>`<tr><td><strong>${esc(id)}</strong></td><td>${money(item.instant_sell)}</td><td>${money(item.instant_buy)}</td><td>${money(item.instant_buy-item.instant_sell)}</td></tr>`).join(''):'<tr><td colspan="4" class="empty-td">No live products found. No substitute prices shown.</td></tr>';
}

async function loadPoolCatalog(){
 try {const data=await api('/api/pools');state.poolCatalog=data;
  const ss=data.summary;
  $('pool-summary').textContent=`${ss.creatures} creatures / ${ss.anytime_pools} pools / ${ss.creature_drop_tables} verified drop tables · ${ss.drop_items} drop entries`;
 }catch(e){$('pool-summary').textContent='Pool source unavailable: '+e.message;}
}
function poolParams(){
 let manual={};const txt=$('pool-manual-prices').value.trim();
 if(txt){ manual=JSON.parse(txt);if(Array.isArray(manual)||typeof manual!=='object'||manual===null)throw Error('Manual prices must be a name-to-price JSON object.'); }
 return {pool:$('pool-name').value,base_pool:$('pool-base').value,
  reels_per_hour:readNum('pool-catches',1050),tracking:readNum('pool-tracking',30),fishing_level:readNum('pool-level',50),
  sea_creature_chance:readNum('pool-scc',100),double_hook_chance:readNum('pool-dh',30),
  hotspot_override_percent:readNum('pool-override',15),bait:$('pool-bait').value,hook:$('pool-hook').value,time_of_day:$('pool-time').value,
  squid_hat:$('pool-squid-hat').checked,novice_trophy_fisher:$('pool-novice').checked,adept_trophy_fisher:$('pool-adept').checked,
  magic_find:readNum('pool-mf',0),looting_level:readNum('pool-looting',0),hydra_kills_per_catch:readNum('pool-hydra-kills',1),
  bait_saved_percent:readNum('pool-bait-saved',10),manual_bait_price:readNum('pool-bait-price')||null,manual_item_prices:manual};
}
async function runPool(){
 const output=$('pool-results');output.textContent='Calculating weighted creature pool…';
 try{
 const r=await post('/api/pools/project',{params:poolParams(),use_live_market:true});
 const shown=r.creatures.filter(x=>x.expected_per_hour>=0.01);
 output.innerHTML=`<div class="warning-box">PARTIAL MODEL · ${esc(r.pool_name)} · ${fmt(r.creature_rate)} sea creatures/hour. No verified total net profit. Unpriced drop entries: ${r.unpriced.length}; creatures lacking drop tables: ${r.unmodelled.length}. Standard rolls use your Magic Find and Looting. Pet and dye rolls use base rates.</div>
 <div class="feature-list"><div><span>◈</span> Priced common-drop revenue/h <strong>${short(r.known_common_revenue)}</strong></div><div><span>◈</span> Priced rare-drop expected value/h <strong>${short(r.known_rare_base_ev)}</strong></div><div><span>◈</span> Jackpot expected value/h (separate) <strong>${short(r.known_jackpot_base_ev)}</strong></div><div><span>◈</span> Bait cost/h <strong>${r.bait_cost===null?'UNPRICED':short(r.bait_cost)}</strong></div><div><span>◈</span> Priced SUBSET after bait, not total net <strong>${r.known_subtotal_after_bait===null?'UNAVAILABLE':short(r.known_subtotal_after_bait)}</strong></div></div>
 <div class="table-scroll"><table class="data-table"><thead><tr><th>CREATURE</th><th>WEIGHT</th><th>SPAWN %</th><th>EXPECTED / HR</th><th>DROP DATA</th></tr></thead><tbody>${shown.map(x=>`<tr><td><strong>${esc(x.name)}</strong></td><td>${fmt(x.modified_weight)}</td><td>${(x.probability*100).toFixed(3)}%</td><td>${fmt(x.expected_per_hour)}</td><td>${x.has_drop_table?`<details><summary>${x.drops.length} known drops</summary>${x.drops.map(d=>`<div class="feature-list"><div><a href="${esc(d.source)}" target="_blank" rel="noreferrer">${esc(d.name)}</a><strong>${(d.base_chance*100).toPrecision(3)}% base → ${((d.adjusted_chance ?? d.base_chance)*100).toPrecision(3)}% per kill · ${fmt(d.expected_units)} items/h · ${d.expected_coins===null?'UNPRICED':short(d.expected_coins)} · ${d.tier}</strong></div></div>`).join('')}</details>`:'UNMODELLED'}</td></tr>`).join('')}</tbody></table></div>
 <div class="warning-box"><strong>Known gaps:</strong> ${esc(r.unmodelled.join(', ')||'No creatures without drop tables')}<br/>${esc(r.unpriced.slice(0,28).map(x=>x.drop).filter((v,i,a)=>a.indexOf(v)===i).join(', ')||'No missing prices in the listed drops')}${r.unpriced.length>28?' …':''}<br/><a href="https://hypixelskyblock.minecraft.wiki/w/Sea_Creatures" target="_blank" rel="noreferrer">Source: current SkyBlock Wiki spawn weights ↗</a></div>`;
 }catch(e){output.className='placeholder-line';output.textContent='Pool calculation blocked: '+e.message;}
}
async function runDiscovery(){
 const el=$('discovery-results');el.innerHTML='Running documented equipment combinations…';
 try{const r=await post('/api/experiments/squid',{params:getParams(),manual_prices:getOverrides()});
 el.className='variation-list';el.innerHTML=`<div class="warning-box">${esc(r.warning)} ${r.prices_live?'Official live market inputs.':'Prices unverified or missing.'}</div>`+r.variants.map((m,i)=>`<div class="variation"><span class="rank">${String(i+1).padStart(2,'0')}</span><div><strong>${esc(m.label)}</strong><small>Partial model · ${money(m.ink_per_hour)} ink/hour · NOT a complete profit prediction</small></div><div class="value">${m.modelled_net===null?'UNPRICED':short(m.modelled_net)}</div></div>`).join('');
 }catch(e){el.className='placeholder-line';el.textContent='Variants could not run: '+e.message;}
}
const storageKey='deepwater_field_sessions_v01';
function getSessions(){try{let records=JSON.parse(localStorage.getItem(storageKey)||'[]');return Array.isArray(records)?records:[];}catch{return[];}}
function renderSessions(){
 const sess=getSessions();
 $('session-history').innerHTML=sess.length?sess.map(x=>`<div class="session-row"><div><strong>${esc(x.method)}</strong><small>${esc(x.date)} · ${money(x.duration)} min · ${money(x.ink)} ink · ${esc(x.notes||'')}</small></div><div><div class="coins">${short(x.rate)}/hr</div><small>${x.price_source==='live'?'Live API at logging':'Manual price'}${x.predictedInkPerHour!==null&&x.predictedInkPerHour!==undefined&&x.predictedInkPerHour>0?' · ink prediction error '+((x.measuredInkPerHour-x.predictedInkPerHour)/x.predictedInkPerHour*100).toFixed(1)+'%':''}</small></div></div>`).join(''):'<p class="panel-text">No sessions recorded yet.</p>';
}
function saveSession(){
 const duration=readNum('duration'),ink=readNum('sessionInk'),other=readNum('sessionOther'),cost=readNum('sessionCosts');
 const priceFromLive=state.market?.live && state.market?.products?.INK_SACK?.instant_sell;
 const userPrice=readNum('sessionInkPrice');
 const price=userPrice>0?userPrice:priceFromLive;
 if(!Number.isFinite(duration)||duration<=0||duration>1440||[ink,other,cost].some(x=>!Number.isFinite(x)||x<0)||ink>1e9){alert('Enter valid, nonnegative quantities and a session duration of 1–1440 minutes.');return;}
 if(!price){alert('No live INK_SACK price available. Enter your actual ink sale price per item before saving.');return;}
 const measuredInkPerHour=ink*60/duration;const predictedInkPerHour=$('sessionType').value==='Birch Park squids'?(state.latestCalculation?.ink_per_hour??null):null;
 const record={method:$('sessionType').value,date:new Date().toLocaleString(),duration,ink,other,cost,rate:(ink*price+other-cost)*60/duration,price_source:userPrice>0?'manual':'live',notes:$('sessionNotes').value.slice(0,300),measuredInkPerHour,predictedInkPerHour};
 const data=getSessions();data.unshift(record);localStorage.setItem(storageKey,JSON.stringify(data.slice(0,80)));renderSessions();
}

async function runPayback(){
 const values={extra_gear_cost:readNum('gear-cost'),new_profit:readNum('new-rate'),baseline_profit:readNum('baseline-rate')};
 const el=$('payback-output');
 if(Object.values(values).some(x=>!Number.isFinite(x)||x<0)) {el.textContent='Enter valid, nonnegative amounts.';return;}
 try{const r=await post('/api/payback',values);
   el.innerHTML=r.hours===null?'No payback: new net income does not exceed your current net income.':`<strong style="color:#a9edc6;font-size:18px">${fmt(r.hours)} hours</strong> to recover ${money(values.extra_gear_cost)} coins from ${money(values.new_profit-values.baseline_profit)} extra coins/hour, excluding resale value.`;
 }catch(e){el.textContent='Could not calculate payback: '+e.message;}
}

async function runTests(){
 let pass=0,fail=0,blocked=0;const out=[];
 const check=(name,status,detail)=>{out.push({name,status,detail});if(status==='PASS')pass++;else if(status==='FAIL')fail++;else blocked++;};
 const close=(a,b)=>Math.abs(a-b)<0.00001;
 try{const h=await api('/api/health');check('Backend health endpoint',h.status==='ok'?'PASS':'FAIL',`status=${h.status}, version=${h.version}`);}catch(e){check('Backend health endpoint','BLOCKED',e.message);}
 try{const r=await post('/api/calculate/squid',{params:{reels_per_hour:0,rain:false,bait:'NONE',other_common_weight:0},manual_prices:{'INK_SACK':{instant_sell:10,instant_buy:12},'WATER_LILY':{instant_sell:2,instant_buy:3}}});
 check('Zero reels → zero natural and caught Squids',close(r.ink_per_hour,0)&&close(r.modelled_net,0)?'PASS':'FAIL',`ink=${r.ink_per_hour}, net=${r.modelled_net}`);
 }catch(e){check('Zero reels → zero natural and caught Squids','BLOCKED',e.message);}
 try{const p={'INK_SACK':{instant_sell:10,instant_buy:12},'WATER_LILY':{instant_sell:2,instant_buy:3},'FISH_BAIT':{instant_sell:4,instant_buy:8}};
 const r=await post('/api/calculate/squid',{params:{reels_per_hour:100,sea_creature_chance:100,double_hook_chance:0,rain:false,other_common_weight:0,bait:'FISH_BAIT',bait_saved_percent:10},manual_prices:p});
 const expected=r.ink_per_hour*10+r.lily_pads_per_hour*2-90*8;
 check('Net revenue deducts bait by correct instant-buy side',close(r.modelled_net,expected)?'PASS':'FAIL',`expected=${expected.toFixed(2)}, result=${r.modelled_net}, bait=${r.cost_bait}`);
 }catch(e){check('Net revenue deducts bait by correct instant-buy side','BLOCKED',e.message);}
 try{const r=await post('/api/calculate/squid',{params:{reels_per_hour:100,bait:'FISH_BAIT',rain:false},manual_prices:{},use_live_market:false});
 check('Missing prices never yield a fabricated numeric net',(!r.price_complete&&r.modelled_net===null)?'PASS':'FAIL',`complete=${r.price_complete}, net=${r.modelled_net}`);
 }catch(e){check('Missing prices never yield a fabricated numeric net','BLOCKED',e.message);}
 try{const r=await post('/api/calculate/squid',{params:{sea_creature_chance:101},manual_prices:{}});check('Invalid SCC >100 rejected','FAIL','API wrongly accepted invalid SCC');}
 catch(e){check('Invalid SCC >100 rejected',e.message.includes('Sea Creature Chance')?'PASS':'FAIL',e.message);}
 try{const r=await api('/api/rankings');check('No unverified methods are ranked as proven',r.ranked.length===0?'PASS':'FAIL',`verified ranked entries=${r.ranked?.length}`);}catch(e){check('No unverified methods are ranked as proven','BLOCKED',e.message);}
 try{const r=await post('/api/experiments/squid',{params:{reels_per_hour:0,rain:false,bait:'NONE'},manual_prices:{}});check('Discovery enumerates 16 testable variants',r.count===16&&r.variants.every(x=>x.full_profit_verified===false)?'PASS':'FAIL',`variants=${r.count}, all flagged unverified=${r.variants?.every(x=>!x.full_profit_verified)}`);}catch(e){check('Discovery enumerates 16 testable variants','BLOCKED',e.message);}
 try{const m=await api('/api/prices');if(m.live){const ink=m.products?.INK_SACK;check('Live Bazaar product data and spread',ink&&ink.instant_sell>0&&ink.instant_buy>=ink.instant_sell?'PASS':'FAIL',`INK_SACK sell=${ink?.instant_sell}, buy=${ink?.instant_buy}, items=${m.product_count}`);}
 else check('Live Bazaar API connectivity','BLOCKED',m.last_error||'No verified live market data');}catch(e){check('Live Bazaar API connectivity','BLOCKED',e.message);}
 try{const r=await post('/api/payback',{extra_gear_cost:200000000,new_profit:50000000,baseline_profit:40000000});check('ROI payback formula 200M/10M=20h',close(r.hours,20)?'PASS':'FAIL',`observed=${r.hours} hours`);}catch(e){check('ROI payback formula 200M/10M=20h','BLOCKED',e.message);}
 state.tests=out;$('test-pass').textContent=pass;$('test-fail').textContent=fail;$('test-blocked').textContent=blocked;$('test-run-time').textContent='RAN '+new Date().toLocaleString();
 $('tests-list').innerHTML=out.map(t=>`<div class="testrow"><div class="test-symbol ${t.status==='PASS'?'ok':t.status==='FAIL'?'fail':'block'}">${t.status==='PASS'?'✓':t.status==='FAIL'?'✕':'!'}</div><div class="test-info"><strong>${esc(t.name)}</strong><p>${esc(t.detail)}</p></div><span class="status ${t.status==='PASS'?'status-green':'status-amber'}">${esc(t.status)}</span></div>`).join('');
}


// Fishing Encyclopedia — mechanics-backed gear candidates, NOT verified profit rankings.
let libraryCatalog=[];
let libraryPage=1;
const LIB_PAGE_SIZE=24;
const LIBRARY_SLOTS={armor:'Armor',rod:'Fishing rod',hook:'Hook',line:'Line',sinker:'Sinker',bait:'Bait',casting_pet:'Casting pet',reeling_pet:'Reeling pet',kill_pet:'Kill pet',weapon:'Weapon',equipment:'Equipment',enchants:'Enchantments',stats:'Stat targets',autopet:'Autopet / swap rule'};
function optimizedProfitMarkup(s){
 const estimate=Number.isFinite(s.profit_per_hour)?`${esc(short(s.profit_per_hour))} coins/hr`:'Estimate pending';
 const tag=s.global_hypermax_verified===true?'':' <span class="library-chip warn">Hypothetical</span>';
 return `<span class="small"><b>Optimized setup · Estimated net profit/hr</b><br>${estimate}${tag}</span>`;
}
function filterLibrary(){
 const search=$('library-search').value.trim().toLowerCase();
 const region=$('library-region').value;
 const effort=$('library-effort').value;
 const events=$('library-event').value;
 const washed=$('library-washed').checked;
 let rows=libraryCatalog.filter(s=>
   (events==='all'||s.availability===events) &&
   (!region||s.region===region)&&(!effort||s.effort===effort)&&
   (washed||!['previously-tested','effort-rejected','low-prospect'].includes(s.status))&&
   (!search||[s.name,s.region,s.objective,s.target,s.user_note].some(v=>String(v||'').toLowerCase().includes(search)))
 );
 const totalPages=Math.max(1,Math.ceil(rows.length/LIB_PAGE_SIZE));
 if(libraryPage>totalPages)libraryPage=totalPages;
 if(libraryPage<1)libraryPage=1;
 $('library-count').textContent=`${rows.length} matching strategies (${libraryCatalog.length} catalog entries).  Each is a setup candidate, not a proven 40M/hour rate.`;
 $('library-page').textContent=`Page ${libraryPage} of ${totalPages}`;
 $('library-previous').disabled=libraryPage===1;
 $('library-next').disabled=libraryPage>=totalPages;
 const chunk=rows.slice((libraryPage-1)*LIB_PAGE_SIZE,libraryPage*LIB_PAGE_SIZE);
 $('library-cards').innerHTML=chunk.map(s=>`<button class="library-card" data-strategy-id="${esc(s.id)}" type="button">
   <span class="micro">${esc(s.region)} · ${esc(s.availability.toUpperCase())}</span>
   <strong>${esc(s.name)}</strong><span class="small">${esc(s.objective)}</span>
   <span class="tags"><span class="library-chip">${esc(s.effort)} effort</span><span class="library-chip">${esc(s.movement)} movement</span>
   <span class="library-chip ${s.status==='candidate'?'':'warn'}">${esc(s.status)}</span></span>
   ${optimizedProfitMarkup(s)}
   <span class="small">View full loadout, experiment, tutorial &amp; source links ↗</span>
   </button>`).join('') || `<div class="placeholder-line">No strategies match these filters. Try All locations or include previously tested methods.</div>`;
}
function renderHypotheses(){
 const rows=libraryCatalog.filter(s=>s.availability==='anytime'&&s.status==='candidate'&&s.priority>=4&&s.experiment?.verified===false);
 $('hypothetical-cards').innerHTML=rows.map(s=>`<button class="library-card" data-strategy-id="${esc(s.id)}" type="button">
   <span class="micro">${esc(s.region)} · ANYTIME</span>
   <strong>${esc(s.name)}</strong>
   <span class="small">${esc(s.experiment.reason)}</span>
   <span class="small"><b>Field test</b> · ${esc(s.experiment.protocol)}</span>
   ${optimizedProfitMarkup(s)}
   <span class="small">Open full method ↗</span>
 </button>`).join('') || '<div class="placeholder-line">No featured hypotheses are available.</div>';
}
async function loadLibrary(){
 try{
  const result=await api('/api/strategies?availability=all&limit=200');
  libraryCatalog=result.items||[];
  const regions=[...new Set(libraryCatalog.map(s=>s.region))].sort((a,b)=>a.localeCompare(b));
  $('library-region').innerHTML='<option value="">All locations</option>'+regions.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('');
  filterLibrary();
  renderHypotheses();
 }catch(e){$('hypothetical-cards').textContent='Hypotheses could not load.';$('library-count').textContent='Could not load strategy catalog: '+e.message;}
}
const slotMarkup=(s)=>Object.entries(LIBRARY_SLOTS).map(([key,label])=>`<div class="slot"><span class="k">${esc(label)}</span><span class="v">${esc(s[key]||'Not yet established')}</span></div>`).join('');
async function showStrategy(id){
 const el=$('library-detail'); el.hidden=false;
 el.innerHTML='<p>Loading method setup and live market context…</p>';
 navigate('library');
 try{
  const data=await api('/api/strategies/'+encodeURIComponent(id));
  const s=data.strategy,ob=data.market_observations||{};
  const marketRows=(ob.item_prices||[]);
  const marketInfo=marketRows.length ?
    `<div class="table-scroll"><table class="price-table"><thead><tr><th>Drop</th><th>Base chance</th><th>Instant sell</th><th>Price evidence</th></tr></thead><tbody>${marketRows.map(d=>`<tr><td>${esc(d.item)}</td><td>${esc((d.base_chance*100).toFixed(3)+'%')}</td><td>${d.instant_sell===null?'Unpriced':money(d.instant_sell)}</td><td>${esc(d.status)}</td></tr>`).join('')}</tbody></table></div>`:
    '<p class="subtle">No verified drop table linked for this specific method yet. Price and profit are unknown.</p>';
  el.innerHTML=`<button type="button" class="btn btn-outline" id="close-library-detail">← Close setup</button>
  <h2>${esc(s.name)}</h2><p class="subtle">${esc(s.region)} · ${esc(s.availability)} · ${esc(s.effort)} effort · ${esc(s.movement)} movement · Reviewed ${esc(s.reviewed_on)}</p>
  <div class="warning-box"><strong>HIGH-END LOADOUT CANDIDATE — NOT A PROVEN GLOBAL OPTIMUM.</strong> ${esc(s.profit_status)}. Gear depends on caps, market prices and verified drop mechanics.${s.user_note?'<p>'+esc(s.user_note)+'</p>':''}</div>
  <div class="method-section">${optimizedProfitMarkup(s)}</div>
  <div class="method-section"><h3>What you're farming</h3><p class="subtle">${esc(s.objective)}</p><p class="subtle">${esc(s.mechanics_note)}</p></div>
  <div class="method-section"><h3>High-end setup · Every slot</h3><div class="slot-grid">${slotMarkup(s.best_documented_setup)}</div></div>
  <div class="method-section"><h3>Hypothetical / experimental setup</h3><strong>${esc(s.experiment.name)}</strong><p class="subtle">${esc(s.experiment.reason)}</p><p class="subtle">Test protocol: ${esc(s.experiment.protocol)}</p><span class="library-chip warn">NOT VERIFIED</span></div>
  <div class="method-section"><h3>Fishing tutorial</h3><ol>${s.tutorial.map(x=>`<li>${esc(x)}</li>`).join('')}</ol></div>
  <div class="method-section"><h3>Available live price observations (not full profit)</h3><p class="subtle">${ob.market_live?'Live Bazaar snapshot;':'Live Bazaar unavailable;'} market values alone do not establish drops/hour. AH-only items remain unpriced.</p>${marketInfo}</div>
  <div class="method-section"><h3>Mechanic sources</h3><div class="source-list">${s.sources.map((u,i)=>`<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">Reference ${i+1} ↗</a>`).join('')}</div></div>`;
  $('close-library-detail').addEventListener('click',()=>{el.hidden=true;el.innerHTML='';});
  el.scrollIntoView({behavior:'smooth',block:'start'});
 }catch(e){el.innerHTML=`<div class="warning-box">Couldn't open this method: ${esc(e.message)}</div>`;}
}
function setupLibrary(){
 for(const id of ['library-search','library-region','library-effort','library-event','library-washed']){
  $(id).addEventListener(id==='library-search'?'input':'change',()=>{libraryPage=1;filterLibrary();});
 }
 $('library-previous').addEventListener('click',()=>{libraryPage--;filterLibrary();});
 $('library-next').addEventListener('click',()=>{libraryPage++;filterLibrary();});
 for(const id of ['library-cards','hypothetical-cards']){
  $(id).addEventListener('click',e=>{const c=e.target.closest('[data-strategy-id]');if(c)showStrategy(c.dataset.strategyId);});
 }
}

async function init(){
 setupLibrary();
 $('run-pool').addEventListener('click',runPool);$('run-calc').addEventListener('click',runCalc);$('reset-calc').addEventListener('click',resetCalc);$('run-discovery').addEventListener('click',runDiscovery);
 $('market-search').addEventListener('input',renderMarket);$('reload-market').addEventListener('click',()=>loadMarket(true));$('refresh-prices').addEventListener('click',()=>loadMarket(true));
 $('save-session').addEventListener('click',saveSession);$('clear-sessions').addEventListener('click',()=>{if(confirm('Remove all recorded field sessions on this browser?')){localStorage.removeItem(storageKey);renderSessions();}});
 $('run-tests').addEventListener('click',runTests);$('calc-payback').addEventListener('click',runPayback);$('spawnEff').addEventListener('input',()=>$('spawnEffText').textContent=$('spawnEff').value+'%');
 await Promise.allSettled([loadMethods(),loadMarket(),loadPoolCatalog(),loadLibrary()]);
 renderSessions();
 // Poll for new official prices periodically while the website is open.
 // The server independently caches Hypixel requests for 180 seconds.
 setInterval(() => { if (!document.hidden) loadMarket(); }, 180000);
 document.addEventListener('visibilitychange', () => {
   if (!document.hidden && Date.now() - state.lastMarketPollAt >= 180000) loadMarket();
 });
}
init();
