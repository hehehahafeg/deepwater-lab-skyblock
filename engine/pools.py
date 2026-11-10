"""Citable anytime sea-creature pools and conservative partial-loot projection.

Data transcribed from https://hypixelskyblock.minecraft.wiki/w/Sea_Creatures
and individual creature pages (source URLs shipped on each drop table).

The documented spawn *weights* are complete for ordinary pool rolls. This
is NOT a complete fishing-profit model: fishing treasures, lootshare, magic-find
rules, looting, charms, pet drops and human kill times are not fully covered.
No item with missing prices contributes zero to a purported net profit.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
from math import isfinite
from engine.models import bounded_number

WIKI='https://hypixelskyblock.minecraft.wiki/w/'
SEA_SOURCE=WIKI+'Sea_Creatures'
TRACKING_SOURCE=WIKI+'Tracking'

RARITIES=('COMMON','UNCOMMON','RARE','EPIC','LEGENDARY','MYTHIC')
@dataclass(frozen=True)
class Creature:
    name: str
    base_weight: int
    rarity: str
    min_fishing: int
    requirement: str | None = None
    def serialize(self):
        return {**asdict(self), 'elusive':self.rarity in ('LEGENDARY','MYTHIC'),
                'source':WIKI+self.name.replace(' ','_')}

def c(name,w,rarity,level,requirement=None):return Creature(name,w,rarity,level,requirement)

# Caught from stationary water or lava; hotspot sets are replacements, not additive.
POOLS = {
 'basic_water': {'name':'Basic Water / Birch Park','region':'The Park and other basic water islands','liquid':'water','creatures':[
  c('Squid',1200,'COMMON',1),c('Sea Walker',800,'COMMON',1),c('Sea Witch',700,'UNCOMMON',7),
  c('Sea Archer',550,'UNCOMMON',9),c('Rider of the Deep',400,'UNCOMMON',11),
  c('Catfish',250,'RARE',13),c('Sea Leech',160,'RARE',16),c('Guardian Defender',130,'EPIC',17),
  c('Deep Sea Protector',88,'EPIC',18),c('Water Hydra',18,'LEGENDARY',19)]},
 'bayou': {'name':'Backwater Bayou','region':'Backwater Bayou','liquid':'water','creatures':[
  c('Trash Gobbler',5000,'COMMON',5),c('Dumpster Diver',2875,'UNCOMMON',5),
  c('Banshee',1500,'RARE',10),c('Bayou Sludge',500,'EPIC',15),c('Alligator',100,'LEGENDARY',20),c('Titanoboa',25,'MYTHIC',30)]},
 'lotus': {'name':'Lotus Atoll','region':'Lotus Atoll','liquid':'water','creatures':[
  c('Atoll Croaker',5000,'COMMON',10),c('Lotus Guardian',2875,'UNCOMMON',10),c('gorF',1500,'RARE',10),
  c('Drowned Captain',500,'EPIC',10),c('Puddle Jumper',100,'LEGENDARY',10),c('Frog Prince',25,'MYTHIC',10)]},
 'moonglade': {'name':'Moonglade Marsh','region':'Galatea','liquid':'water','creatures':[
  c('Bogged',5000,'COMMON',5),c('Wetwing',2875,'UNCOMMON',7),c('Tadgang',1500,'RARE',9),
  c('Ent',500,'EPIC',12),c('The Loch Emperor',100,'LEGENDARY',20),c('Nessie',25,'MYTHIC',25)]},
 'torrhus': {'name':'Torrhus Canyon','region':'Torrhus Canyon','liquid':'water','creatures':[
  c('Haggard',5000,'COMMON',15),c('Brineling',2875,'UNCOMMON',15),c('Sprawl',1500,'RARE',15),
  c('Torrid',500,'EPIC',15),c('Silkbreeze',100,'LEGENDARY',15),c('Giant Isopod',25,'MYTHIC',15)]},
 'crimson_lava': {'name':'Crimson Isle stationary lava','region':'Crimson Isle','liquid':'lava','creatures':[
  c('Magma Slug',1600,'UNCOMMON',27),c('Moogma',1200,'UNCOMMON',28),c('Lava Leech',600,'RARE',30),
  c('Pyroclastic Worm',400,'RARE',31),c('Lava Flame',360,'RARE',33),c('Fire Eel',280,'RARE',34),
  c('Taurus',160,'EPIC',35),c('Thunder',40,'LEGENDARY',36,'Novice Trophy Fisher'),
  c('Lord Jawbus',8,'MYTHIC',45,'Adept Trophy Fisher')]},
 'hotspot_water': {'name':'Water hotspot override pool','region':'Any eligible water hotspot','liquid':'water','is_override':True,'creatures':[
  c('Frog Man',5000,'COMMON',5),c('Inkling',2875,'UNCOMMON',7),c('Snapping Turtle',1500,'RARE',10),
  c('Manta Ray',500,'EPIC',19),c('Blue Ringed Octopus',100,'LEGENDARY',35),c('Wiki Tiki',25,'MYTHIC',40)]},
 'hotspot_lava': {'name':'Crimson lava hotspot override pool','region':'Crimson Isle hotspot','liquid':'lava','is_override':True,'creatures':[
  c('Fried Chicken',5000,'COMMON',14),c('Volcanic Snail',2875,'UNCOMMON',17),c('Fireproof Witch',1500,'RARE',22),
  c('Magma Pillar',500,'EPIC',31),c('Fiery Scuttler',100,'LEGENDARY',37),c('Ragnarok',25,'MYTHIC',47)]},
}

# Drops: (visible_name, item_key, min_quantity, max_quantity, base_chance, tier)
# `item_key` is a Bazaar candidate identifier, NOT proof of current Bazaar listing.
# None = deliberately unpriced until a verifiable market mapping exists.
# Tier 'jackpot' deliberately separated from recurring EV.
# All rare chances are BASE before special MF/Looting. We do not blindly apply MF.
DROPS:dict[str,dict[str,Any]]={}
def record(mob: str, rows, source=None, note=None):
    DROPS[mob]={'source': source or (WIKI+mob.replace(' ','_')),'note':note,
                'drops':[dict(name=row[0],market_id=row[1],min_quantity=row[2],max_quantity=row[3],chance=row[4],tier=row[5],
                              expected_quantity=row[6] if len(row)>6 else (row[2]+row[3])/2)
                    for row in rows]}

def d(n,mid,mn,mx,p=1,tier='common',expected=None):return (n,mid,mn,mx,p,tier,*((expected,) if expected is not None else ()))

record('Squid',[
 d('Ink Sac','INK_SACK',2,3),d('Lily Pad','WATER_LILY',1,2),
 d('Enchanted Ink Sac','ENCHANTED_INK_SACK',1,1,.005,'rare'),
 d('Squid Boots',None,1,1,.01,'rare'),
 d('Aquamarine Dye',None,1,1,1/5_000_000,'jackpot')], note='Pet double-drop effects and Looting on enchanted ink require separate verification.')
record('Alligator',[
 d('Enchanted Lily Pad','ENCHANTED_LILY_PAD',2,4), d('Alligator Skin',None,1,1),
 d('Condensed Lily Pad',None,1,1,.005,'rare'),d('Aquamarine Dye',None,1,1,1/50_000,'jackpot')])
record('Titanoboa',[
 d('Enchanted Lily Pad','ENCHANTED_LILY_PAD',2,4),d('Condensed Lily Pad',None,1,1,.01,'rare'),
 d("Bobbin’ Scriptures",None,1,1,.01,'rare'), d('Titanoboa Shed',None,1,1,.002,'rare'),
 d('Snake Eyes',None,1,1,.0011,'rare'), d('Aquamarine Dye',None,1,1,1/50_000,'jackpot')])
record('Puddle Jumper',[
 d('Silver Lotus',None,1,1),d('Puddle Jumper Trophy Frog',None,1,1),
 d('Gold Lotus',None,1,1,.01,'rare'),d('Aquamarine Dye',None,1,1,1/50_000,'jackpot')],
 note='Puddle Jumper has a multi-jump fishing minigame; cast rate cannot be reused without time adjustments.')
record('Frog Prince',[
 d('Silver Lotus',None,8,8),d('Gold Lotus',None,1,1,.05,'rare'),
 d("Prince’s Crown Jewel",None,1,1,.0025,'rare'),d('Aquamarine Dye',None,1,1,1/50_000,'jackpot')])
record('The Loch Emperor',[
 d('Sea Lumies',None,32,64),d('Enchanted Mangrove Log',None,8,16),
 d("Emperor’s Skull",None,1,1,.2),d('Enchanted Sea Lumies',None,1,1,.2,'rare'),
 d('Rare Flying Fish Pet',None,1,1,.04,'rare'),d('Epic Flying Fish Pet',None,1,1,.02,'rare'),
 d('Legendary Flying Fish Pet',None,1,1,.005,'jackpot'),
 d('Mangcore',None,1,1,.01,'rare'),d('Aquamarine Dye',None,1,1,1/50_000,'jackpot')],
 note='Flying Fish pet rarities are mutually exclusive. Base chances shown without Magic Find or Pet Luck.')
record('Nessie',[
 d('Enchanted Mangrove Log',None,16,32),d('Enchanted Sea Lumies',None,2,4),
 d('Mangcore',None,1,1,.1,'rare'),d('Mound of Seagrass',None,1,1,.02,'rare'),
 d("Bobbin’ Scriptures",None,1,1,.01,'rare'),d('Vibrant Coral',None,1,1,.005,'rare'),
 d('Aquamarine Dye',None,1,1,1/50_000,'jackpot')],
 note='Nessie leaves the original fishing area during its fight; modeled spawns do not imply efficient kills.')
record('Silkbreeze',[
 d('Enchanted Helix Log',None,4,8),d('Enchanted Ruby Veilshroom',None,1,1),
 d('Sublime Silk',None,1,1,.2,'rare'),d('Veilshroom Bunch',None,1,1,.01,'rare'),
 d('Helixis',None,1,1,.01,'rare'),d('Distant Echo',None,1,1,.01,'rare'),
 d('Aquamarine Dye',None,1,1,1/50_000,'jackpot')])
record('Thunder',[
 d('Thunder Fragment',None,1,1),d('Silver Magmafish',None,8,16),
 d('Flash I book',None,1,1,.015,'rare'),d('Carmine Dye',None,1,1,1/50_000,'jackpot')],
 note='Flash I book is a major non-Bazaar-valued drop and MUST be included before net profit can be trusted.')
record('Lord Jawbus',[
 d('Magma Lord Fragment',None,1,1),d('Silver Magmafish',None,16,32),
 d('Lord Jawbus Shard',None,1,1,.02,'rare'),d("Bobbin’ Scriptures",None,1,1,.01,'rare'),
 d('Radioactive Vial',None,1,1,.005,'rare'), d('Carmine Dye',None,1,1,1/50_000,'jackpot')],
 note='Fight has follower phases; bait and high catch rates alone cannot establish achievable kills/hour.')
record('Blue Ringed Octopus',[
 d('Enchanted Clay Ball','ENCHANTED_CLAY_BALL',2,4),d('Blue Ring',None,1,1),
 d('Enchanted Clay Block','ENCHANTED_CLAY_BLOCK',1,1,.005,'rare'),
 d('Octopus Tendril',None,1,1,.001,'rare'),d('Aquamarine Dye',None,1,1,1/50_000,'jackpot')])
record('Wiki Tiki',[
 d('Enchanted Jungle Wood','ENCHANTED_JUNGLE_LOG',8,16),d('Enchanted Clay Ball','ENCHANTED_CLAY_BALL',8,16),
 d('Enchanted Clay Block','ENCHANTED_CLAY_BLOCK',1,1,.01,'rare'),
 d("Bobbin’ Scriptures",None,1,1,.01,'rare'), d('Troubled Bubble',None,1,1,.002,'rare'),
 d('Tiki Mask',None,1,1,.001,'jackpot'),d('Aquamarine Dye',None,1,1,1/50_000,'jackpot')])


# May 2026 revised Backwater Bayou loot tables. These six complete the
# documented creature-by-creature *base* drop entries for ordinary Bayou.
record('Trash Gobbler',[
 d('Lily Pad','WATER_LILY',1,2),
 d('Can of Worms',None,1,1,.05,'rare'),
 d('Aquamarine Dye',None,1,1,1/5_000_000,'jackpot')])
record('Dumpster Diver',[
 d('Lily Pad','WATER_LILY',2,4),
 d('Bronze Bowl',None,1,1,.02,'rare'),
 d('Enchanted Lily Pad','ENCHANTED_LILY_PAD',1,1,.01,'rare'),
 d('Overflowing Trash Can',None,1,1,.005,'rare'),
 d('Aquamarine Dye',None,1,1,1/5_000_000,'jackpot')])
record('Banshee',[
 d('Lily Pad','WATER_LILY',8,16),
 d('Torn Cloth',None,1,1,.03,'rare'),
 d('Enchanted Lily Pad','ENCHANTED_LILY_PAD',1,1,.02,'rare'),
 d('Calcified Heart',None,1,1,.001,'rare'),
 d('Aquamarine Dye',None,1,1,1/2_500_000,'jackpot')])
record('Bayou Sludge',[
 d('Lily Pad','WATER_LILY',16,32),
 d('Slimeball','SLIME_BALL',16,32),
 d('Enchanted Lily Pad','ENCHANTED_LILY_PAD',1,1,.04,'rare'),
 d('Enchanted Slimeball','ENCHANTED_SLIME_BALL',1,1,.04,'rare'),
 d('Poison Sample',None,1,1,.005,'rare'),
 d('Blessing VI enchanted book',None,1,1,.001,'rare'),
 d('Enchanted Slime Block','ENCHANTED_SLIME_BLOCK',1,1,.0005,'rare'),
 d('Aquamarine Dye',None,1,1,1/2_500_000,'jackpot')],
 note='Two or three spawned Bayou Sludglings are NOT included in loot earnings.')
record('Inkling',[
 d('Clay Ball','CLAY_BALL',2,4),d('Ink Sac','INK_SACK',2,4),
 d('Ink Splat',None,1,1,.04,'rare'),
 d('Enchanted Ink Sac','ENCHANTED_INK_SACK',1,1,.01,'rare'),
 d('Enchanted Clay Ball','ENCHANTED_CLAY_BALL',1,1,.01,'rare'),
 d('Uncommon Fishing Exp Boost',None,1,1,.0005,'rare'),
 d('Aquamarine Dye',None,1,1,1/5_000_000,'jackpot')])
record('Frog Man',[
 d('Clay Ball','CLAY_BALL',1,2),d('Half-Eaten Mushroom',None,1,1),
 d('Aquamarine Dye',None,1,1,1/5_000_000,'jackpot')])


# Complete documented BASE item drop tables for ordinary/basic water fishing.
# Conditional additions are represented with expected quantities where the
# distribution is not uniform; non-Bazaar items remain explicitly unpriced.
record('Sea Walker',[
 d('Rotten Flesh','ROTTEN_FLESH',5,9,1,'common',6.5),
 d('Raw Cod','RAW_FISH',2,2),d('Lily Pad','WATER_LILY',1,1),
 d('Aquamarine Dye',None,1,1,1/5_000_000,'jackpot')])
record('Sea Witch',[
 d('Raw Salmon','RAW_SALMON',1,3,1,'common',2),
 d('Lily Pad','WATER_LILY',1,2),
 d('Tropical Fish','CLOWNFISH',1,1,.2),
 d('Fairy Armor Piece',None,1,1,.05,'rare'),
 d('Aquamarine Dye',None,1,1,1/5_000_000,'jackpot')])
record('Sea Archer',[
 d('Raw Cod','RAW_FISH',2,2),d('Lily Pad','WATER_LILY',1,1),
 d('Bone','BONE',8,13,1,'common',10.5),
 d('Enchanted Bone','ENCHANTED_BONE',1,1,.01,'rare'),
 d('Bone Dye',None,1,1,1/3_000_000,'jackpot'),
 d('Aquamarine Dye',None,1,1,1/5_000_000,'jackpot')])
record('Rider of the Deep',[
 d('Lily Pad','WATER_LILY',2,2),
 d('Dark Bait','DARK_BAIT',1,1,.5),
 d('Enchanted Feather','ENCHANTED_FEATHER',1,1,.5),
 d('Enchanted Rotten Flesh','ENCHANTED_ROTTEN_FLESH',1,1,.5),
 d('Sponge','SPONGE',1,1,.2),
 d('Magnet VI book',None,1,1,.02,'rare'),
 d('Aquamarine Dye',None,1,1,1/5_000_000,'jackpot')])
record('Catfish',[
 d('Raw Cod','RAW_FISH',20,20),d('Raw Salmon','RAW_SALMON',10,10),
 d('Pufferfish','PUFFERFISH',5,5),d('Tropical Fish','CLOWNFISH',2,2),
 d('Lily Pad','WATER_LILY',2,3),d('Sponge','SPONGE',1,1,.2),
 d('Frail VI book',None,1,1,.01,'rare'),
 d('Aquamarine Dye',None,1,1,1/2_500_000,'jackpot')])
record('Sea Leech',[
 d('Raw Cod','RAW_FISH',10,10),d('Lily Pad','WATER_LILY',3,4),
 d('Tropical Fish','CLOWNFISH',2,2),d('Sponge','SPONGE',1,1,.4),
 d('Spiked Hook VI book',None,1,1,.02,'rare'),
 d('Aquamarine Dye',None,1,1,1/2_500_000,'jackpot')])
record('Guardian Defender',[
 d('Raw Cod','RAW_FISH',15,15),d('Lily Pad','WATER_LILY',5,7,1,'common',6.1),
 d('Sponge','SPONGE',1,1),
 d('Enchanted Prismarine Shard','ENCHANTED_PRISMARINE_SHARD',1,1,.6),
 d('Enchanted Prismarine Crystals','ENCHANTED_PRISMARINE_CRYSTALS',1,1,.5),
 d('Lure VI book',None,1,1,.02,'rare'),
 d('Aquamarine Dye',None,1,1,1/2_500_000,'jackpot')])
record('Deep Sea Protector',[
 d('Lily Pad','WATER_LILY',12,15),d('Enchanted Iron Ingot','ENCHANTED_IRON',2,2),
 d('Tropical Fish','CLOWNFISH',2,3),d('Sponge','SPONGE',1,1),
 d('Angler VI book',None,1,1,.02,'rare'),
 d('Aquamarine Dye',None,1,1,1/2_500_000,'jackpot')])
record('Water Hydra',[
 d('Raw Cod','RAW_FISH',20,20),d('Raw Salmon','RAW_SALMON',2,2),
 d('Pufferfish','PUFFERFISH',2,2),d('Tropical Fish','CLOWNFISH',2,2),
 d('Sponge','SPONGE',5,5),d('Lily Pad','WATER_LILY',16,18,1,'common',17),
 d('Fish Affinity Talisman',None,1,1,.30,'rare'),
 d('Water Hydra Head',None,1,1,.14,'rare'),
 d('Aquamarine Dye',None,1,1,1/50_000,'jackpot')],
 note='One hooked Water Hydra splits at half health; both Hydras can drop items if killed. Two kills per catch is conditional.')

# Drop data covers only individually checked pages. Never imply the entire pool is valued.
REVIEW_DATE='2026-11-10'

def catalog_summary():
    return {'source':SEA_SOURCE,'reviewed_on':REVIEW_DATE,'anytime_pools':len(POOLS),
            'creatures':sum(len(p['creatures']) for p in POOLS.values()),
            'creature_drop_tables':len(DROPS),'drop_items':sum(len(v['drops']) for v in DROPS.values()),
            'status':'base spawn pools sourced; partial drop tables, not complete method profit'}

def public_catalog():
    return {'summary':catalog_summary(), 'pools':[
       {'id':id,'name':pool['name'],'region':pool['region'],'liquid':pool['liquid'],
        'is_override':pool.get('is_override',False),'creatures':[cr.serialize()|{'has_drop_table':cr.name in DROPS} for cr in pool['creatures']]}
       for id,pool in POOLS.items()],
       'drop_tables':DROPS,'sources':{'sea_creatures':SEA_SOURCE,'tracking':TRACKING_SOURCE},
       'limitations':['Events excluded','Unlisted creature drops are not zero','Magic Find and Looting not applied to base drops','Potential Bazaar IDs are not proof a tradeable market exists']}

def rarity_weighted_pool(pool_id:str, *, fishing_level=50, tracking=0,
                         bait='NONE', time_of_day='day', hook='NONE', squid_hat=False,
                         novice_trophy_fisher=True, adept_trophy_fisher=True):
    if pool_id not in POOLS: raise ValueError('Unknown fishing pool')
    fishing_level=bounded_number(fishing_level,'Fishing level',0,60)
    tracking=bounded_number(tracking,'Tracking',0,300)
    if bait not in ('NONE','FISH_BAIT','SPIKED_BAIT','LIGHT_BAIT','DARK_BAIT','WHALE_BAIT','HOTSPOT_BAIT','WOODEN_BAIT','MINNOW_BAIT'):
        raise ValueError('Unsupported bait')
    if time_of_day not in ('day','night'):raise ValueError('Time must be day or night')
    if hook not in ('NONE','COMMON_HOOK','PUDDLE_JUMPER_HOOK','HOTSPOT_HOOK'):
        raise ValueError('Unsupported hook')
    # modifiers are multiplicative on eligible weights, then denominator normalized.
    rare_bait=(bait=='WHALE_BAIT' or (bait=='LIGHT_BAIT' and time_of_day=='day')
               or (bait=='DARK_BAIT' and time_of_day=='night'))
    weights=[]
    for cr in POOLS[pool_id]['creatures']:
        if fishing_level<cr.min_fishing:continue
        if cr.requirement=='Novice Trophy Fisher' and not novice_trophy_fisher:continue
        if cr.requirement=='Adept Trophy Fisher' and not adept_trophy_fisher:continue
        factor=1.0
        if rare_bait and cr.base_weight<400:factor*=1.25
        if hook=='COMMON_HOOK' and cr.rarity=='COMMON':factor*=1.25
        if hook=='PUDDLE_JUMPER_HOOK' and cr.name=='Puddle Jumper':factor*=5
        if squid_hat and cr.name in ('Squid','Inkling'):factor*=2
        if cr.rarity in ('LEGENDARY','MYTHIC'):factor*=1+tracking/100
        weights.append((cr,cr.base_weight*factor))
    total=sum(w for _,w in weights)
    if total<=0:raise ValueError('No unlocked creatures in this pool')
    return [{'name':cr.name,'rarity':cr.rarity,'base_weight':cr.base_weight,
             'modified_weight':w,'probability':w/total,'fishing_level':cr.min_fishing,
             'source':WIKI+cr.name.replace(' ','_'),'has_drop_table':cr.name in DROPS}
            for cr,w in weights]

def project_pool(params:dict, prices:dict, *, prices_live:bool=False):
    pool_id=params.get('pool','basic_water')
    reels=bounded_number(params.get('reels_per_hour',1050),'Reels/hour',0,5000)
    scc=bounded_number(params.get('sea_creature_chance',100),'Sea Creature Chance',0,100)
    dh=bounded_number(params.get('double_hook_chance',30),'Double Hook Chance',0,100)
    tracking=params.get('tracking',0)
    loot=rarity_weighted_pool(pool_id,fishing_level=params.get('fishing_level',50),tracking=tracking,
                            bait=params.get('bait','NONE'),time_of_day=params.get('time_of_day','day'),
                            hook=params.get('hook','NONE'),squid_hat=params.get('squid_hat',False),
                            novice_trophy_fisher=params.get('novice_trophy_fisher',True),
                            adept_trophy_fisher=params.get('adept_trophy_fisher',True))
    # Hotspots OVERRIDE ordinary sea-creature rolls; do not treat their pool
    # as a normal 100% pool when modelling a real fishing session.
    override_share=None
    if POOLS[pool_id].get('is_override'):
        override_share=bounded_number(params.get('hotspot_override_percent',15),
                                      'Hotspot override percent',0,85)/100
        base_id=params.get('base_pool','bayou' if pool_id=='hotspot_water' else 'crimson_lava')
        if base_id not in POOLS or POOLS[base_id].get('is_override'):
            raise ValueError('Select an ordinary underlying pool')
        if POOLS[base_id]['liquid']!=POOLS[pool_id]['liquid']:
            raise ValueError('Hotspot and underlying pool must use the same liquid')
        base=rarity_weighted_pool(base_id,fishing_level=params.get('fishing_level',50),tracking=tracking,
                                  bait=params.get('bait','NONE'),time_of_day=params.get('time_of_day','day'),
                                  hook=params.get('hook','NONE'),squid_hat=params.get('squid_hat',False),
                                  novice_trophy_fisher=params.get('novice_trophy_fisher',True),
                                  adept_trophy_fisher=params.get('adept_trophy_fisher',True))
        for mob in loot: mob['probability']*=override_share
        for mob in base: mob['probability']*=1-override_share
        loot=base+loot
    total_expected=reels*scc/100*(1+dh/100)
    subtotal=0.0; base_rare=0.0; jackpot=0.0
    unpriced=[];priced=[];unmodelled=[];rows=[]
    # A caller can set manually researched prices on a per-name basis. Every such use
    # is explicitly labelled unverified and cannot produce a verified full profit.
    manual=params.get('manual_item_prices',{})
    if not isinstance(manual,dict):raise ValueError('Manual prices must be a dictionary')
    squid_pet=bool(params.get('squid_pet',False))
    pet_multiplier=bounded_number(params.get('squid_pet_multiplier',2 if squid_pet else 1),'Squid Pet expected drop multiplier',1,2)
    if not squid_pet:pet_multiplier=1
    natural_squids=bounded_number(params.get('natural_squids_per_hour',0),'Natural squids/hour',0,100000)
    hydra_kills=bounded_number(params.get('hydra_kills_per_catch',1),'Hydra kills/catch',1,2)
    for mob in loot:
        spawn_count=total_expected*mob['probability']
        kills=spawn_count+(natural_squids if mob['name']=='Squid' else 0)
        if mob['name']=='Water Hydra':kills*=hydra_kills
        entry={'name':mob['name'],'probability':mob['probability'],'expected_per_hour':spawn_count,'expected_kills_per_hour':kills,
               'base_weight':mob['base_weight'],'modified_weight':mob['modified_weight'],
               'has_drop_table':mob['has_drop_table'],'drops':[],'source':mob['source']}
        drop_info=DROPS.get(mob['name'])
        if drop_info is None:
            if spawn_count>0:unmodelled.append(mob['name'])
        else:
            for d in drop_info['drops']:
                per_mob=d['expected_quantity']*d['chance']
                qty=kills*per_mob*(pet_multiplier if mob['name']=='Squid' else 1)
                price=None;price_type=None
                # Bazaar prices are player INSTANT SELL for drops, and no price
                # is inferred for AH items. Manual item prices keyed by exact item name.
                if d['market_id']:
                    price_record=prices.get(d['market_id'])
                    if isinstance(price_record,dict):
                        v=price_record.get('instant_sell')
                        try:
                            if v is not None and isfinite(float(v)) and float(v)>0:
                                price=float(v);price_type='bazaar-live' if prices_live else 'bazaar-unverified'
                        except (ValueError,TypeError,OverflowError):pass
                if price is None and d['name'] in manual:
                    price=bounded_number(manual[d['name']],f"Manual price for {d['name']}",0,1e12)
                    if price==0:price=None
                    else:price_type='manual-unverified'
                val=qty*price if price is not None else None
                if val is None and qty>0:unpriced.append({'mob':mob['name'],'drop':d['name'],'expected_units':qty})
                if val is not None:
                    priced.append({'mob':mob['name'],'drop':d['name'],'coins':val,'price_type':price_type})
                    if d['tier']=='jackpot':jackpot+=val
                    elif d['tier']=='rare':base_rare+=val
                    else:subtotal+=val
                entry['drops'].append({'name':d['name'],'market_id':d['market_id'],
                           'base_chance':d['chance'],'expected_quantity_per_kill':d['expected_quantity'], 'expected_units':qty,
                           'tier':d['tier'],'unit_price':price,'price_source':price_type,'expected_coins':val,
                           'source':drop_info['source']})
        rows.append(entry)
    # Operating costs: require current instant-BUY input price or a manual price.
    bait=params.get('bait','NONE')
    saved=bounded_number(params.get('bait_saved_percent',10),'Bait saved percent',0,100)
    bprice=0.0 if bait=='NONE' else None
    if bait!='NONE':
        record=prices.get(bait)
        if isinstance(record,dict):
            try:
                v=float(record['instant_buy'])
                if isfinite(v) and v>0:bprice=v
            except (ValueError,TypeError,KeyError,OverflowError):pass
        if bprice is None and params.get('manual_bait_price') is not None:
            v=bounded_number(params['manual_bait_price'],'Manual bait price',0,1e10)
            if v>0:bprice=v
    cost_bait=(reels*(1-saved/100)*bprice) if bprice is not None else None
    # The evaluated subset MUST NEVER be mistaken for full profitability.
    subtotal_and_rare=subtotal+base_rare
    return {'pool':pool_id,'pool_name':POOLS[pool_id]['name'],'creature_rate':total_expected,'hotspot_override_percent':None if override_share is None else override_share*100,
      'creatures':rows,'known_common_revenue':subtotal,'known_rare_base_ev':base_rare,
      'known_jackpot_base_ev':jackpot,'known_subtotal':subtotal_and_rare,
      'known_subtotal_after_bait':subtotal_and_rare-cost_bait if cost_bait is not None else None,
      'bait_cost':cost_bait,'bait_price':bprice,
      'unpriced':unpriced,'unmodelled':unmodelled,
      'has_complete_loot':not (unpriced or unmodelled),
      'is_full_method_profit':False, 'prices_live':prices_live,
      'warnings':['Partial financial coverage: prices are missing and/or full loot behavior is unmodelled.',
                  'Base drop rates only. Squid Pet double drops on Squids are applied when enabled; Magic Find, Looting, other pets, charm shards, loot-sharing and actual kill time are not applied.',
                  'Bait cost is known only when priced; full net profit is deliberately unavailable.',
                  'Jackpot expected value is shown separately and not treated as recurring revenue.'],
      'sources':{'pool':SEA_SOURCE,'tracking':TRACKING_SOURCE}}
