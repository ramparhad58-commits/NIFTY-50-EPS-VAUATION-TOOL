#!/usr/bin/env python3
"""Fetch Nifty 50 EOD close + P/E and write data.json.
Runs in GitHub Actions (server-side, so no browser CORS limits).
Price: Yahoo Finance JSON (no key). P/E: NSE niftyindices, with graceful fallback."""
import json, os, datetime, urllib.request, http.cookiejar

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def yahoo_price():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?range=7d&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    r = d["chart"]["result"][0]
    closes, ts = r["indicators"]["quote"][0]["close"], r["timestamp"]
    for c, t in zip(reversed(closes), reversed(ts)):
        if c is not None:
            day = datetime.datetime.fromtimestamp(t, IST).strftime("%Y-%m-%d")
            return round(float(c), 2), day
    raise RuntimeError("no Yahoo close")

def nse_pe():
    """Return (pe, close, date) from NSE; raises on any failure."""
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    base = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
    op.open(urllib.request.Request(
        "https://www.niftyindices.com/reports/historical-data", headers=base), timeout=30).read()
    end = datetime.datetime.now(IST); start = end - datetime.timedelta(days=10)
    payload = {"cinfo": "{'name':'NIFTY 50','startDate':'%s','endDate':'%s','indexName':'NIFTY 50'}"
               % (start.strftime("%d-%b-%Y"), end.strftime("%d-%b-%Y"))}
    h = dict(base); h.update({"Content-Type": "application/json; charset=UTF-8",
        "Referer": "https://www.niftyindices.com/reports/historical-data",
        "X-Requested-With": "XMLHttpRequest"})
    req = urllib.request.Request(
        "https://www.niftyindices.com/Backpage.aspx/getpepbHistoricaldatatabletoString",
        data=json.dumps(payload).encode(), headers=h)
    obj = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    rows = json.loads(obj["d"])
    def g(r, *keys):
        for k in keys:
            for kk in r:
                if kk.lower().replace(" ", "") == k:
                    return r[kk]
        return None
    clean = []
    for r in rows:
        pe = g(r, "pe"); 
        if pe in (None, "", "-"): continue
        clean.append((g(r, "historicaldate", "date") or "", float(pe),
                      float(g(r, "close", "closingvalue") or 0)))
    clean.sort()
    date, pe, close = clean[-1]
    return pe, close, date

def main():
    today = datetime.datetime.now(IST).strftime("%Y-%m-%d")
    # load previous
    prev = {}
    if os.path.exists("data.json"):
        prev = json.load(open("data.json"))
    last_eps = float(prev.get("eps") or 1143.8)   # seed EPS
    history = prev.get("history", [])

    price, pdate = yahoo_price()
    source = "Yahoo price + last EPS (NSE unavailable)"
    eps = last_eps
    try:
        pe_nse, close_nse, ndate = nse_pe()
        base = close_nse or price
        eps = round(base / pe_nse, 2)
        source = "NSE (niftyindices) + Yahoo price"
    except Exception as e:
        print("NSE fetch failed, falling back:", repr(e))

    pe = round(price / eps, 2)
    snap = {"date": pdate, "nifty": price, "pe": pe, "eps": eps}
    # upsert into history
    history = [h for h in history if h.get("date") != pdate] + [snap]
    history.sort(key=lambda h: h["date"])
    history = history[-1500:]  # ~6 years

    out = {"updated": today, "asof": pdate, "nifty": price, "eps": eps, "pe": pe,
           "source": source, "history": history}
    json.dump(out, open("data.json", "w"), indent=1)
    print("WROTE", today, "nifty", price, "eps", eps, "pe", pe, "|", source)

if __name__ == "__main__":
    main()
