# Nifty 50 Valuation Meter — auto-updating (free)

A self-updating Nifty 50 P/E valuation gauge. A scheduled GitHub Action pulls the
end-of-day close + P/E every market day and commits `data.json`; GitHub Pages serves
the meter, which reads that file. **You never type anything.**

## Files
- `index.html` — the meter page (gauge, fair-value ladder, P/E history chart)
- `fetch_nifty.py` — EOD fetcher (Python standard library only — no pip installs)
- `data.json` — the data the page reads (the bot overwrites this daily)
- `.github/workflows/eod.yml` — the daily scheduler (16:00 IST, Mon–Fri)

## One-time setup (~5 minutes)
1. Create a new **public** GitHub repo, e.g. `nifty-meter`.
2. Upload all these files, keeping the folder structure
   (`.github/workflows/eod.yml` must stay in that path).
3. Repo **Settings → Actions → General →** under *Workflow permissions*
   pick **Read and write permissions**, Save.
4. Repo **Settings → Pages →** Source = *Deploy from a branch*, Branch = `main` / `root`, Save.
   After a minute your page is live at `https://<your-username>.github.io/nifty-meter/`.
   Bookmark it.
5. Repo **Actions** tab → select **Nifty EOD update** → **Run workflow** once to populate
   live data immediately (otherwise it first runs at the next 16:00 IST).

That's it. From then on it refreshes itself every trading day.

## How the data is sourced
- **Price:** Yahoo Finance EOD JSON for `^NSEI` (no key, very reliable).
- **P/E & EPS:** NSE (niftyindices.com). If NSE blocks the runner on a given day,
  the script falls back to `price ÷ last-known EPS`. Since index EPS only changes when
  quarterly results land, this stays accurate between result seasons.
- If you ever want to hard-set EPS after a results season, edit the `"eps"` value in
  `data.json` once — the bot carries it forward.

## Notes
- Cron times in GitHub Actions are **UTC**; `30 10 * * 1-5` = 16:00 IST, weekdays.
  GitHub may delay scheduled runs by a few minutes under load — harmless for EOD.
- Valuation zones use the **post-2021 consolidated-earnings** P/E history
  (5-yr range ~18.9–30.5, long-run avg ~22.5). Not investment advice.
