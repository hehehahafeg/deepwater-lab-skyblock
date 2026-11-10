# Deepwater Lab — SkyBlock Fishing Profit Engine

**Version 0.3 — deployable web service with automatically refreshed live Bazaar support; still not a finished discovery system.**

Built for Minecraft IGN **SmackThatCuzzo**, with a strict 40M+ coins/hour target, an anytime-method preference, low movement, and no recycled event-dependent strategies. No Hypixel credentials or payment are needed.

## Best option: hosted HTTPS website

The package now includes a free-plan Render deployment manifest (`render.yaml`) and a `DEPLOY_WEBSITE.md` walkthrough. Deployment requires access to a Render account (and usually a Git repository), and is **not completed or live yet**. On the hosted site, Bazaar prices are fetched server-side and the page checks for updated prices approximately every three minutes. No paid plan is required for a small test deployment, but the free server sleeps after inactivity.

## Alternative: standalone HTML (no installation)

Open **`Offline_Preview.html`** by double-clicking it. The same file is available separately as `Deepwater_Lab_Offline_Preview.html`.

The offline version has:
- Working manual-price squid simulation.
- **Pool Explorer** with 55 Wiki-weighted creatures across eight anytime pools; 18 creature-specific base loot tables and 99 drop entries. It models water/lava hotspot replacement separately from ordinary creatures and visibly withholds incomplete full-method profits.
- An equipment comparison lab enumerating 16 combinations.
- Manual session logging in this browser and a prediction-versus-observation ink error calculation.
- A gear upgrade payback calculator.
- An embedded diagnostics suite.

**Offline mode cannot retrieve live Bazaar prices**. Prices are intentionally unavailable until you enter your own price values. On the **Profit Simulator** tab, expand **Manual price overrides**, enter actual Ink Sac instant-sell, Lily Pad instant-sell, and bait instant-buy prices, then calculate. Offline diagnostics intentionally show the backend health and live-market checks as **BLOCKED**, not as passed.

## Full version with live Bazaar lookup

Requirements: Python 3.11+ and internet access.

**Windows:** Double-click `RUN_WINDOWS.bat`, which installs the Python dependencies, starts the server, and opens the browser on `http://127.0.0.1:8765`.

**macOS/Linux:** run `bash RUN_MAC_LINUX.sh`. Open `http://127.0.0.1:8765`.

The local backend calls the **official public, keyless Hypixel Bazaar endpoint** server-side with a 3-minute cache. `quick_status.buyPrice` is labelled **player instant sell**; `quick_status.sellPrice` is **player instant buy**. The displayed quick-price numbers are weighted approximations, not guaranteed sale executions. Unavailable or stale API data is **not silently replaced with fabricated prices**.

If your school network blocks downloading dependencies or reaching Hypixel, use the offline demo instead. Replit/paid hosting is not required to run locally.

## What the financial model does and does not do

The modeled Birch Park squid subset includes:
- Squid base weight `1200`, Squid Hat `2×`, Common Hook `1.25×` **applied to all common creatures**.
- Sea Creature Chance and Double Hook Chance.
- Level-100 Squid Pet doubling squid drops.
- Natural rain squid spawn ceiling with an adjustable spawn/clearing efficiency factor.
- Ink Sac and Lily Pad base quantities, bait costs and optional paid rain.
- Partial sensitivity to catches/hour and equipment combinations.

The simulator now uses **all ten documented basic-water creature weights** (sum 4,296; Squid 1,200; the other COMMON creature is Sea Walker at 800). The *other common weight* control is intentionally retained as a what-if sensitivity input and its default value is the documented weight.

The new Pool Explorer has the current basic-water, Backwater Bayou, Lotus Atoll, Moonglade Marsh, Torrhus Canyon, Crimson Isle lava, water-hotspot and lava-hotspot pools. Their base creature weights are sourced from the current Wiki. It models Fishing-level unlocks, trophy gates for Thunder and Jawbus, common/special hooks, rare bait weight multipliers, Squid Hat, Tracking, SSC, Double Hook and hotspot replacement up to 85%. Default item costs use **actual instant-buy inputs only if a live market is available**.

The app has **18 creature-specific drop tables out of 55 creatures, totaling 99 base drop entries**. The entire ordinary Bayou pool has a table, and the hotspot pool currently has four of its six tables. Missing auction/Bazaar price mapping, event-specific modifiers, ordinary fishing treasure, Fishing/Sea Creature kill throughput, Looting, Magic Find, squid-pet boost on non-squid drops, true AH valuation, rare pet exclusivity modifiers, charms and downstream mob drops remain incomplete. Do **not** interpret a priced subset as full net or a validated hourly method. Extra creatures and environment conditions can modify observed yields.

The user's observed squid results (30–35M total/hr; 20–25M ink/hr) are displayed independently as real-world reference points, **not inserted into the model's prediction**.

## Test results

- **97 Python automated tests passed** (market mapping/cache/stale behavior, squid and full-pool probability, bait costs, Fishing-level unlocks and hotspot blending, missing prices, API routes, Python–JavaScript parity across five source-backed pool scenarios).
- **Desktop browser (in-process test fixture):** navigation, manual-input calculation, 16 method variants, ordinary Bayou (6 creatures), hotspot+Bayou blend (12 creatures), diagnostics UI; **9 pass / 0 fail / 0 blocked** for embedded checks under controlled prices.
- **Offline browser:** manual-price simulation, 16 variants, Bayou source drop tables and Bayou/hotspot blend worked; offline diagnostics **7 pass / 0 fail / 2 expected blocked** because no backend/live market.
- **Mobile browser:** 390px viewport, mobile navigation and calculator worked without horizontal overflow.

**Not tested/verified:** live retrieval from Hypixel within this execution environment, because outbound DNS/network access is restricted. Data is fetched from your machine when the server runs, provided Hypixel is reachable. The 97 tests do not prove the prediction matches gameplay. No live Bazaar call or independent real-game backtesting was possible from this test environment.

Run the test suite yourself:

    python -m pytest -q

For optional browser smoke tests if Playwright + Chromium are installed:

    python tests/browser_check.py
    python tests/browser_offline_check.py
    python tests/browser_mobile_check.py

The automated browser tests are optional and use fixed **fixture prices** to test logic; those prices are not the current Bazaar.

## Sources

- Hypixel Public API: https://api.hypixel.net/
- Hypixel Wiki — Squid: https://hypixelskyblock.minecraft.wiki/w/Squid
- Hypixel Wiki — Squid Pet: https://hypixelskyblock.minecraft.wiki/w/Squid_Pet
- Hypixel Wiki — Sea Creatures: https://hypixelskyblock.minecraft.wiki/w/Sea_Creatures
- Hypixel Wiki — Common Hook: https://hypixelskyblock.minecraft.wiki/w/Common_Hook
- Hypixel Wiki — Fishing Bait: https://hypixelskyblock.minecraft.wiki/w/Fishing_Bait
- Hypixel Wiki — The Park (rain): https://hypixelskyblock.minecraft.wiki/w/The_Park
- Hypixel Wiki — Lily Pad (`WATER_LILY`): https://hypixelskyblock.minecraft.wiki/w/Lily_Pad

This project is independent and not affiliated with Hypixel. No API key, login, paid service, or purchased assets were used.

## Future milestones (not implemented yet)

1. Complete the remaining 37 creature-specific loot tables, item IDs and non-Bazaar valuation.
2. Live AH-based item valuation for non-Bazaar drops using validated completed sales.
3. Optimize across locations, bait, pet swaps, equipment and movement — with reject rules and full profit coverage.
4. Backtest against independent published sessions and **then** user-measured fishing sessions.
5. Produce credible 40M+/hr candidates only after complete costs and uncertainty checks.

Trustworthy **cross-method** rankings are intentionally empty until those requirements are met.

For the Pool Explorer, visit **Discovery Lab → Fishing pool**, enter your actual fishing stats and select a pool. If using the offline HTML, enter real item prices manually in the JSON box (for example `{"Titanoboa Shed": 1000000}` is an illustrative format, **not a current price**); unpriced items remain flagged. The `known_subtotal_after_bait` label is a subset, **never a method-profit prediction**.
