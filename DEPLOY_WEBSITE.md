# Publish Deepwater Lab as a website (free-tier prototype)

This project is a FastAPI application that hosts its own browser frontend and a server-side Hypixel Bazaar data proxy. It is **NOT** published just because this file exists.

## Recommended: Render free web service

The included `render.yaml` configures a free Python web service. Hosting is subject to Render's current limits and terms; the free service sleeps after roughly 15 minutes without traffic and may take about one minute to wake. No paid plan is required for a modest hobby prototype.

1. Create a GitHub repository for this project, including `app.py`, `engine/`, `static/`, `requirements.txt`, and `render.yaml` at repository root. Do not commit `.env`, credentials, or secrets.
2. Connect your GitHub repository to Render using its dashboard or the Render connection in ChatGPT. Choose **New > Blueprint** and select the repository, which reads `render.yaml`; select the free plan and review that nothing is billable. Alternatively choose **New > Web Service**, Python runtime, Free, build `pip install -r requirements.txt`, start `uvicorn app:app --host 0.0.0.0 --port $PORT`.
3. Once the deploy succeeds, Render provides an HTTPS `onrender.com` URL. Open it on your Chromebook (subject to school site restrictions). The **Bazaar monitor** fetches actual public Hypixel quick-status prices via the server; the page polls the server about every 3 minutes.

## Verify the actual hosted website

- Visit `/api/health` at your Render URL. It should report `status: ok`.
- Visit `/api/prices`. It should report `live: true`, a real `checked_at` timestamp, and hundreds of items, with `INK_SACK` where available. If `live:false`, inspect `last_error`: your host might not reach Hypixel. Do not rely on `stale` values as live.
- Open the **Bazaar monitor** page and press **Refresh Bazaar**. Confirm the UI says LIVE MARKET.
- Open **Diagnostics** and press **Run functional checks**. Check for no failures and distinguish live checks from deterministic tests.
- The calculator still has **partial** fishing loot coverage: a live Bazaar connection does NOT make the model's predicted whole-method profit accurate.

## Security and cost

The public Hypixel Bazaar API is keyless. All requests use HTTPS and server caching to reduce load. No Minecraft authentication, personal password, or API key is required. The prototype stores field-session notes in that browser's local storage only; they will not automatically sync between school Chromebook and home computer.

## Limitations

Live pricing requires server internet and Hypixel API availability. Free Render web services sleep after inactivity; the first page load may be slow. Hosting won't bypass school web restrictions. Game-mechanics completeness and actual profit validation remain separate development milestones.
