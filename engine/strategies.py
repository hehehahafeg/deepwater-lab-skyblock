"""Evidence-indexed fishing strategies (profiles, not profitability forecasts).

Every profile has a mechanics-constrained starting loadout and a separate,
explicitly unverified experiment. A 'hypermax candidate' is NEVER a claim of
proven global optimality. The app deliberately refuses to invent profit/hr.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from typing import Any
from engine.pools import POOLS, DROPS, SEA_SOURCE, WIKI

VERIFIED_DATE='2026-11-10'
BASE_SOURCES={
 'sea_pool': SEA_SOURCE,
 'hotspot': WIKI+'Fishing_Hotspots',
 'hook': WIKI+'Rod_Parts',
 'fishing': WIKI+'Fishing',
 'treasure': WIKI+'Treasure_Hook',
 'wooden': WIKI+'Wooden_Bait',
 'hunting': WIKI+'Hunting',
 'hound': WIKI+'Hound_Pet',
 'squid_pet': WIKI+'Squid_Pet',
 'bait': WIKI+'Fishing_Bait',
 'trophy': WIKI+'Trophy_Fishing',
 'hellfire': WIKI+'Hellfire_Rod',
}

def slug(s):
 return ''.join(x if x.isalnum() else '-' for x in s.lower()).strip('-').replace('--','-')

G=[]

# The island-dependent speed caps are published in the current Fishing Speed Wiki.
# Generic hotspot profiles have no universal cap: they inherit the island below.
SPEED_CAP_SOURCE = WIKI + 'Fishing_Speed'
REGION_SPEED_CAPS = {'Backwater Bayou': 200, 'Lotus Atoll': 250, 'Crimson Isle': 350}

def regional_speed_cap(region):
 if region == 'Water Hotspots':
  return None
 return REGION_SPEED_CAPS.get(region, 300)

def kit(style:str,target:str='',rarity:str='RARE',weight:int=100):
 lava=style in ('lava','lava-hotspot','trophy','lava-worm')
 treasure=style=='treasure'
 hotspot=style in ('water-hotspot','lava-hotspot')
 squid=style=='squid'
 common=(rarity=='COMMON')
 rare_weight=weight<400
 if treasure:
  return {
    'armor':'Highest verified Treasure Chance loadout you own; do not assume Sea Creature gear improves treasure tier',
    'rod':'Hypermaxed Rod of the Sea (water); Hellfire Rod (Crimson lava)',
    'hook':'Treasure Hook — prevents sea creatures; use ONLY for treasure profiles',
    'line':'Titan Line if it helps speed cap, otherwise highest applicable fishing/treasure value',
    'sinker':'Stingy Sinker for bait conservation; change only after comparing value per cast',
    'bait':'Wooden Bait for zone-specific GOOD shards; Blessed Bait for higher treasure-tier experiments',
    'casting_pet':'Level 100 Mythic Flying Fish for cast speed if needed',
    'reeling_pet':'Level 100 Mythic Hermit Crab to investigate GREAT/OUTSTANDING treasure tiers',
    'kill_pet':'None (Treasure Hook removes sea creatures)',
    'weapon':'Not required',
    'equipment':'Highest confirmed Treasure Chance stats; do not stack unverified sea-creature modifiers',
    'enchants':'Max applicable rod enchants, including treasure-oriented bonuses when supported',
    'stats':'Location-specific Fishing Speed cap; treasure chance and tier distribution; bait-save chance',
    'autopet':'On cast → Flying Fish when below cap; otherwise retain Hermit Crab for reeling',
  }
 if squid:
  return {
    'armor':'Squid Hat + 3/4 hypermaxed Submerged Magma Lord',
    'rod':'Hypermaxed Rod of the Sea',
    'hook':'Common Hook (raises common sea-creature weighting)',
    'line':'Titan Line',
    'sinker':'Prismarine Sinker for secondary drops; compare Stingy Sinker if bait is expensive',
    'bait':'Fish Bait below 300 Fishing Speed; test Spiked Bait only if SCC below 100',
    'casting_pet':'Level 100 Mythic Flying Fish when needed to reach casting speed cap',
    'reeling_pet':'Level 100 Legendary or Epic Squid Pet for double squid drops',
    'kill_pet':'Keep Squid Pet for ordinary squid; GDrag only for separately verified profitable rare kills',
    'weapon':'Hyperion with highest legitimately available Looting level',
    'equipment':'Fishing gear with useful Double Hook and catch-speed bonuses',
    'enchants':'Best available applicable rod enchants; Looting V maximum on weapon',
    'stats':'300 Fishing Speed on cast; 100 SCC on reel; maximum practical Double Hook; clear rain spawns',
    'autopet':'On throw hook → Flying Fish; swap to Squid before reel; do NOT auto-GDrag ordinary squids',
  }
 bait=('Hotspot Bait' if hotspot else ('Light Bait in day / Dark Bait at night (only if rare-weight threshold benefits target)' if rare_weight else 'Fish Bait until speed-capped; if capped compare bait costs'))
 if style=='trophy':bait='Trophy-fishing bait selected for the specific trophy condition; verify species requirements'
 if style=='lava-worm':bait='Fish Bait if below cap; otherwise compare input costs; special worm location eligibility is required'
 return {
  'armor':'Full hypermaxed Submerged Magma Lord (adjust if alternate equipment produces higher effective stats)',
  'rod':'Hypermaxed Hellfire Rod' if lava else 'Hypermaxed Rod of the Sea',
  'hook':'Hotspot Hook' if hotspot else ('Common Hook' if common else 'No specialized hook (Common Hook biases against this target)'),
  'line':'Titan Line (verify actual stat gain at your fishing cap)',
  'sinker':'Hotspot Sinker (doubles hotspot stat bonuses)' if hotspot else ('Stingy Sinker (reduces bait operating cost)' if not common else 'Stingy Sinker; compare Lotus/Chum/Prismarine Sinker only with priced secondary loot'),
  'bait':bait,
  'casting_pet':'Level 100 Mythic Flying Fish if below Fishing Speed cap',
  'reeling_pet':'Level 100 Mythic Hermit Crab for hotspot replacement' if hotspot else ('Best stats-verified Fishing pet; keep Flying Fish if required to cap SCC' if rarity in ('COMMON','UNCOMMON') else 'Flying Fish or high-SCC fishing pet; compare actual catch outcomes'),
  'kill_pet':'GDrag for eligible rare-drop kills; compare against Hound ONLY as an experiment' if not common else 'Best verified profitable drop pet; GDrag only for MF-eligible drops',
  'weapon':'Hyperion plus Flaming Flay for resistant lava mobs' if lava else 'Hyperion or reliable instant-kill weapon, maximum legitimately available Looting V',
  'equipment':'High Double Hook Chance, relevant Loch Hook/Tracking and Fishing attributes where available',
  'enchants':'Max applicable rod enchants; weapon Looting V is the maximum',
  'stats':('350' if lava else ('200' if style=='bayou' else '250' if style=='lotus' else '300'))+' Fishing Speed cap; 100 SCC; Double Hook; Tracking for Elusive creatures',
  'autopet':'On cast → Flying Fish if needed; verify pet at reel; swap GDrag BEFORE valuable kill (combat trigger may be late)',
 }

def experiment_for(style,target,rarity,weight):
 if style=='squid':return ('GDrag vs Squid kill swap',
   'Compare rare-drop MF against guaranteed double-ink. Do not assume a pet swap on hit preserves the Squid perk.',
   'Two equal-duration trials with count of ink, Squid kills and rare drops; record bait and rain uptime.')
 if style=='water-hotspot' and target=='Wiki Tiki':return ('Hound Finder vs GDrag for Tiki Mask',
   'Hound boosts armor drops, but Tiki Mask may not qualify as armor in the loot engine. Effect is UNVERIFIED; do not multiply its drop chance.',
   'Count Wiki Tiki kills and actual masks across controlled trials, separate Hound vs GDrag; large sample required.')
 if style in ('water-hotspot','lava-hotspot'):
  return ('Targeted hybrid hotspot override',
  'Compare maximum hotspot replacement against lower replacement with more of the ordinary-pool rare drops. Higher override does not automatically mean higher total revenue.',
  '10–20 minute paired sessions; measure all creature counts, rare drops and moving time; use actual instant sells.')
 if style=='treasure':return ('Tier-shifting versus shard-only fishing',
  'Try Blessed versus Wooden Bait and different treasure-tier bonuses. Missing live shard price or tier weights makes a theoretical ranking unreliable.',
  'Track GOOD/GREAT/OUTSTANDING catches and actual shard units separately in equal sessions.')
 if style in ('lava','trophy','lava-worm'):
  return ('Magic Find versus uptime / lootshare',
  'Compare GDrag before rare kills versus staying on a catch-rate pet. Include full fight duration, Flash books and non-Bazaar drop values.',
  'Measure creatures killed (not just reeled), fight downtime and per-drop revenue over a long enough session.')
 if style=='hunting':return ('Pocket Black Hole capture versus conventional kill',
  'Hunting Fortune may improve shard yield but capture processing costs time; capture profitability is unverified.',
  'Compare shard units per minute after capturing with total conventional loot over matched sessions.')
 if rarity in ('LEGENDARY','MYTHIC'):
  return ('Tracking / rare-bait sensitivity',
  'Increasing one creature’s relative weight also changes the denominator for all others; rare-bait only boosts creatures below the required weight threshold.',
  'Compare actual target appearances per 100 sea creatures with differing bait and Tracking conditions.')
 return ('Alternate catch-weight optimization',
  'Test Common Hook versus neutral hook and speed-focused bait; only COMMON weight receives the Common Hook bonus.',
  'Log target catches per 100 sea creatures in two equal-duration samples.')

def add(name,region,style,objective,*,target='',rarity='RARE',weight=100,
        pool='',movement='fixed',effort='low',availability='anytime',status='candidate',
        user_note='',verified_note='',sources=(),tags=(),priority=0):
 # A Hunting-hybrid must keep its fishing/capture workflow distinct from a
 # pure rare-drop kill build. Choose the actual liquid, not an unrelated style.
 if style == 'hunting':
  underlying_style = 'lava' if region == 'Crimson Isle' else 'lotus' if region == 'Lotus Atoll' else 'water'
 else:
  underlying_style = style
 base=kit(underlying_style,target,rarity,weight)
 cap=regional_speed_cap(region)
 if cap is None:
  cap_label='Underlying island cap (Bayou 200; Lotus 250; Crimson 350; otherwise 300)'
 else:
  cap_label=f'{cap} Fishing Speed cap'
 # Preserve condition-dependent stat instructions for treasure/trophy fishing
 # while ensuring every method displays its real island cap.
 if ' Fishing Speed cap' in base['stats'] and base['stats'].split(' Fishing Speed cap')[0].split()[-1].isdigit():
  before=base['stats'].split(' Fishing Speed cap',1)[0]
  old_cap=before.split()[-1]
  base['stats']=base['stats'].replace(old_cap+' Fishing Speed cap',cap_label,1)
 elif cap_label not in base['stats']:
  base['stats']=cap_label+'; '+base['stats']
 if style == 'hunting':
  base['equipment']='Highest usable fishing stats for catching, plus Pocket Black Hole / Hunting tools ONLY where eligible; verify capture mechanic for the target'
  base['reeling_pet']='Maximize eligible catch chance first; do not assume a kill pet improves shard captures'
  base['kill_pet']='Use GDrag only for eligible rare kill drops; for captured targets compare Hunting Fortune instead of Magic Find'
  base['weapon']='Hyperion for eligible kill-only route; avoid killing before a capture; use appropriate capture tool on eligible targets'
  base['autopet']='Cast with Flying Fish if needed; choose the catch pet on reel; explicitly swap to capture/Hunting setup when the target spawns'
  base['stats']+='; verify Hunting Fortune and capture throughput separately'
 experiment,why,test=experiment_for(style,target,rarity,weight)
 step=[
  'Confirm the fishing location, liquid and unlocks in /scg; only eligible sea creatures can spawn.',
  'Configure the rod parts and bait; check your region-specific Fishing Speed cap and 100% SCC before starting.',
  'Cast and reel with the specified pet timing; collect/kill target creatures and ALL other loot.',
  'Record actual reels/hour, target spawns/hour, bait consumed, rare drops and time lost to combat or movement.',
  'Value Bazaar items at current INSTANT SELL and bought bait at current INSTANT BUY; leave unpriced drops unknown.',
 ]
 if style=='treasure':step[2]='Use Treasure Hook to obtain item/treasure catches; record treasure tiers and shard quantities, not sea creatures.'
 if style=='hunting':step[2]='Fish the target, then capture or charm with permitted Hunting tools; count Hunting Fortune and handling time.'
 if style in ('water-hotspot','lava-hotspot'):step[0]='Locate an active eligible hotspot; keep movement time measured and do not assume permanent 100% override.'
 if style=='squid':step[0]='Fish in the Birch Park during Vanessa rain; kill natural rain squids promptly to keep the spawn cap clear.'
 if style=='trophy':step[0]='Select a specific trophy fish and satisfy its documented location/condition before casting.'
 if style=='lava-worm':step[0]='Find a Crystal Hollows location where Flaming Worm spawning is eligible; check current requirements.'
 item_sources=[BASE_SOURCES['sea_pool'],BASE_SOURCES['fishing']]
 if pool in POOLS:
  item_sources += [WIKI+target.replace(' ','_')]
 if style in ('water-hotspot','lava-hotspot'):item_sources +=[BASE_SOURCES['hotspot'],BASE_SOURCES['hook']]
 if style=='treasure':item_sources +=[BASE_SOURCES['treasure'],BASE_SOURCES['wooden']]
 if style=='squid':item_sources +=[BASE_SOURCES['squid_pet']]
 if style=='trophy':item_sources +=[BASE_SOURCES['trophy']]
 item_sources+=list(sources)
 method={
 'id':slug(name),'name':name,'region':region,'style':style,'family':region,'objective':objective,
 'target':target,'pool':pool,'movement':movement,'effort':effort,
 'availability':availability,'status':status,'tags':list(tags),
 'user_note':user_note,'mechanics_note':verified_note or 'Candidate optimization constrained by documented fishing mechanics; global optimum not verified.',
 'best_documented_setup':base,'experiment':{'name':experiment,'reason':why,'protocol':test,'verified':False},
 'tutorial':step,'sources':list(dict.fromkeys(item_sources)),'reviewed_on':VERIFIED_DATE,
 'confidence':'mechanics-partial','profit_per_hour':None,'profit_status':'NOT VERIFIED — no complete drop-value and cast-rate model',
 'global_hypermax_verified':False,
 'fishing_speed_cap':cap, 'fishing_speed_cap_source':SPEED_CAP_SOURCE,
 'priority':priority,
 }
 if any(x['id']==method['id'] for x in G):raise ValueError('Duplicate strategy '+name)
 G.append(method)
 return method

# Every individually documented creature in the existing eight weighted pools:
# targeting does not imply that biased gear can actually improve a given creature.
for pid,pool in POOLS.items():
 for creature in pool['creatures']:
  name=creature.name
  style=('water-hotspot' if pid=='hotspot_water' else 'lava-hotspot' if pid=='hotspot_lava' else
         'squid' if name=='Squid' else 'bayou' if pid=='bayou' else 'lotus' if pid=='lotus' else
         'lava' if pid=='crimson_lava' else 'water')
  if pid=='hotspot_water':region='Water Hotspots'
  elif pid=='hotspot_lava':region='Crimson Isle'
  else:region=pool['region'].split(' and ')[0]
  user_note='Already explored; include for comparison even if unprofitable.' if name in ('The Loch Emperor','Tadgang','Fire Eel','Taurus') else ''
  add(f'{region} · Target {name}',region,style,f'Increase {name} catches and evaluate its entire loot table, not just one drop.',
      target=name,rarity=creature.rarity,weight=creature.base_weight,pool=pid,
      movement='small-area' if 'hotspot' in pid else 'fixed',effort='medium' if name in ('Nessie','Lord Jawbus','Puddle Jumper') else 'low',
      status='previously-tested' if user_note else 'candidate',user_note=user_note,
      tags=['individual-creature','weighted-pool'],priority=3 if name in ('Wiki Tiki','Titanoboa','Squid','Thunder') else 1)

# Distinct full-loop methods and measurable experiments, including weak and retired options.
add('Bayou · Full-Loot Hotspot Circuit','Backwater Bayou','water-hotspot','Fish compact hotspots while valuing all ordinary and override creatures.',target='Wiki Tiki',pool='hotspot_water',movement='small-area',tags=['recommended-test','hotspot'],priority=8)
add('Bayou · Titanoboa + Wiki Tiki Hybrid','Backwater Bayou','water-hotspot','Optimize both rare ordinary-pool Titanoboa and hotspot Wiki Tiki; avoid valuing only Tiki Mask.',target='Titanoboa',pool='hotspot_water',movement='small-area',priority=8)
add('Bayou · Wiki Tiki Hound Finder Experiment','Backwater Bayou','water-hotspot','Test whether Hound Finder affects Tiki Mask without treating it as confirmed.',target='Wiki Tiki',pool='hotspot_water',movement='small-area',tags=['unverified-interaction'],priority=9)
G[-1]['best_documented_setup']['kill_pet']='GDrag before kill for eligible rare drops; Hound is NOT verified'
G[-1]['experiment']={'name':'Hound pet Finder on Tiki Mask','reason':'Hound Finder increases armor drops. The Tiki Mask drop might or might not count as an armor drop; no bonus is applied without evidence.','protocol':'Compare actual Tiki Mask drops per Wiki Tiki kill between GDrag and Hound across a substantial number of kills. Record base MF and Looting.','verified':False}
add('Bayou · Ordinary Pool (Avoid Hotspot Override)','Backwater Bayou','bayou','Prioritize Titanoboa, Alligator and ordinary pool drops instead of hotspot replacements.',target='Titanoboa',rarity='MYTHIC',weight=25,pool='bayou',priority=5)
add('Bayou · Chum Sinker Side-Loot Test','Backwater Bayou','bayou','Evaluate Chum materialization against Stingy bait conservation without assuming profitability.',target='Alligator',rarity='LEGENDARY',weight=100,pool='bayou',priority=2)
G[-1]['experiment']={'name':'Chum Sinker vs Stingy Sinker','reason':'The secondary Chum items must sell for more than the bait savings; only current prices can decide.','protocol':'Count casts, Chum and bait use in matched sessions; value using verified live prices.','verified':False}
add('Bayou · Treasure-Junk Focus','Backwater Bayou','treasure','Test Junk Sinker and treasure-tier junk instead of sea creatures.',pool='bayou',priority=2)
G[-1]['best_documented_setup']['sinker']='Junk Sinker for Bayou junk-replacement experiment; compare Stingy for costs'
add('Birch Park · Rain Squid + Natural Spawns','The Park','squid','Optimize fished squid plus automatically appearing rain squid, valuing all ink and secondary loot.',target='Squid',pool='basic_water',priority=9)
add('Birch Park · Dry Squid Control','The Park','squid','Measure whether paying for rain improves net after cost and natural-spawn clearing.',target='Squid',pool='basic_water',priority=4)
G[-1]['best_documented_setup']['bait']='Fish Bait only if below Fishing Speed cap; dry session must not include rain fee'
add('Birch Park · Squid Pet vs GDrag Kill Swap','The Park','squid','Isolate guaranteed Squid Pet ink multiplier versus rare-drop MF.',target='Squid',pool='basic_water',priority=5)
add('Birch Park · Inkling Hotspot + Squid','The Park','water-hotspot','Compare common squid pool with Inkling hotspot replacement.',target='Inkling',pool='hotspot_water',movement='small-area',priority=5)
add('Spider Den · Water Hotspot','Spider’s Den','water-hotspot','Compare hotspot sea creatures on a Combat island versus Bayou drops.',target='Wiki Tiki',pool='hotspot_water',movement='small-area',priority=4)
add('Basic Water · Water Hydra Rare-Drop Focus','Basic Water Islands','water','Track rare water sea creature revenue relative to squid opportunity cost.',target='Water Hydra',rarity='LEGENDARY',weight=18,pool='basic_water',priority=2)
add('Lotus Atoll · Puddle Jumper Hook Focus','Lotus Atoll','lotus','Use specialized hook to increase Puddle Jumper weight; count jump-minigame downtime.',target='Puddle Jumper',rarity='LEGENDARY',weight=100,pool='lotus',priority=5,effort='medium')
G[-1]['best_documented_setup']['hook']='Puddle Jumper Hook (+400% chance for Puddle Jumper)'
add('Lotus Atoll · Frog Prince Crown Jewel','Lotus Atoll','lotus','Price Gold Lotus and Prince’s Crown Jewel as separate expected-value drops.',target='Frog Prince',rarity='MYTHIC',weight=25,pool='lotus',priority=4)
add('Lotus Atoll · Trophy Frog Shard Handling','Lotus Atoll','hunting','Hybrid involving frog captures/shards after fishing; count actual capture time and Hunting Fortune.',target='Puddle Jumper',pool='lotus',effort='medium',status='previously-tested',user_note='Previous research showed shard price compression; retain for future repricing.')
G[-1]['best_documented_setup']['equipment']='Pocket Black Hole / Hunting tools only if verified for the target; Fishing gear for catches'
add('Lotus Atoll · Lotus Sinker Harvest','Lotus Atoll','lotus','Compare materialized Lotus by catch against bait-saving alternatives.',target='Atoll Croaker',rarity='COMMON',weight=5000,pool='lotus')
G[-1]['best_documented_setup']['sinker']='Lotus Sinker, conditional on actual Lotus sell price'
add('Galatea · Moonglade Full Loot','Galatea','water','Count all Moonglade catches, including rare loch and Nessie but without overvaluing them.',target='Nessie',rarity='MYTHIC',weight=25,pool='moonglade',status='previously-tested',user_note='Similar to user’s prior Driptoad Delve tests.')
add('Galatea · Tadgang Shard Capture','Galatea','hunting','Catch Tadgang then capture for shards; model Hunting Fortune and capture throughput.',target='Tadgang',pool='moonglade',effort='medium',status='previously-tested',user_note='Rejected without high Hunting Fortune; include for completeness.')
add('Galatea · Tadgang Charm/Kill Hybrid','Galatea','hunting','Compare normal kills and Hunting charm/capture outcomes.',target='Tadgang',pool='moonglade',effort='medium',status='previously-tested')
add('Galatea · Nessie Combat-Downtime Test','Galatea','water','Estimate real net after Nessie phases and moving; not purely fishing rate.',target='Nessie',rarity='MYTHIC',weight=25,pool='moonglade',effort='medium')
add('Torrhus · Generic Full-Loot Fishing','Torrhus Canyon','water','Value all Torrhus creatures and check whether unknown drops change rankings.',target='Giant Isopod',rarity='MYTHIC',weight=25,pool='torrhus')
add('Torrhus · Hotspot Haven Giant Water Bug','Torrhus Canyon','treasure','Use hotspot GREAT/OUTSTANDING catches for Giant Water Bug Shards; requires Hunting Fortune and tier data.',pool='torrhus',effort='low')
add('Torrhus · Sepialot Treasure Shards','Torrhus Canyon','treasure','Compare Wooden Bait GOOD/GREAT tier shard yield against bait cost.',pool='torrhus')
add('Torrhus · Stingray/Watersnake Treasure','Torrhus Canyon','treasure','Price each treasure tier and shard type independently; do not assume one tier is dominant.',pool='torrhus')
add('Crimson Isle · Stationary Full-Loot Lava','Crimson Isle','lava','No hotspot travel: fish, kill and value all Thunder/Jawbus and regular lava drops.',target='Thunder',rarity='LEGENDARY',weight=40,pool='crimson_lava',priority=7)
add('Crimson Isle · Thunder Flash I Books','Crimson Isle','lava','Treat Flash I books as a major AH-valued drop rather than ignoring them.',target='Thunder',rarity='LEGENDARY',weight=40,pool='crimson_lava',priority=7)
add('Crimson Isle · Jawbus Solo Boss Loop','Crimson Isle','lava','Account for follower combat phases and non-Bazaar Magma Lord Fragments.',target='Lord Jawbus',rarity='MYTHIC',weight=8,pool='crimson_lava',effort='medium',priority=6)
add('Crimson Isle · Lava Hotspot Short-Route','Crimson Isle','lava-hotspot','Maintain a small local hotspot loop if available, without crossing the entire island.',target='Ragnarok',pool='hotspot_lava',movement='small-area',effort='medium',status='effort-rejected',user_note='User dislikes long Crimson Isle hotspot traversal; short routes only.')
add('Crimson Isle · Full-Rotation Lava Hotspots','Crimson Isle','lava-hotspot','Record maximum hotspot revenue while accounting for long travel effort.',target='Fiery Scuttler',pool='hotspot_lava',movement='long-route',effort='high',status='effort-rejected',user_note='Previously profitable but too annoying for this user; hidden under default preference filter.')
add('Crimson Isle · Trophy Fishing Condition Lab','Crimson Isle','trophy','Complete conditional Trophy Fish collection, not automatically a high-net-profit method.',pool='crimson_lava',effort='medium')
G[-1]['best_documented_setup']['reeling_pet']='Kuudra Pet / highest verified Trophy Chance option for trophy conditions'
G[-1]['best_documented_setup']['hook']='No targeted sea-creature hook; select rod/line for Trophy Chance'
G[-1]['best_documented_setup']['line']='Trophy Line if eligible and valuable for Trophy Chance'
add('Crimson Isle · Trophy Fish Fillet Value','Crimson Isle','trophy','Compare fillet-derived Magmafish value with direct items; no invented trophy yields.',pool='crimson_lava',effort='medium')
add('Crimson Isle · Fire Eel/Taurus Captures','Crimson Isle','hunting','Historic capture method included but marked washed for this user.',target='Taurus',pool='crimson_lava',status='previously-tested',user_note='User tested and called this method washed. Do not promote as a recommendation.')
add('Crimson Isle · Magmafish Secondary Loot','Crimson Isle','lava','Optimize recurring silver magmafish and other routine loot, not only rare bosses.',target='Moogma',rarity='UNCOMMON',weight=1200,pool='crimson_lava')
add('Crystal Hollows · Flaming Worm Membranes','Crystal Hollows','lava-worm','Stationary worm fishing subject to valid location and spawn requirements; compare membranes at current prices.',target='Flaming Worm',status='previously-tested',user_note='Previous price checks suggested low income; keep for comparison.')
add('Crystal Hollows · Silentdepth Wooden Bait','Crystal Hollows','treasure','Collect Silentdepth Shards from GOOD treasure catches and subtract high bait costs.',status='previously-tested',user_note='User called treasure shard pricing washed.')
add('Crystal Hollows · Water Worm Fishing','Crystal Hollows','water','Target water worms only where documented in-game; do not assume they use the basic water pool.',target='Water Worm',status='uncertain-spawn',user_note='Exact currently eligible Water Worm mechanics need verification.')
add('Dwarven Mines · Abyssal Lantern Shards','Dwarven Mines','treasure','Treasure Hook + Wooden Bait for applicable Dwarven shard pool.',status='previously-tested',user_note='User called this washed at current prices.')
add('Dwarven Mines · Basic Water Sea Creatures','Dwarven Mines','water','Baseline water catches and side loot; verify local pool eligibility.',pool='basic_water')
add('Tomb Floodway · Shinyfish Treasure','Tomb Floodway','treasure','Use updated Shinyfish prices instead of historical profits.',status='previously-tested',user_note='User rejected stale valuations; not a priority.')
add('Tomb Floodway · Verdant/Azure Shards','Tomb Floodway','treasure','Evaluate each Wooden Bait zone shard weight and value separately.',status='previously-tested')
add('Tomb Floodway · Flexbone Treasure','Tomb Floodway','treasure','Track Flexbone prices and rarity; historical estimates unreliable.',status='previously-tested')
add('Spider Den · Regular Basic Water Fishing','Spider’s Den','water','Measure ordinary basic water catches versus Garden/Park restrictions.',pool='basic_water')
add('The Park · Chum Sinker Commodity Fishing','The Park','water','Evaluate bait-less commodity Chum materialization per reel versus regular squid farming.',pool='basic_water')
G[-1]['best_documented_setup']['sinker']='Chum Sinker; profit needs real Chum trading price'
add('Private Island · Basic Water Fishing','Private Island','water','Record low-effort fishing baseline; private island SCC penalty must be applied.',pool='basic_water',status='low-prospect',verified_note='SCC on Private Islands is reduced; stated visible SCC may not equal effective SCC.')
add('Garden · Basic Water Fishing','The Garden','water','Record low-effort fishing baseline with Garden SCC penalty and any special rules.',pool='basic_water',status='low-prospect',verified_note='Garden SCC reduction makes this distinct from public-island fishing.')
# Event techniques are in the encyclopedia but hidden by default (user insists on anytime).
add('Shark Fishing Festival · Great White Teeth','Fishing Festival','water','Event-only shark catches and Megalodon rare-drop expected value.',availability='event-only',status='event-only',user_note='Event-dependent: excluded by user’s default anytime-only filter.')
add('Spooky Festival · Bayou Spooky Sea Creatures','Spooky Festival','water','Event-only spooky creature drops plus ordinary fishing revenue.',availability='event-only',status='event-only',user_note='Event-dependent: excluded by user’s default anytime-only filter.')
add('Winter Jerry Workshop · Yeti Fishing','Jerry’s Workshop','water','Winter-island fishing; availability depends on island schedule.',availability='event-only',status='event-only',user_note='Limited-time location; default filter excludes.')
add('Fishing Festival · Shark Hotspot Hybrid','Fishing Festival','water-hotspot','Experimental event overlay; only evaluate while festival active.',availability='event-only',status='event-only',user_note='Festival requirement; default filter excludes.')

STRATEGIES=tuple(G)
BY_ID={s['id']:s for s in STRATEGIES}
assert len(STRATEGIES)==len(BY_ID)

# Fixed schema rather than arbitrary user-generated URL queries.
def summarize(s):
 return {k:s[k] for k in ('id','name','region','style','objective','target','pool','movement','effort','availability','status','tags','user_note','confidence','profit_per_hour','profit_status','global_hypermax_verified','experiment','priority')}

def list_strategies(*,query='',region='',availability='anytime',effort='',show_washed=True,limit=200):
 if availability not in ('anytime','all','event-only'):raise ValueError('Invalid availability')
 q=query.strip().casefold()
 if len(q)>120:raise ValueError('Search query too long')
 try:limit=int(limit)
 except (ValueError,TypeError):raise ValueError('Invalid limit')
 if limit<1 or limit>300:raise ValueError('Limit out of range')
 rows=[s for s in STRATEGIES if
    (availability=='all' or s['availability']==availability)
    and (not region or s['region']==region)
    and (not effort or s['effort']==effort)
    and (show_washed or s['status'] not in ('previously-tested','effort-rejected','low-prospect'))
    and (not q or q in ' '.join((s['name'],s['region'],s['objective'],s['target'],s['user_note'],s['experiment']['name'])).casefold())]
 rows.sort(key=lambda s:(-s['priority'],s['region'],s['name']))
 return {'count':len(rows),'total_catalog':len(STRATEGIES),'items':[summarize(s) for s in rows[:limit]],
         'truncated':len(rows)>limit,'default_availability':'anytime',
         'disclaimer':'Every entry is a strategy/experiment, NOT a verified full-profit estimate. Hypermax loadouts are research candidates until tested.'}

def get_strategy(id):
 return BY_ID.get(id)

def market_observations(strategy,products,live=False):
 """Return market side/coverage only; DO NOT invent method profit, drop odds or AH prices."""
 key=strategy['target']; table=DROPS.get(key) if key else None
 rows=[]
 if table:
  for d in table['drops']:
   product=products.get(d['market_id']) if d.get('market_id') else None
   rows.append({'item':d['name'],'market_id':d['market_id'],'instant_sell':product.get('instant_sell') if product else None,
      'tier':d['tier'],'base_chance':d['chance'],'status':'live-bazaar' if product and live else 'unpriced',
      'source':table['source']})
 return {'target':key,'has_drop_table':bool(table),'market_live':bool(live),
         'item_prices':rows,'full_profit_verified':False,'estimated_profit_per_hour':None,
         'unknown_reason':'Complete creature pool, every drop market, modifiers, and observed catch speed not verified together.'}
