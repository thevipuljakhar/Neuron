# NEURON v2 — Indian RE Intelligence Monitor
**by Vipul Jakhar**  |  **Snapshot: 2026-06-03 12:51**  |  **All endpoints verified live**

---

## Quick Start

```bash
cd "D:\Polygon\Git Projects\Neuron"
python neuron.py
# Then open http://localhost:5000
```

### One-time setup (already completed)

```bash
pip install flask yfinance feedparser numpy requests pandas beautifulsoup4 openpyxl
playwright install chromium
```

---

## Project Structure

```
Neuron/
  neuron.py                <- Flask backend (381 lines)
  templates/
    index.html             <- Full dashboard UI (1064 lines, Solarized Dark)
  requirements.txt
  start.bat                <- Windows one-click launcher
  NEURON_V2_SNAPSHOT.md   <- This recovery file
```

---

## Data Sources — All Free, Zero API Keys

| Source | URL | Cache TTL | Data |
|--------|-----|-----------|------|
| MNRE Physical Progress | mnre.gov.in/en/physical-progress/ | 1 hr | Live installed capacity by sector |
| CEA Excel Report | cea.nic.in/.../Website.xlsx | 24 hr | National + state-wise all fuels |
| Yahoo Finance | yfinance library | 5 min | 14 NSE RE stocks live |
| RSS x7 | Mercom, PVTech, ET Energy, Saur, REGlobal, IEEFA, CleanTechnica | 5 min | Industry news + alerts |
| World Bank API | api.worldbank.org/v2/country/IN | 24 hr | India RE % of electricity |
| YouTube RSS | youtube.com/feeds/videos.xml | 10 min | Live channel video IDs |
| PM Surya Ghar | pmsuryaghar.gov.in | 1 hr | Rooftop solar stats (Playwright) |
| PM KUSUM | pmkusum.mnre.gov.in | 1 hr | Agricultural solar stats (Playwright) |

---

## Live Data at Time of Snapshot

| Metric | Value | Source |
|--------|-------|--------|
| Solar Installed | 154,236 MW (154.2 GW) | MNRE |
| Wind Installed | 56,437 MW | MNRE |
| Total RE | 279,255 MW | MNRE |
| Total Non-Fossil | 288,035 MW | MNRE |
| Total India Installed | 537,264 MW | CEA |
| 500 GW Target Progress | 55.8% | Calculated |
| Intelligence Alerts Active | 11 | RSS keyword scan |

---

## Dashboard Tabs

| Tab | Key Features |
|-----|-------------|
| **Overview** | 14 stock cards (NSE live), candlestick+SMA20, MNRE live capacity bars, commodities table |
| **Solar** | Live GW metrics from MNRE, solar leaders table, PM Surya Ghar, state-wise chart, 2030 projection |
| **BESS** | Deployment trajectory, 8-player table, tech mix bars, 2030 GWh projection |
| **Green H2** | NGHM mission KPIs, cost trajectory ($6->$1/kg), project pipeline, value chain |
| **Analytics** | Candlestick+Bollinger Bands, RSI/MACD/SMA indicators, 90-day polynomial projection, World Bank chart |
| **News & Policy** | Live RSS from 7 sources, policy milestone tracker, SECI tender tracker |
| **Global & Live TV** | 8 live TV channels with switching, global RE ETFs, investment chart, normalised benchmark |

---

## Alert System (Bell Icon, Top-Right)

Polls every 10 minutes. Scans all RSS articles for keyword matches across 7 categories.
New alerts show red badge with count. Slide-out drawer from right edge.

| Category | Trigger Keywords |
|----------|-----------------|
| SUPPLY CHAIN | polysilicon, supply chain, cell shortage, module price, wafer, backsheet, glass shortage |
| TRADE | tariff, anti-dumping, ALMM, BCD, AD/CVD, import duty, safeguard, trade war, customs |
| POLICY | PLI, VGF, SECI tender, MNRE notification, carbon credit, RPO, REC, budget allocation |
| BESS/GH2 | battery storage, BESS, green hydrogen, electrolyzer, GH2, hydrogen mission, NGHM |
| MARKET | L1 tariff, auction result, bid, capacity addition, MW commissioned, GW installed |
| COMPANIES | Waaree, Premier Energy, Adani Green, IREDA, NHPC, Suzlon, Tata Power, Saatvik |
| GLOBAL | China solar, US IRA, EU solar, IRENA report, BloombergNEF, polysilicon price |

---

## Live TV Channels

| # | Channel | YouTube Channel ID | Color Accent |
|---|---------|-------------------|-------------|
| 1 | WION | UCsB-sMFo8gznkLsNt5NU0mg | #b58900 (yellow) |
| 2 | ET Now | UCJim7HNvOmCJRLJnQJp0czw | #268bd2 (blue) |
| 3 | CNBC TV18 | UC7HExiGZiGPJqOfkfANczQA | #2aa198 (cyan) |
| 4 | India TV | UCE_Uy-xEpFiRLmpTEkxc-LA | #859900 (green) |
| 5 | Bloomberg | UCIALMKvObZNtJ6AmdCLP7Lg | #dc322f (red) |
| 6 | DD News | UCF2MmTp-Q6HlCJDjdHWF9Rw | #6c71c4 (violet) |
| 7 | NewsX | UCFZIZGhSwRSGF6Mn__cTjIA | #d33682 (magenta) |
| 8 | Al Jazeera | UCNye-wNBqNL5ZzHSJj3l8Bg | #cb4b16 (orange) |

---

## NSE Stock Universe (14 Stocks)

| Symbol | Company |
|--------|---------|
| ADANIGREEN.NS | Adani Green Energy |
| NHPC.NS | NHPC |
| NTPC.NS | NTPC |
| SUZLON.NS | Suzlon Energy |
| SWSOLAR.NS | Sterling & Wilson Solar |
| IREDA.NS | IREDA |
| SJVN.NS | SJVN |
| WAAREEENER.NS | Waaree Energies |
| PREMIENERG.NS | Premier Energies |
| TATAPOWER.NS | Tata Power |
| TORNTPOWER.NS | Torrent Power |
| INOXWIND.NS | Inox Wind |
| WEBSOL.NS | Websol Energy |
| BOROSIL.NS | Borosil Renewables |

---

## All API Endpoints

| Route | Cache | Description |
|-------|-------|-------------|
| GET / | — | Dashboard HTML |
| GET /api/dashboard | 5min | Quotes + news + commodities + alerts (single boot call) |
| GET /api/quotes | 5min | All 14 RE stock quotes |
| GET /api/history/<symbol> | 5min | 1Y OHLCV history for NSE symbol |
| GET /api/analysis/<symbol> | 5min | Technicals + 90d projection + 6M history |
| GET /api/mnre_live | 1hr | MNRE physical progress scraped live |
| GET /api/cea_capacity | 24hr | CEA national installed capacity breakdown |
| GET /api/statewise | 24hr | Top 10 states + Others RE capacity from CEA Excel |
| GET /api/alerts | 5min | Keyword-matched intelligence alerts from RSS |
| GET /api/news | 5min | Latest articles from 7 RSS feeds |
| GET /api/live_channels | static | TV channel list with YouTube IDs |
| GET /api/youtube_live/<id> | 10min | Latest video ID for channel (from YouTube RSS) |
| GET /api/commodities | 5min | Gold, Crude, Silver, NatGas, Aluminum |
| GET /api/global_re | 5min | ICLN, QCLN, NEE, ENPH, SEDG quotes |
| GET /api/worldbank | 24hr | India renewable % from World Bank API |
| GET /api/pm_surya_ghar | 1hr | Rooftop solar stats via Playwright browser |
| GET /api/pm_kusum | 1hr | PM KUSUM stats via Playwright browser |

---

## Solarized Dark Theme Palette

```
--bg:      #002b36   Page background
--bg2:     #073642   Panel / header background
--border:  #094554   All borders
--cyan:    #2aa198   Primary accent, titles
--green:   #859900   Positive values, BUY signal
--red:     #dc322f   Negative values, SELL signal
--yellow:  #b58900   Neutral, HOLD signal
--blue:    #268bd2   Info, secondary data
--violet:  #6c71c4   BESS / alternative
--orange:  #cb4b16   Warnings
--magenta: #d33682   Alerts / highlight
--base0:   #839496   Body text
--base01:  #586e75   Muted / labels
Font:      JetBrains Mono, Courier New, monospace
```

---

## Technical Notes

- CEA URL auto-detects from report page; fallback constructs from current YYYY/MM
- MNRE data updates monthly from govt website (last seen: 30.04.2026)
- PM Surya Ghar / KUSUM are JS-heavy; Playwright Chromium required (installed)
- YouTube live_stream embed works for most news channels; some may show unavailable
- All .nic.in / .gov.in govt sites use verify=False due to SSL cert chain issues
- Cache is in-memory dict; cleared on server restart
- threaded=True on Flask allows concurrent API calls during page load

---

## RESTORE FROM THIS FILE

**If any edit breaks Neuron, restore in 3 steps:**

1. Copy the `neuron.py` code block below -> paste into `neuron.py`
2. Copy the `index.html` code block below -> paste into `templates/index.html`
3. Run: `python neuron.py` then open `http://localhost:5000`

**No database. No config files. No environment variables needed.**

---

## FULL SOURCE CODE — neuron.py

```python
"""
Neuron v2 - Indian RE Industry Intelligence Monitor
by Vipul Jakhar
"""
import json, time, re, os, io
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template
import yfinance as yf
import requests
import feedparser
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
cache = {}
CACHE_TTL = 300

RE_STOCKS = {
    "ADANIGREEN.NS":"Adani Green","NHPC.NS":"NHPC","NTPC.NS":"NTPC",
    "SUZLON.NS":"Suzlon","SWSOLAR.NS":"Sterling Wilson","IREDA.NS":"IREDA",
    "SJVN.NS":"SJVN","WAAREEENER.NS":"Waaree","PREMIENERG.NS":"Premier Energy",
    "TATAPOWER.NS":"Tata Power","TORNTPOWER.NS":"Torrent Power",
    "INOXWIND.NS":"Inox Wind","WEBSOL.NS":"Websol Energy","BOROSIL.NS":"Borosil Renewables",
}

RSS_FEEDS = [
    ("Mercom India","https://mercomindia.com/feed/"),
    ("PV Tech","https://www.pv-tech.org/feed/"),
    ("ET Energy","https://economictimes.indiatimes.com/industry/energy/power/rssfeeds/13358393.cms"),
    ("Saur Energy","https://www.saurenergy.com/feed"),
    ("REGlobal","https://reglobal.co/feed/"),
    ("IEEFA India","https://ieefa.org/feed/"),
    ("CleanTechnica","https://cleantechnica.com/feed/"),
]
COMMODITIES = {"GC=F":"Gold","CL=F":"Crude Oil","SI=F":"Silver","NG=F":"Natural Gas","ALI=F":"Aluminum"}
GLOBAL_RE   = {"ICLN":"iShares Global CE","QCLN":"First Trust NASDAQ CE","NEE":"NextEra Energy","ENPH":"Enphase Energy","SEDG":"SolarEdge"}

ALERT_KEYWORDS = {
    "SUPPLY CHAIN":["polysilicon","supply chain","cell shortage","module price","wafer","backsheet","glass shortage"],
    "TRADE":       ["tariff","anti-dumping","ALMM","BCD","AD/CVD","import duty","safeguard","trade war","customs"],
    "POLICY":      ["PLI","VGF","SECI tender","MNRE notification","carbon credit","RPO","REC","budget allocation"],
    "BESS/GH2":    ["battery storage","BESS","green hydrogen","electrolyzer","GH2","hydrogen mission","NGHM","pumped hydro"],
    "MARKET":      ["L1 tariff","auction result","bid","capacity addition","MW commissioned","GW installed","solar auction"],
    "COMPANIES":   ["Waaree","Premier Energy","Adani Green","IREDA","NHPC","Suzlon","Tata Power","Saatvik","Vikram Solar"],
    "GLOBAL":      ["China solar","US IRA","EU solar","IRENA report","BloombergNEF","polysilicon price","panel oversupply"],
}
SEEN_ALERTS = set()

LIVE_CHANNELS = [
    {"name":"WION",       "id":"UCsB-sMFo8gznkLsNt5NU0mg","color":"#b58900"},
    {"name":"ET Now",     "id":"UCJim7HNvOmCJRLJnQJp0czw","color":"#268bd2"},
    {"name":"CNBC TV18",  "id":"UC7HExiGZiGPJqOfkfANczQA","color":"#2aa198"},
    {"name":"India TV",   "id":"UCE_Uy-xEpFiRLmpTEkxc-LA","color":"#859900"},
    {"name":"Bloomberg",  "id":"UCIALMKvObZNtJ6AmdCLP7Lg","color":"#dc322f"},
    {"name":"DD News",    "id":"UCF2MmTp-Q6HlCJDjdHWF9Rw","color":"#6c71c4"},
    {"name":"NewsX",      "id":"UCFZIZGhSwRSGF6Mn__cTjIA","color":"#d33682"},
    {"name":"Al Jazeera", "id":"UCNye-wNBqNL5ZzHSJj3l8Bg","color":"#cb4b16"},
]

def get_cache(key, ttl=None):
    e = cache.get(key)
    if e and time.time()-e["ts"] < (ttl or CACHE_TTL): return e["data"]
    return None

def set_cache(key, data):
    cache[key] = {"data":data,"ts":time.time()}

def fetch_quote(symbol):
    try:
        t=yf.Ticker(symbol); hist=t.history(period="5d")
        if hist.empty: return None
        close=float(hist["Close"].iloc[-1]); prev=float(hist["Close"].iloc[-2]) if len(hist)>1 else close
        chg=close-prev; chgp=(chg/prev*100) if prev else 0
        return {"symbol":symbol,"name":RE_STOCKS.get(symbol,symbol),"price":round(close,2),
                "change":round(chg,2),"change_pct":round(chgp,2),"volume":int(hist["Volume"].iloc[-1]),
                "high":round(float(hist["High"].iloc[-1]),2),"low":round(float(hist["Low"].iloc[-1]),2),
                "mktcap":getattr(t.fast_info,"market_cap",None)}
    except: return None

def fetch_history(symbol, period="1y"):
    try:
        t=yf.Ticker(symbol); hist=t.history(period=period)
        return [{"date":str(d.date()),"open":round(float(r.Open),2),"high":round(float(r.High),2),
                 "low":round(float(r.Low),2),"close":round(float(r.Close),2),"volume":int(r.Volume)}
                for d,r in hist.iterrows()]
    except: return []

def fetch_all_quotes():
    cached=get_cache("all_quotes")
    if cached: return cached
    results={}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs={ex.submit(fetch_quote,s):s for s in RE_STOCKS}
        for f in as_completed(futs):
            d=f.result()
            if d: results[futs[f]]=d
    set_cache("all_quotes",results); return results

def fetch_quote_generic(symbol, name):
    try:
        t=yf.Ticker(symbol); hist=t.history(period="2d")
        if hist.empty: return None
        close=float(hist["Close"].iloc[-1]); prev=float(hist["Close"].iloc[-2]) if len(hist)>1 else close
        chg=close-prev
        return {"symbol":symbol,"name":name,"price":round(close,2),"change":round(chg,2),
                "change_pct":round((chg/prev*100) if prev else 0,2)}
    except: return None

def fetch_commodities():
    cached=get_cache("commodities")
    if cached: return cached
    results={}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs={ex.submit(fetch_quote_generic,s,n):s for s,n in COMMODITIES.items()}
        for f in as_completed(futs):
            d=f.result()
            if d: results[futs[f]]=d
    set_cache("commodities",results); return results

def fetch_global_re():
    cached=get_cache("global_re")
    if cached: return cached
    results={}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs={ex.submit(fetch_quote_generic,s,n):s for s,n in GLOBAL_RE.items()}
        for f in as_completed(futs):
            d=f.result()
            if d: results[futs[f]]=d
    set_cache("global_re",results); return results

def fetch_mnre_live():
    cached=get_cache("mnre_live",3600)
    if cached: return cached
    try:
        hdr={"User-Agent":"Mozilla/5.0 Chrome/124 Safari/537.36"}
        r=requests.get("https://mnre.gov.in/en/physical-progress/",headers=hdr,timeout=20,verify=False)
        soup=BeautifulSoup(r.text,"html.parser")
        table=soup.find("table")
        if not table: return {}
        rows=table.find_all("tr")
        header=[c.get_text(strip=True) for c in rows[0].find_all(["th","td"])]
        data={}
        for row in rows[2:]:
            cells=[c.get_text(strip=True) for c in row.find_all(["td","th"])]
            if len(cells)>=4 and cells[0] and cells[3]:
                try: data[cells[0]]={"monthly_mw":float(cells[1].replace(",","")) if cells[1] else 0,
                                     "cumulative_mw":float(cells[3].replace(",","")) if cells[3] else 0}
                except: pass
        result={"data":data,"as_on":header[3] if len(header)>3 else "",
                "fetched_at":datetime.now().strftime("%Y-%m-%d %H:%M")}
        set_cache("mnre_live",result); return result
    except Exception as e: return {"error":str(e)}

def _cea_url():
    try:
        hdr={"User-Agent":"Mozilla/5.0 Chrome/124 Safari/537.36"}
        r=requests.get("https://cea.nic.in/installed-capacity-report/?lang=en",headers=hdr,timeout=15,verify=False)
        soup=BeautifulSoup(r.text,"html.parser")
        for a in soup.find_all("a",href=True):
            if ".xlsx" in a["href"].lower() and "installed" in a["href"].lower():
                return a["href"]
    except: pass
    n=datetime.now()
    return f"https://cea.nic.in/wp-content/uploads/installed/{n.year}/{n.month:02d}/Website.xlsx"

def fetch_cea_capacity():
    cached=get_cache("cea_cap",86400)
    if cached: return cached
    try:
        hdr={"User-Agent":"Mozilla/5.0 Chrome/124 Safari/537.36"}
        url=_cea_url()
        r=requests.get(url,headers=hdr,timeout=20,verify=False)
        if r.status_code!=200: return {}
        df=pd.read_excel(io.BytesIO(r.content),sheet_name="Summary",header=None)
        result={"source_url":url,"fetched_at":datetime.now().strftime("%Y-%m-%d")}
        for _,row in df.iterrows():
            # Structure: NaN NaN [Category?] [Label] [MW] [Pct]
            non_null=[v for v in row.values if pd.notna(v)]
            if len(non_null)>=2:
                try:
                    # Last str is label, first float is MW, second float is pct
                    strs=[str(v).strip() for v in non_null if isinstance(v,str) and str(v).strip()]
                    nums=[float(v) for v in non_null if isinstance(v,(int,float)) and not isinstance(v,bool)]
                    if strs and len(nums)>=2:
                        label=strs[-1]
                        mw=nums[0]; pct=nums[1]
                        if mw>100: result[label]={"mw":round(mw,2),"pct":round(pct*100,2)}
                except: pass
        set_cache("cea_cap",result); return result
    except Exception as e: return {"error":str(e)}

def fetch_statewise():
    cached=get_cache("statewise",86400)
    if cached: return cached
    try:
        hdr={"User-Agent":"Mozilla/5.0 Chrome/124 Safari/537.36"}
        url=_cea_url()
        r=requests.get(url,headers=hdr,timeout=20,verify=False)
        df=pd.read_excel(io.BytesIO(r.content),sheet_name="IC",header=None)
        STATES={"Rajasthan","Gujarat","Karnataka","Tamil Nadu","Andhra Pradesh",
                "Maharashtra","Madhya Pradesh","Telangana","Uttar Pradesh","Bihar",
                "Punjab","Haryana","Kerala","Odisha","West Bengal","Jharkhand",
                "Himachal Pradesh","Uttarakhand","Assam","Chhattisgarh","Goa"}
        sd={}
        for _,row in df.iterrows():
            name=str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            if name in STATES:
                try:
                    res=float(row.iloc[10]) if pd.notna(row.iloc[10]) else 0
                    tot=float(row.iloc[12]) if pd.notna(row.iloc[12]) else 0
                    if name in sd: sd[name]["res_mw"]+=res; sd[name]["total_mw"]+=tot
                    else: sd[name]={"res_mw":round(res,2),"total_mw":round(tot,2)}
                except: pass
        srt=sorted(sd.items(),key=lambda x:x[1]["res_mw"],reverse=True)
        top={k:v for k,v in srt[:10]}
        others=sum(v["res_mw"] for _,v in srt[10:])
        if others>0: top["Others"]={"res_mw":round(others,2),"total_mw":0}
        result={"states":top,"as_on":datetime.now().strftime("%B %Y")}
        set_cache("statewise",result); return result
    except Exception as e: return {"error":str(e),"states":{}}

def fetch_pm_surya_ghar():
    cached=get_cache("surya_ghar",3600)
    if cached: return cached
    try:
        from scrapling.fetchers import StealthyFetcher
        page=StealthyFetcher.fetch("https://pmsuryaghar.gov.in/",headless=True,network_idle=True,timeout=30000,disable_resources=True)
        text=page.get_text()
        nums=re.findall(r"([\d,]+)\s*(?:applications?|connections?|rooftop|beneficiar\w*|install\w*)",text,re.I)
        counters={}
        for el in page.css(".counter,.count,[class*=number],[class*=stat]"):
            t2=el.get_text(strip=True)
            if re.search(r"\d",t2): counters[len(counters)]=t2[:80]
        result={"nums":nums[:10],"counters":counters,"fetched_at":datetime.now().strftime("%Y-%m-%d %H:%M")}
        set_cache("surya_ghar",result); return result
    except Exception as e: return {"error":str(e),"note":"Playwright required - run: playwright install chromium"}

def fetch_pm_kusum():
    cached=get_cache("pm_kusum",3600)
    if cached: return cached
    try:
        from scrapling.fetchers import StealthyFetcher
        page=StealthyFetcher.fetch("https://pmkusum.mnre.gov.in/landing.html",headless=True,network_idle=True,timeout=30000,disable_resources=True)
        text=page.get_text()
        nums=re.findall(r"([\d,\.]+)\s*(MW|GW|pumps?|Lakh|crore|beneficiar\w*)",text,re.I)
        comps={}
        for el in page.css("[class*=component],[class*=stat],[class*=count],h3,h4"):
            t2=el.get_text(strip=True)
            if re.search(r"\d",t2) and len(t2)<150: comps[len(comps)]=t2
        result={"nums":nums[:15],"components":comps,"fetched_at":datetime.now().strftime("%Y-%m-%d %H:%M")}
        set_cache("pm_kusum",result); return result
    except Exception as e: return {"error":str(e),"note":"Playwright required - run: playwright install chromium"}

def fetch_news():
    cached=get_cache("news")
    if cached: return cached
    articles=[]
    for source,url in RSS_FEEDS:
        try:
            feed=feedparser.parse(url)
            for e in feed.entries[:6]:
                articles.append({"source":source,"title":e.get("title",""),"link":e.get("link",""),
                                  "date":e.get("published",""),"summary":(e.get("summary","") or "")[:250]})
        except: pass
    articles.sort(key=lambda x:x["date"],reverse=True)
    set_cache("news",articles); return articles

def get_alerts():
    articles=fetch_news(); alerts=[]
    for a in articles:
        text=(a["title"]+" "+a["summary"]).lower()
        for cat,kws in ALERT_KEYWORDS.items():
            matched=[kw for kw in kws if kw.lower() in text]
            if matched:
                uid=a["link"]+cat; is_new=uid not in SEEN_ALERTS
                SEEN_ALERTS.add(uid)
                alerts.append({**a,"category":cat,"keywords":matched,"is_new":is_new}); break
    return alerts

def get_youtube_live(channel_id):
    cached=get_cache(f"yt_{channel_id}",600)
    if cached: return cached
    try:
        import xml.etree.ElementTree as ET
        r=requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",timeout=10)
        ns={"yt":"http://www.youtube.com/xml/schemas/2015","atom":"http://www.w3.org/2005/Atom"}
        root=ET.fromstring(r.text)
        entries=root.findall("atom:entry",ns)
        if entries:
            vid=entries[0].find("yt:videoId",ns); title=entries[0].find("atom:title",ns)
            result={"video_id":vid.text if vid is not None else "","title":title.text if title is not None else ""}
            set_cache(f"yt_{channel_id}",result); return result
    except: pass
    return {"video_id":"","title":""}

def india_energy_worldbank():
    cached=get_cache("wb_energy",86400)
    if cached: return cached
    try:
        r=requests.get("https://api.worldbank.org/v2/country/IN/indicator/EG.ELC.RNEW.ZS?format=json&mrv=12",timeout=15)
        data=r.json()
        series=[{"year":d["date"],"value":d["value"]} for d in data[1] if d["value"]]
        set_cache("wb_energy",series); return series
    except: return []

def compute_projection(prices,days=90):
    if len(prices)<30: return []
    y=np.array([p["close"] for p in prices[-90:]]); x=np.arange(len(y))
    coeffs=np.polyfit(x,y,2); fx=np.arange(len(y),len(y)+days); fy=np.polyval(coeffs,fx)
    last=datetime.strptime(prices[-1]["date"],"%Y-%m-%d")
    return [{"date":(last+timedelta(days=i+1)).strftime("%Y-%m-%d"),"projected":round(float(v),2)} for i,v in enumerate(fy)]

def compute_technicals(prices):
    if len(prices)<26: return {}
    closes=np.array([p["close"] for p in prices])
    delta=np.diff(closes); gain=np.where(delta>0,delta,0); loss=np.where(delta<0,-delta,0)
    avg_g=np.mean(gain[-14:]); avg_l=np.mean(loss[-14:])
    rsi=100-(100/(1+avg_g/avg_l)) if avg_l else 100
    ema12=float(np.mean(closes[-12:])); ema26=float(np.mean(closes[-26:]))
    macd=ema12-ema26; sig=float(np.mean(closes[-9:])-np.mean(closes[-18:]))
    sma20=float(np.mean(closes[-20:])); std20=float(np.std(closes[-20:]))
    return {"rsi":round(float(rsi),2),"macd":round(macd,2),"macd_signal":round(sig,2),
            "bb_upper":round(sma20+2*std20,2),"bb_lower":round(sma20-2*std20,2),"bb_mid":round(sma20,2),
            "sma20":round(sma20,2),"sma50":round(float(np.mean(closes[-50:])),2) if len(closes)>=50 else None}

@app.route("/")
def index(): return render_template("index.html")
@app.route("/api/quotes")
def api_quotes(): return jsonify(fetch_all_quotes())
@app.route("/api/news")
def api_news(): return jsonify(fetch_news())
@app.route("/api/commodities")
def api_commodities(): return jsonify(fetch_commodities())
@app.route("/api/global_re")
def api_global_re(): return jsonify(fetch_global_re())
@app.route("/api/mnre_live")
def api_mnre_live(): return jsonify(fetch_mnre_live())
@app.route("/api/cea_capacity")
def api_cea_capacity(): return jsonify(fetch_cea_capacity())
@app.route("/api/statewise")
def api_statewise(): return jsonify(fetch_statewise())
@app.route("/api/pm_surya_ghar")
def api_pm_surya_ghar(): return jsonify(fetch_pm_surya_ghar())
@app.route("/api/pm_kusum")
def api_pm_kusum(): return jsonify(fetch_pm_kusum())
@app.route("/api/alerts")
def api_alerts(): return jsonify(get_alerts())
@app.route("/api/live_channels")
def api_live_channels(): return jsonify(LIVE_CHANNELS)
@app.route("/api/youtube_live/<channel_id>")
def api_youtube_live(channel_id):
    return jsonify(get_youtube_live(re.sub(r"[^A-Za-z0-9_-]","",channel_id)))
@app.route("/api/worldbank")
def api_worldbank(): return jsonify({"renewable_pct":india_energy_worldbank()})
@app.route("/api/history/<symbol>")
def api_history(symbol):
    sym=symbol+".NS" if "." not in symbol else symbol
    cached=get_cache(f"hist_{sym}")
    if cached: return jsonify(cached)
    data=fetch_history(sym); set_cache(f"hist_{sym}",data); return jsonify(data)
@app.route("/api/analysis/<symbol>")
def api_analysis(symbol):
    sym=symbol+".NS" if "." not in symbol else symbol
    prices=fetch_history(sym,"2y")
    return jsonify({"symbol":sym,"technicals":compute_technicals(prices),
                    "projection":compute_projection(prices),"history":prices[-180:]})
@app.route("/api/dashboard")
def api_dashboard():
    return jsonify({"quotes":fetch_all_quotes(),"news":fetch_news()[:15],
                    "commodities":fetch_commodities(),"global_re":fetch_global_re(),
                    "alerts":get_alerts()[:10]})

if __name__ == "__main__":
    print("  NEURON v2 - Indian RE Intelligence Monitor")
    print("  by Vipul Jakhar")
    print("  -> http://localhost:5000")
    app.run(debug=False, port=5000, threaded=True)
```

---

## FULL SOURCE CODE — templates/index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>NEURON v2 — Indian RE Monitor</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
:root{
  --bg:#002b36;--bg2:#073642;--border:#094554;
  --base01:#586e75;--base0:#839496;--base1:#93a1a1;
  --yellow:#b58900;--orange:#cb4b16;--red:#dc322f;
  --magenta:#d33682;--violet:#6c71c4;--blue:#268bd2;
  --cyan:#2aa198;--green:#859900;
  --font:'JetBrains Mono','Courier New',monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--base0);font-family:var(--font);font-size:13px;overflow-x:hidden}
/* Header */
#header{background:var(--bg2);border-bottom:1px solid var(--border);padding:10px 20px;
  display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:200}
.brand-name{font-size:22px;font-weight:700;letter-spacing:4px;color:var(--cyan);text-shadow:0 0 20px #2aa19844}
.brand-sub{font-size:10px;color:var(--base01);letter-spacing:2px}
.header-right{display:flex;gap:16px;align-items:center}
#clock{color:var(--cyan);font-size:15px;letter-spacing:2px}
#market-status{padding:3px 10px;border-radius:2px;font-size:10px;letter-spacing:1px}
.status-open{background:#85990022;color:var(--green);border:1px solid #85990044}
.status-closed{background:#dc322f22;color:var(--red);border:1px solid #dc322f44}
/* Alert Bell */
#alert-btn{position:relative;cursor:pointer;padding:5px 10px;background:var(--bg);
  border:1px solid var(--border);border-radius:3px;font-size:14px;color:var(--base0);
  transition:border-color .2s}
#alert-btn:hover{border-color:var(--yellow)}
#alert-badge{position:absolute;top:-4px;right:-4px;background:var(--red);color:#fff;
  font-size:9px;width:16px;height:16px;border-radius:50%;display:none;align-items:center;
  justify-content:center;font-weight:700;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.2)}}
/* Alert Drawer */
#alert-drawer{position:fixed;top:0;right:-420px;width:420px;height:100vh;background:var(--bg2);
  border-left:1px solid var(--border);z-index:500;transition:right .3s ease;overflow-y:auto;
  box-shadow:-8px 0 30px #00000088}
#alert-drawer.open{right:0}
.drawer-header{padding:16px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.drawer-title{color:var(--cyan);font-size:12px;letter-spacing:2px;text-transform:uppercase}
#drawer-close{cursor:pointer;color:var(--base01);font-size:18px;padding:4px 8px}
#drawer-close:hover{color:var(--red)}
.alert-item{padding:12px 16px;border-bottom:1px solid var(--border)44;transition:background .15s}
.alert-item:hover{background:var(--bg)}
.alert-item.new-alert{border-left:3px solid var(--yellow)}
.alert-cat{font-size:9px;letter-spacing:1px;text-transform:uppercase;padding:1px 6px;border-radius:2px;display:inline-block;margin-bottom:6px}
.cat-supply{background:#b5890022;color:var(--yellow);border:1px solid #b5890044}
.cat-trade{background:#dc322f22;color:var(--red);border:1px solid #dc322f44}
.cat-policy{background:#268bd222;color:var(--blue);border:1px solid #268bd244}
.cat-bess{background:#6c71c422;color:var(--violet);border:1px solid #6c71c444}
.cat-market{background:#85990022;color:var(--green);border:1px solid #85990044}
.cat-companies{background:#2aa19822;color:var(--cyan);border:1px solid #2aa19844}
.cat-global{background:#d3368222;color:var(--magenta);border:1px solid #d3368244}
.alert-title{font-size:12px;color:var(--base1);margin-bottom:4px}
.alert-title a{color:var(--base1);text-decoration:none}
.alert-title a:hover{color:var(--cyan)}
.alert-source{font-size:10px;color:var(--base01)}
.alert-kw{font-size:9px;color:var(--orange);margin-top:4px}
/* Ticker */
#ticker-wrap{background:var(--bg2);border-bottom:1px solid var(--border);overflow:hidden;height:28px;position:relative}
#ticker{display:flex;gap:40px;white-space:nowrap;animation:scroll 80s linear infinite;padding:6px 0;position:absolute}
@keyframes scroll{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.tick-up{color:var(--green)}.tick-dn{color:var(--red)}.tick-name{color:var(--base01);margin-right:6px}
/* Tabs */
#tabs{background:var(--bg2);border-bottom:1px solid var(--border);display:flex;padding:0 20px;overflow-x:auto}
.tab{padding:10px 18px;cursor:pointer;font-size:11px;letter-spacing:1px;color:var(--base01);
  border-bottom:2px solid transparent;transition:all .2s;text-transform:uppercase;white-space:nowrap}
.tab:hover{color:var(--base1)}.tab.active{color:var(--cyan);border-bottom-color:var(--cyan)}
/* Layout */
#app{padding:16px}
.panel{background:var(--bg2);border:1px solid var(--border);border-radius:3px;margin-bottom:14px}
.panel-header{padding:10px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.panel-title{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--cyan);font-weight:700}
.panel-body{padding:14px 16px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
/* Stock Cards */
.stock-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:10px}
.stock-card{background:var(--bg);border:1px solid var(--border);border-radius:3px;padding:12px;
  cursor:pointer;transition:border-color .2s}
.stock-card:hover,.stock-card.selected{border-color:var(--cyan);box-shadow:0 0 8px #2aa19833}
.sc-name{font-size:10px;color:var(--base01);margin-bottom:4px}
.sc-price{font-size:18px;color:var(--base1);font-weight:700}
.sc-change{font-size:11px;margin-top:2px}.sc-vol{font-size:10px;color:var(--base01);margin-top:4px}
.up{color:var(--green)}.dn{color:var(--red)}.neu{color:var(--yellow)}
/* Tables */
table{width:100%;border-collapse:collapse}
th{text-align:left;padding:8px 10px;font-size:10px;letter-spacing:1px;text-transform:uppercase;
  color:var(--base01);border-bottom:1px solid var(--border)}
td{padding:8px 10px;border-bottom:1px solid #09455488;font-size:12px}
tr:last-child td{border-bottom:none}
tr:hover td{background:#00000022}
/* Metrics */
.metric-card{background:var(--bg);border:1px solid var(--border);border-radius:3px;padding:14px}
.metric-label{font-size:10px;color:var(--base01);letter-spacing:1px;text-transform:uppercase}
.metric-value{font-size:22px;color:var(--base1);font-weight:700;margin-top:4px}
.metric-sub{font-size:11px;color:var(--base01);margin-top:2px}
.metric-live{font-size:9px;color:var(--green);letter-spacing:1px}
/* Bars */
.bar-row{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.bar-label{width:130px;font-size:11px;color:var(--base1);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-track{flex:1;height:6px;background:var(--bg);border-radius:3px}
.bar-fill{height:100%;border-radius:3px;background:var(--cyan);transition:width .8s ease}
.bar-val{width:60px;text-align:right;font-size:11px;color:var(--base01)}
/* News */
.news-item{padding:10px 0;border-bottom:1px solid #09455466}
.news-item:last-child{border-bottom:none}
.news-source{font-size:10px;color:var(--cyan);letter-spacing:1px}
.news-title{font-size:12px;color:var(--base1);margin:4px 0}
.news-title a{color:var(--base1);text-decoration:none}
.news-title a:hover{color:var(--cyan)}
.news-date{font-size:10px;color:var(--base01)}
.news-summary{font-size:11px;color:var(--base0);margin-top:4px;line-height:1.5}
/* Tech cards */
.tech-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px}
.tech-card{background:var(--bg);border:1px solid var(--border);border-radius:3px;padding:10px;text-align:center}
.tech-label{font-size:10px;color:var(--base01)}
.tech-value{font-size:15px;font-weight:700;margin-top:3px}
/* Signal */
.signal{display:inline-block;padding:2px 8px;border-radius:2px;font-size:10px;letter-spacing:1px;text-transform:uppercase}
.signal-buy{background:#85990022;color:var(--green);border:1px solid #85990044}
.signal-sell{background:#dc322f22;color:var(--red);border:1px solid #dc322f44}
.signal-hold{background:#b5890022;color:var(--yellow);border:1px solid #b5890044}
/* Live TV Panel */
#live-tv-panel{background:var(--bg);border:1px solid var(--border);border-radius:3px}
.channel-switcher{display:flex;flex-wrap:wrap;gap:8px;padding:12px 16px;border-bottom:1px solid var(--border)}
.ch-btn{padding:6px 14px;border-radius:3px;cursor:pointer;font-size:11px;font-family:var(--font);
  letter-spacing:1px;border:1px solid var(--border);background:var(--bg2);color:var(--base0);
  transition:all .15s}
.ch-btn:hover{color:var(--base1);border-color:var(--base01)}
.ch-btn.active{font-weight:700;border-color:currentColor}
#tv-frame-wrap{position:relative;padding-top:56.25%}
#tv-frame{position:absolute;top:0;left:0;width:100%;height:100%;border:none;background:#000}
.tv-title{padding:8px 16px;font-size:10px;color:var(--base01);border-top:1px solid var(--border);
  display:flex;justify-content:space-between;align-items:center}
/* Tabs */
.tab-content{display:none}
.tab-content.active{display:block}
/* Scrollbar */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border)}
/* Loader */
.loader{text-align:center;padding:30px;color:var(--base01);letter-spacing:2px}
/* MNRE live indicator */
.live-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);
  animation:blink 1.5s infinite;margin-right:5px}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
</style>
</head>
<body>

<!-- Floating Alert Drawer -->
<div id="alert-drawer">
  <div class="drawer-header">
    <span class="drawer-title">Intelligence Alerts</span>
    <span id="drawer-close" onclick="closeDrawer()">✕</span>
  </div>
  <div id="drawer-body"><div class="loader">Loading…</div></div>
</div>
<div id="drawer-overlay" onclick="closeDrawer()" style="display:none;position:fixed;inset:0;background:#00000066;z-index:499"></div>

<!-- Header -->
<div id="header">
  <div>
    <div class="brand-name">NEURON</div>
    <div class="brand-sub">INDIAN RE INTELLIGENCE · by Vipul Jakhar · v2</div>
  </div>
  <div class="header-right">
    <div id="alert-btn" onclick="toggleDrawer()">
      🔔
      <div id="alert-badge"></div>
    </div>
    <div id="market-status" class="status-closed">CLOSED</div>
    <div id="clock">--:--:--</div>
  </div>
</div>

<!-- Ticker -->
<div id="ticker-wrap">
  <div id="ticker"><span style="color:var(--base01);padding:6px 0">Loading live quotes…</span></div>
</div>

<!-- Tabs -->
<div id="tabs">
  <div class="tab active"  onclick="switchTab('overview')">Overview</div>
  <div class="tab" onclick="switchTab('solar')">Solar</div>
  <div class="tab" onclick="switchTab('bess')">BESS</div>
  <div class="tab" onclick="switchTab('gh2')">Green H₂</div>
  <div class="tab" onclick="switchTab('analytics')">Analytics</div>
  <div class="tab" onclick="switchTab('news')">News & Policy</div>
  <div class="tab" onclick="switchTab('global')">Global & Live TV</div>
</div>

<div id="app">

<!-- ══════════ OVERVIEW ══════════ -->
<div id="tab-overview" class="tab-content active">
  <div class="grid2">
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header">
        <span class="panel-title">Indian RE Equities — NSE Live</span>
        <span style="font-size:10px;color:var(--base01)">Click stock to analyse ↓</span>
      </div>
      <div class="panel-body">
        <div id="stock-grid" class="stock-grid"><div class="loader">Fetching live data…</div></div>
      </div>
    </div>

    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header">
        <span class="panel-title" id="chart-title">Price Chart</span>
        <div style="display:flex;gap:10px;align-items:center">
          <span id="chart-signal"></span>
          <select id="period-sel" onchange="loadChart()" style="background:var(--bg);color:var(--base0);border:1px solid var(--border);padding:3px 8px;font-size:11px;font-family:var(--font)">
            <option value="3mo">3M</option><option value="6mo">6M</option>
            <option value="1y" selected>1Y</option><option value="2y">2Y</option><option value="5y">5Y</option>
          </select>
        </div>
      </div>
      <div class="panel-body">
        <div id="price-chart" style="height:320px"></div>
        <div class="tech-grid" id="tech-cards" style="margin-top:12px"></div>
      </div>
    </div>

    <!-- MNRE Live Capacity -->
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title"><span class="live-dot"></span>MNRE Live Capacity</span>
        <span id="mnre-as-on" style="font-size:10px;color:var(--base01)"></span>
      </div>
      <div class="panel-body" id="mnre-bars"><div class="loader">Fetching MNRE…</div></div>
    </div>

    <!-- Commodities -->
    <div class="panel">
      <div class="panel-header"><span class="panel-title">Commodities</span></div>
      <div class="panel-body">
        <table id="comm-table"><tr><td class="loader">Loading…</td></tr></table>
      </div>
    </div>
  </div>
</div>

<!-- ══════════ SOLAR ══════════ -->
<div id="tab-solar" class="tab-content">
  <div class="grid2">
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header"><span class="panel-title"><span class="live-dot"></span>India Solar — Live Intelligence</span></div>
      <div class="panel-body">
        <div class="grid4" id="solar-metrics" style="margin-bottom:16px">
          <div class="metric-card">
            <div class="metric-label">Solar Installed</div>
            <div class="metric-value" id="solar-mw" style="color:var(--yellow)">—</div>
            <div class="metric-sub metric-live" id="solar-src">Loading MNRE…</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">2030 Solar Target</div>
            <div class="metric-value" style="color:var(--cyan)">280 GW</div>
            <div class="metric-sub">MNRE target</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Monthly Addition</div>
            <div class="metric-value" id="solar-monthly" style="color:var(--green)">—</div>
            <div class="metric-sub">Current FY pace</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Solar LCOE India</div>
            <div class="metric-value" style="color:var(--blue)">₹2.1/u</div>
            <div class="metric-sub">avg tariff trend</div>
          </div>
        </div>
        <div id="solar-history-chart" style="height:280px"></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header"><span class="panel-title">Solar Leaders</span></div>
      <div class="panel-body">
        <table id="solar-leaders"><tr><td class="loader">Loading…</td></tr></table>
      </div>
    </div>

    <!-- PM Surya Ghar -->
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">PM Surya Ghar — Rooftop</span>
        <span id="surya-fetch-btn" onclick="loadSuryaGhar()" style="cursor:pointer;font-size:10px;color:var(--cyan)">▶ Fetch Live</span>
      </div>
      <div class="panel-body" id="surya-body">
        <div class="metric-card" style="margin-bottom:10px">
          <div class="metric-label">Scheme Target</div>
          <div class="metric-value" style="color:var(--cyan)">1 Cr Homes</div>
          <div class="metric-sub">3 kW average per household</div>
        </div>
        <div id="surya-live" style="color:var(--base01);font-size:11px">Click "Fetch Live" to pull real-time PM Surya Ghar data via browser automation.</div>
      </div>
    </div>

    <!-- State-wise chart -->
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header">
        <span class="panel-title"><span class="live-dot"></span>State-wise RE Capacity (CEA) — Top 10 + Others</span>
        <span id="statewise-as-on" style="font-size:10px;color:var(--base01)"></span>
      </div>
      <div class="panel-body">
        <div id="statewise-chart" style="height:300px"></div>
      </div>
    </div>

    <!-- Projection -->
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header"><span class="panel-title">Solar Capacity Projection to 2030 (GW)</span></div>
      <div class="panel-body"><div id="solar-proj-chart" style="height:260px"></div></div>
    </div>

    <!-- PM KUSUM -->
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header">
        <span class="panel-title">PM KUSUM — Agricultural Solar</span>
        <span onclick="loadPmKusum()" style="cursor:pointer;font-size:10px;color:var(--cyan)">▶ Fetch Live</span>
      </div>
      <div class="panel-body">
        <div class="grid4" style="margin-bottom:14px">
          <div class="metric-card"><div class="metric-label">Component A</div><div class="metric-value" style="color:var(--yellow)">10 GW</div><div class="metric-sub">Ground-mounted solar (Farmers land)</div></div>
          <div class="metric-card"><div class="metric-label">Component B</div><div class="metric-value" style="color:var(--cyan)">2 M Pumps</div><div class="metric-sub">Standalone solar pumps</div></div>
          <div class="metric-card"><div class="metric-label">Component C</div><div class="metric-value" style="color:var(--green)">1.5 M Pumps</div><div class="metric-sub">Grid-connected solar pumps</div></div>
          <div class="metric-card"><div class="metric-label">Total Budget</div><div class="metric-value" style="color:var(--blue)">₹34,422 Cr</div><div class="metric-sub">Central financial assistance</div></div>
        </div>
        <div id="kusum-live" style="color:var(--base01);font-size:11px">Click "Fetch Live" to pull real-time PM KUSUM data via browser automation.</div>
      </div>
    </div>
  </div>
</div>

<!-- ══════════ BESS ══════════ -->
<div id="tab-bess" class="tab-content">
  <div class="grid2">
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header"><span class="panel-title">BESS — Battery Energy Storage Systems India</span></div>
      <div class="panel-body">
        <div class="grid4" style="margin-bottom:16px">
          <div class="metric-card"><div class="metric-label">Installed BESS</div><div class="metric-value" style="color:var(--orange)">~4 GWh</div><div class="metric-sub">operational 2024</div></div>
          <div class="metric-card"><div class="metric-label">2030 BESS Target</div><div class="metric-value" style="color:var(--cyan)">47 GWh</div><div class="metric-sub">NTPC + private</div></div>
          <div class="metric-card"><div class="metric-label">VGF Approved</div><div class="metric-value" style="color:var(--green)">₹3,760 Cr</div><div class="metric-sub">4,000 MWh tranche</div></div>
          <div class="metric-card"><div class="metric-label">LFP Cell Cost</div><div class="metric-value" style="color:var(--blue)">~$55/kWh</div><div class="metric-sub">2024 vs $150 in 2021</div></div>
        </div>
        <div id="bess-chart" style="height:280px"></div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-header"><span class="panel-title">Key BESS Players India</span></div>
      <div class="panel-body">
        <table>
          <tr><th>Company</th><th>Scale</th><th>Status</th></tr>
          <tr><td>Greenko</td><td>5 GWh</td><td><span class="signal signal-buy">Active</span></td></tr>
          <tr><td>NTPC</td><td>3 GWh</td><td><span class="signal signal-hold">Tender</span></td></tr>
          <tr><td>Adani Green</td><td>2 GWh</td><td><span class="signal signal-hold">Pipeline</span></td></tr>
          <tr><td>JSW Energy</td><td>1 GWh+</td><td><span class="signal signal-buy">Active</span></td></tr>
          <tr><td>ReNew Power</td><td>1.5 GWh</td><td><span class="signal signal-buy">Active</span></td></tr>
          <tr><td>Amara Raja</td><td>Cell Mfg</td><td><span class="signal signal-buy">Scaling</span></td></tr>
          <tr><td>Exide</td><td>Li-ion Mfg</td><td><span class="signal signal-hold">Ramp-up</span></td></tr>
          <tr><td>Tata Power</td><td>Pumped Hydro</td><td><span class="signal signal-hold">Dev</span></td></tr>
        </table>
      </div>
    </div>
    <div class="panel">
      <div class="panel-header"><span class="panel-title">Technology Mix</span></div>
      <div class="panel-body">
        <div class="bar-row"><div class="bar-label">Li-ion LFP</div><div class="bar-track"><div class="bar-fill" style="width:72%"></div></div><div class="bar-val">72%</div></div>
        <div class="bar-row"><div class="bar-label">Pumped Hydro</div><div class="bar-track"><div class="bar-fill" style="width:18%;background:var(--blue)"></div></div><div class="bar-val">18%</div></div>
        <div class="bar-row"><div class="bar-label">Flow Battery</div><div class="bar-track"><div class="bar-fill" style="width:6%;background:var(--violet)"></div></div><div class="bar-val">6%</div></div>
        <div class="bar-row"><div class="bar-label">Other</div><div class="bar-track"><div class="bar-fill" style="width:4%;background:var(--yellow)"></div></div><div class="bar-val">4%</div></div>
      </div>
    </div>
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header"><span class="panel-title">BESS Deployment Trajectory 2020–2030 (GWh)</span></div>
      <div class="panel-body"><div id="bess-proj-chart" style="height:260px"></div></div>
    </div>
  </div>
</div>

<!-- ══════════ GH2 ══════════ -->
<div id="tab-gh2" class="tab-content">
  <div class="grid2">
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header"><span class="panel-title">Green Hydrogen — National Mission</span></div>
      <div class="panel-body">
        <div class="grid4" style="margin-bottom:16px">
          <div class="metric-card"><div class="metric-label">NGHM Target 2030</div><div class="metric-value" style="color:var(--cyan)">5 MMT/yr</div><div class="metric-sub">National Green H₂ Mission</div></div>
          <div class="metric-card"><div class="metric-label">Electrolyzer Target</div><div class="metric-value" style="color:var(--yellow)">60–100 GW</div><div class="metric-sub">domestic by 2030</div></div>
          <div class="metric-card"><div class="metric-label">Cost Target 2030</div><div class="metric-value" style="color:var(--green)">$1/kg</div><div class="metric-sub">from ~$4 today</div></div>
          <div class="metric-card"><div class="metric-label">NGHM Budget</div><div class="metric-value" style="color:var(--blue)">₹19,744 Cr</div><div class="metric-sub">approved outlay</div></div>
        </div>
        <div id="gh2-chart" style="height:280px"></div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-header"><span class="panel-title">Project Pipeline</span></div>
      <div class="panel-body">
        <table>
          <tr><th>Company</th><th>Target</th><th>Status</th></tr>
          <tr><td>NTPC</td><td>2 MMT/yr</td><td><span class="signal signal-hold">Planning</span></td></tr>
          <tr><td>Adani New Ind</td><td>1 MMT/yr</td><td><span class="signal signal-buy">Active</span></td></tr>
          <tr><td>Reliance</td><td>1 MMT/yr</td><td><span class="signal signal-hold">Dev</span></td></tr>
          <tr><td>HPCL</td><td>Refinery</td><td><span class="signal signal-buy">Pilot</span></td></tr>
          <tr><td>ACME Solar</td><td>Export</td><td><span class="signal signal-hold">Dev</span></td></tr>
          <tr><td>H2e Power</td><td>Electrolyzers</td><td><span class="signal signal-buy">Mfg</span></td></tr>
        </table>
      </div>
    </div>
    <div class="panel">
      <div class="panel-header"><span class="panel-title">GH2 Cost Trajectory ($/kg)</span></div>
      <div class="panel-body"><div id="gh2-cost-chart" style="height:260px"></div></div>
    </div>
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header"><span class="panel-title">GH2 Value Chain India</span></div>
      <div class="panel-body">
        <div class="grid4">
          <div class="metric-card"><div class="metric-label">Upstream</div><div class="metric-value" style="font-size:14px;color:var(--cyan)">Solar + Wind RE</div><div class="metric-sub">Dedicated RE zones</div></div>
          <div class="metric-card"><div class="metric-label">Electrolysis</div><div class="metric-value" style="font-size:14px;color:var(--yellow)">PEM / ALK</div><div class="metric-sub">India pushing domestic mfg</div></div>
          <div class="metric-card"><div class="metric-label">Storage/Transport</div><div class="metric-value" style="font-size:14px;color:var(--green)">NH₃ / LOHC</div><div class="metric-sub">Port infra developing</div></div>
          <div class="metric-card"><div class="metric-label">End Use</div><div class="metric-value" style="font-size:14px;color:var(--blue)">Refining/Steel/Export</div><div class="metric-sub">Fertilizer, shipping, industry</div></div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ══════════ ANALYTICS ══════════ -->
<div id="tab-analytics" class="tab-content">
  <div class="grid2">
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header">
        <span class="panel-title">Deep Analytics</span>
        <select id="analytics-stock" onchange="loadAnalytics()" style="background:var(--bg);color:var(--base0);border:1px solid var(--border);padding:3px 8px;font-size:11px;font-family:var(--font)">
          <option value="ADANIGREEN">Adani Green</option><option value="NHPC">NHPC</option>
          <option value="NTPC">NTPC</option><option value="SUZLON">Suzlon</option>
          <option value="SWSOLAR">Sterling Wilson</option><option value="IREDA">IREDA</option>
          <option value="SJVN">SJVN</option><option value="WAAREEENER">Waaree</option>
          <option value="PREMIENERG">Premier Energy</option><option value="TATAPOWER">Tata Power</option>
        </select>
      </div>
      <div class="panel-body"><div id="analytics-chart" style="height:360px"></div></div>
    </div>
    <div class="panel">
      <div class="panel-header"><span class="panel-title">Technical Indicators</span></div>
      <div class="panel-body" id="analytics-tech"><div class="loader">Select stock above</div></div>
    </div>
    <div class="panel">
      <div class="panel-header"><span class="panel-title">90-Day Projection</span></div>
      <div class="panel-body">
        <div id="proj-chart" style="height:230px"></div>
        <div style="margin-top:8px;font-size:10px;color:var(--base01)">⚠ Poly-regression on 90-day history. Not investment advice.</div>
      </div>
    </div>
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header"><span class="panel-title">India Renewable Electricity Share — World Bank</span></div>
      <div class="panel-body"><div id="wb-chart" style="height:250px"></div></div>
    </div>
  </div>
</div>

<!-- ══════════ NEWS ══════════ -->
<div id="tab-news" class="tab-content">
  <div class="grid2">
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header">
        <span class="panel-title">Live Intel Feed — 7 Sources</span>
        <span id="news-ts" style="font-size:10px;color:var(--base01)"></span>
      </div>
      <div class="panel-body" id="news-feed"><div class="loader">Loading…</div></div>
    </div>
    <div class="panel">
      <div class="panel-header"><span class="panel-title">Policy Milestones</span></div>
      <div class="panel-body">
        <div class="news-item"><div class="news-source">ACTIVE</div><div class="news-title">National Green Hydrogen Mission — ₹19,744 Cr</div><div class="news-date">Jan 2023</div></div>
        <div class="news-item"><div class="news-source">ACTIVE</div><div class="news-title">PLI for High-Efficiency Solar Modules — Round 2</div><div class="news-date">₹24,000 Cr</div></div>
        <div class="news-item"><div class="news-source">ACTIVE</div><div class="news-title">RPO — 43.33% renewable by FY2030</div><div class="news-date">MNRE Notification</div></div>
        <div class="news-item"><div class="news-source">ACTIVE</div><div class="news-title">Green Energy Corridors Phase II — ₹12,031 Cr</div><div class="news-date">Transmission</div></div>
        <div class="news-item"><div class="news-source">ACTIVE</div><div class="news-title">BESS VGF Scheme — 4,000 MWh first tranche</div><div class="news-date">₹3,760 Cr</div></div>
        <div class="news-item"><div class="news-source">2025</div><div class="news-title">Carbon Credit Trading Scheme — BEE framework</div><div class="news-date">Rollout</div></div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-header"><span class="panel-title">Active Tenders / Auctions</span></div>
      <div class="panel-body">
        <div class="news-item"><div class="news-source">SECI</div><div class="news-title">5 GW ISTS-connected Solar + Storage hybrid</div><div class="news-summary">Ongoing tender, L1 expected ~₹2.1/kWh</div></div>
        <div class="news-item"><div class="news-source">NTPC REL</div><div class="news-title">3 GWh BESS procurement — Rajasthan</div></div>
        <div class="news-item"><div class="news-source">SECI</div><div class="news-title">450,000 MT/yr Green Methanol tender</div></div>
        <div class="news-item"><div class="news-source">Rajasthan</div><div class="news-title">6 GW solar (REWA-II), Gujarat: 3 GW hybrid</div></div>
        <div class="news-item"><div class="news-source">MSEDCL</div><div class="news-title">3 GW solar + 500 MW BESS (Maharashtra)</div></div>
      </div>
    </div>
  </div>
</div>

<!-- ══════════ GLOBAL + LIVE TV ══════════ -->
<div id="tab-global" class="tab-content">
  <div class="grid2">

    <!-- Live TV Panel -->
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header">
        <span class="panel-title">Live News TV</span>
        <span style="font-size:10px;color:var(--base01)" id="tv-current-title"></span>
      </div>
      <div id="live-tv-panel">
        <div class="channel-switcher" id="channel-switcher">
          <!-- populated by JS -->
        </div>
        <div id="tv-frame-wrap">
          <iframe id="tv-frame" allowfullscreen allow="autoplay; encrypted-media" src="about:blank"></iframe>
        </div>
        <div class="tv-title">
          <span id="tv-video-title" style="color:var(--base01)">Select a channel above</span>
          <span style="font-size:10px;color:var(--base01)">YouTube Live</span>
        </div>
      </div>
    </div>

    <!-- Global RE Stocks -->
    <div class="panel">
      <div class="panel-header"><span class="panel-title">Global RE ETFs & Stocks</span></div>
      <div class="panel-body">
        <div id="global-stock-grid" class="stock-grid" style="margin-bottom:14px"></div>
      </div>
    </div>

    <!-- Global Solar Leaders -->
    <div class="panel">
      <div class="panel-header"><span class="panel-title">Global Installed Solar (GW)</span></div>
      <div class="panel-body">
        <div class="bar-row"><div class="bar-label">China</div><div class="bar-track"><div class="bar-fill" style="width:95%;background:var(--red)"></div></div><div class="bar-val">780 GW</div></div>
        <div class="bar-row"><div class="bar-label">USA</div><div class="bar-track"><div class="bar-fill" style="width:30%;background:var(--blue)"></div></div><div class="bar-val">230 GW</div></div>
        <div class="bar-row"><div class="bar-label">Germany</div><div class="bar-track"><div class="bar-fill" style="width:11%;background:var(--yellow)"></div></div><div class="bar-val">88 GW</div></div>
        <div class="bar-row"><div class="bar-label">India</div><div class="bar-track"><div class="bar-fill" style="width:11%"></div></div><div class="bar-val">154 GW</div></div>
        <div class="bar-row"><div class="bar-label">Japan</div><div class="bar-track"><div class="bar-fill" style="width:10%;background:var(--magenta)"></div></div><div class="bar-val">78 GW</div></div>
        <div class="bar-row"><div class="bar-label">Australia</div><div class="bar-track"><div class="bar-fill" style="width:8%;background:var(--orange)"></div></div><div class="bar-val">65 GW</div></div>
      </div>
    </div>

    <!-- Global Investment chart -->
    <div class="panel" style="grid-column:1/-1">
      <div class="panel-header"><span class="panel-title">Global vs India RE Investment ($Bn)</span></div>
      <div class="panel-body"><div id="global-inv-chart" style="height:260px"></div></div>
    </div>

    <!-- Key watch items -->
    <div class="panel">
      <div class="panel-header"><span class="panel-title">Global Watchlist for India RE</span></div>
      <div class="panel-body">
        <div class="news-item"><div class="news-source">Polysilicon</div><div class="news-title">China poly price: ~$5/kg — margin pressure on module makers</div></div>
        <div class="news-item"><div class="news-source">US IRA</div><div class="news-title">Indian module exports (Waaree, Premier) benefiting from IRA tariffs on China</div></div>
        <div class="news-item"><div class="news-source">EU CBAM</div><div class="news-title">Carbon border mechanism — India RE exporters gaining edge</div></div>
        <div class="news-item"><div class="news-source">Battery</div><div class="news-title">LFP cell: ~$55/kWh (2024) vs $150 (2021) — BESS economics transform</div></div>
        <div class="news-item"><div class="news-source">Electrolyzer</div><div class="news-title">ALK: $400/kW → target $150/kW by 2030 — GH2 cost curve</div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header"><span class="panel-title">Normalised Performance (Base=100)</span></div>
      <div class="panel-body"><div id="norm-chart" style="height:280px"></div></div>
    </div>

  </div>
</div>

</div><!-- /app -->

<script>
// ── Config ──────────────────────────────────────────
const SL = {
  bg:'#002b36',bg2:'#073642',cyan:'#2aa198',green:'#859900',
  red:'#dc322f',yellow:'#b58900',blue:'#268bd2',violet:'#6c71c4',
  orange:'#cb4b16',magenta:'#d33682',base0:'#839496',base01:'#586e75',base1:'#93a1a1'
};
const PLY = (title='') => ({
  paper_bgcolor:SL.bg2, plot_bgcolor:SL.bg,
  font:{family:'JetBrains Mono,monospace',color:SL.base0,size:11},
  title:{text:title,font:{color:SL.cyan,size:12}},
  xaxis:{gridcolor:'#094554',linecolor:'#094554',zerolinecolor:'#094554'},
  yaxis:{gridcolor:'#094554',linecolor:'#094554',zerolinecolor:'#094554'},
  margin:{t:36,r:16,b:40,l:60},
  legend:{bgcolor:'transparent',font:{size:10}},
  hoverlabel:{bgcolor:SL.bg2,font:{family:'JetBrains Mono',size:11}},
});
const CFG = {responsive:true,displayModeBar:false};

let selectedSym = 'ADANIGREEN.NS';
let allQuotes = {};
let liveChannels = [];
let currentChannel = null;

// ── Clock & Market Status ────────────────────────────
function updateClock(){
  const ist = new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Kolkata'}));
  document.getElementById('clock').textContent = ist.toLocaleTimeString('en-IN',{hour12:false})+' IST';
  const h=ist.getHours(), m=ist.getMinutes();
  const open = h>=9 && (h<15||(h===15&&m<=30));
  const el = document.getElementById('market-status');
  el.className = open?'status-open':'status-closed';
  el.textContent = open?'NSE OPEN':'MARKET CLOSED';
}
setInterval(updateClock,1000); updateClock();

// ── Tab Switching ────────────────────────────────────
function switchTab(name){
  const names=['overview','solar','bess','gh2','analytics','news','global'];
  document.querySelectorAll('.tab').forEach((t,i)=>t.classList.toggle('active',names[i]===name));
  document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  if(name==='analytics') loadAnalytics();
  if(name==='global')    loadGlobal();
  if(name==='bess')      drawBessCharts();
  if(name==='gh2')       drawGH2Charts();
  if(name==='solar')     loadSolarTab();
}

// ── Ticker ─────────────────────────────────────────
function buildTicker(quotes){
  const items = Object.values(quotes).map(q=>{
    const cls = q.change>=0?'tick-up':'tick-dn', arr = q.change>=0?'▲':'▼';
    return `<span style="font-size:11px"><span class="tick-name">${q.name}</span><span class="${cls}">₹${q.price} ${arr}${Math.abs(q.change_pct).toFixed(2)}%</span></span>`;
  });
  const html = items.join('<span style="color:var(--base01);padding:0 10px">|</span>')*2 || items.join('<span style="color:var(--base01);padding:0 10px">|</span>');
  document.getElementById('ticker').innerHTML = [...items,...items].join('<span style="color:var(--base01);padding:0 10px">·</span>');
}

// ── Stock Grid ───────────────────────────────────────
function buildStockGrid(quotes){
  allQuotes = quotes;
  const g = document.getElementById('stock-grid');
  g.innerHTML = Object.entries(quotes).map(([sym,q])=>{
    const cls=q.change>=0?'up':'dn', arr=q.change>=0?'▲':'▼';
    return `<div class="stock-card${sym===selectedSym?' selected':''}" onclick="selectStock('${sym}',this)">
      <div class="sc-name">${q.name}</div>
      <div class="sc-price">₹${q.price.toLocaleString('en-IN')}</div>
      <div class="sc-change ${cls}">${arr} ₹${Math.abs(q.change)} (${Math.abs(q.change_pct)}%)</div>
      <div class="sc-vol">Vol: ${(q.volume/1e6).toFixed(2)}M</div>
    </div>`;
  }).join('');
  buildSolarLeaders(quotes);
}

function selectStock(sym, el){
  selectedSym=sym;
  document.querySelectorAll('.stock-card').forEach(c=>c.classList.remove('selected'));
  el.classList.add('selected');
  loadChart();
}

// ── Chart ───────────────────────────────────────────
async function loadChart(){
  const period = document.getElementById('period-sel').value;
  const sym = selectedSym.replace('.NS','');
  document.getElementById('chart-title').textContent = (allQuotes[selectedSym]?.name||sym)+' — Price History';
  const [histRes, analRes] = await Promise.all([
    fetch(`/api/history/${sym}`).then(r=>r.json()),
    fetch(`/api/analysis/${sym}`).then(r=>r.json()),
  ]);
  const filtered = filterByPeriod(histRes, period);
  drawCandlestick('price-chart', filtered, sym);
  drawTechCards('tech-cards', analRes.technicals);
  const sig = computeSignal(analRes.technicals);
  document.getElementById('chart-signal').innerHTML = `<span class="signal signal-${sig.toLowerCase()}">${sig}</span>`;
}

function filterByPeriod(data, period){
  const d={'3mo':90,'6mo':180,'1y':365,'2y':730,'5y':1825}[period]||365;
  return data.slice(-d);
}

function computeSignal(tech){
  if(!tech||!tech.rsi) return 'HOLD';
  if(tech.rsi<35 && tech.macd>tech.macd_signal) return 'BUY';
  if(tech.rsi>70 && tech.macd<tech.macd_signal) return 'SELL';
  return 'HOLD';
}

function drawCandlestick(divId, data, sym){
  if(!data.length) return;
  const sma20 = data.map((_,i,a)=>{
    if(i<19) return null;
    return a.slice(i-19,i+1).reduce((s,d)=>s+d.close,0)/20;
  });
  Plotly.newPlot(divId,[
    {type:'candlestick',x:data.map(d=>d.date),open:data.map(d=>d.open),
     high:data.map(d=>d.high),low:data.map(d=>d.low),close:data.map(d=>d.close),
     name:sym,increasing:{line:{color:SL.green}},decreasing:{line:{color:SL.red}}},
    {type:'scatter',mode:'lines',x:data.map(d=>d.date),y:sma20,
     name:'SMA20',line:{color:SL.yellow,width:1,dash:'dot'},hoverinfo:'skip'},
    {type:'bar',x:data.map(d=>d.date),y:data.map(d=>d.volume),
     name:'Volume',yaxis:'y2',marker:{color:SL.base01+'55'},showlegend:false},
  ],{...PLY(),yaxis:{domain:[0.3,1]},yaxis2:{overlaying:'y',side:'right',showgrid:false,tickformat:'.2s',domain:[0,0.25]},
     xaxis:{rangeslider:{visible:false}},margin:{t:10,r:60,b:40,l:60}},CFG);
}

function drawTechCards(divId, tech){
  if(!tech) return;
  const rc = tech.rsi<35?SL.green:tech.rsi>70?SL.red:SL.yellow;
  const mc = tech.macd>tech.macd_signal?SL.green:SL.red;
  document.getElementById(divId).innerHTML = `
    <div class="tech-card"><div class="tech-label">RSI (14)</div><div class="tech-value" style="color:${rc}">${tech.rsi}</div></div>
    <div class="tech-card"><div class="tech-label">MACD</div><div class="tech-value" style="color:${mc}">${tech.macd}</div></div>
    <div class="tech-card"><div class="tech-label">MACD Sig</div><div class="tech-value">${tech.macd_signal}</div></div>
    <div class="tech-card"><div class="tech-label">BB Upper</div><div class="tech-value" style="color:${SL.red}">₹${tech.bb_upper}</div></div>
    <div class="tech-card"><div class="tech-label">BB Mid</div><div class="tech-value">₹${tech.bb_mid}</div></div>
    <div class="tech-card"><div class="tech-label">BB Lower</div><div class="tech-value" style="color:${SL.green}">₹${tech.bb_lower}</div></div>
    <div class="tech-card"><div class="tech-label">SMA 20</div><div class="tech-value">₹${tech.sma20}</div></div>
    <div class="tech-card"><div class="tech-label">SMA 50</div><div class="tech-value">₹${tech.sma50||'—'}</div></div>`;
}

// ── MNRE Live Capacity ──────────────────────────────
async function loadMnreLive(){
  const d = await fetch('/api/mnre_live').then(r=>r.json());
  if(d.error||!d.data) return;
  document.getElementById('mnre-as-on').textContent = d.as_on;
  const sectors = [
    {key:'Solar Power*',      color:SL.yellow,  max:280000},
    {key:'Wind Power',        color:SL.blue,    max:100000},
    {key:'Large Hydro^',      color:SL.violet,  max:60000},
    {key:'Small Hydro Power', color:SL.magenta, max:10000},
    {key:'Biomass (Bagasse) Cogeneration', color:SL.green, max:15000},
  ];
  const totalMw = d.data['Total RE']?.cumulative_mw || 0;
  let html = sectors.map(s=>{
    const mw = d.data[s.key]?.cumulative_mw || 0;
    if(!mw) return '';
    const pct = Math.min((mw/s.max)*100,100);
    return `<div class="bar-row">
      <div class="bar-label">${s.key.replace('*','').replace('^','').trim()}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${s.color}"></div></div>
      <div class="bar-val">${(mw/1000).toFixed(1)} GW</div>
    </div>`;
  }).join('');
  // 500GW progress bar
  const prog = ((totalMw/1000)/500*100).toFixed(1);
  html += `<div style="margin-top:14px;padding-top:12px;border-top:1px solid var(--border)">
    <div style="display:flex;justify-content:space-between;margin-bottom:6px">
      <span style="font-size:10px;color:var(--base01)">500 GW Target 2030</span>
      <span style="color:var(--cyan);font-size:11px">${(totalMw/1000).toFixed(1)} GW total RE</span>
    </div>
    <div class="bar-track" style="height:10px">
      <div class="bar-fill" style="width:${prog}%;background:linear-gradient(90deg,var(--cyan),var(--blue))"></div>
    </div>
    <div style="text-align:right;font-size:10px;color:var(--base01);margin-top:3px">${prog}% of 500 GW target</div>
  </div>`;
  document.getElementById('mnre-bars').innerHTML = html;

  // Update solar tab metrics
  const solarMw = d.data['Solar Power*']?.cumulative_mw || 0;
  const solarMonthly = d.data['Solar Power*']?.monthly_mw || 0;
  if(solarMw){
    document.getElementById('solar-mw').textContent = (solarMw/1000).toFixed(1)+' GW';
    document.getElementById('solar-src').textContent = 'LIVE · '+d.as_on;
    document.getElementById('solar-monthly').textContent = (solarMonthly/1000).toFixed(2)+' GW';
  }
}

// ── Commodities ─────────────────────────────────────
function buildCommTable(data){
  const rows = Object.values(data).map(c=>{
    const cls = c.change>=0?'up':'dn';
    return `<tr><td>${c.name}</td><td>${c.price}</td><td class="${cls}">${c.change>=0?'+':''}${c.change_pct}%</td></tr>`;
  }).join('');
  document.getElementById('comm-table').innerHTML = `<tr><th>Asset</th><th>Price</th><th>Chg%</th></tr>${rows}`;
}

// ── Solar Tab ───────────────────────────────────────
async function loadSolarTab(){
  await loadMnreLive();
  drawSolarCharts();
  loadStatewise();
}

function buildSolarLeaders(quotes){
  const syms=['ADANIGREEN.NS','WAAREEENER.NS','PREMIENERG.NS','SWSOLAR.NS','SJVN.NS','NHPC.NS','IREDA.NS'];
  const rows = syms.map(sym=>{
    const q=quotes[sym]; if(!q) return '';
    const cls=q.change>=0?'up':'dn';
    const sig=q.change_pct>2?'BUY':q.change_pct<-2?'SELL':'HOLD';
    return `<tr><td>${q.name}</td><td>₹${q.price}</td><td class="${cls}">${q.change_pct}%</td>
            <td><span class="signal signal-${sig.toLowerCase()}">${sig}</span></td></tr>`;
  }).join('');
  document.getElementById('solar-leaders').innerHTML = `<tr><th>Company</th><th>Price</th><th>%</th><th>Signal</th></tr>${rows}`;
}

function drawSolarCharts(){
  const yrs=[2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025];
  const cap=[3,5,9,18,26,35,40,50,62,73,85,98];
  Plotly.newPlot('solar-history-chart',[
    {type:'bar',x:yrs,y:cap,name:'GW Installed',marker:{color:SL.yellow,opacity:.85}},
    {type:'scatter',mode:'lines+markers',x:yrs,y:cap,line:{color:SL.cyan,width:2},name:'Trend'},
  ],{...PLY('India Solar Installed (GW)'),margin:{t:36,r:16,b:40,l:50}},CFG);

  const py=[2025,2026,2027,2028,2029,2030], pc=[98,120,148,180,225,280];
  Plotly.newPlot('solar-proj-chart',[
    {type:'scatter',mode:'lines+markers',x:yrs,y:cap,name:'Historical',line:{color:SL.cyan,width:2},marker:{size:5}},
    {type:'scatter',mode:'lines+markers',x:py,y:pc,name:'Projected',line:{color:SL.yellow,width:2,dash:'dash'},
     marker:{size:5},fill:'tozeroy',fillcolor:SL.yellow+'11'},
    {type:'scatter',mode:'lines',x:[2030,2030],y:[0,280],name:'Target',line:{color:SL.red,dash:'dot',width:1}},
  ],{...PLY('Solar Capacity Projection 2030 (GW)'),margin:{t:36,r:16,b:40,l:50}},CFG);
}

async function loadStatewise(){
  const d = await fetch('/api/statewise').then(r=>r.json());
  if(!d.states||Object.keys(d.states).length===0) return;
  document.getElementById('statewise-as-on').textContent = d.as_on||'';
  const names=Object.keys(d.states), vals=Object.values(d.states).map(v=>v.res_mw);
  const colors=names.map(n=>n==='Others'?SL.base01:SL.cyan);
  Plotly.newPlot('statewise-chart',[
    {type:'bar',x:names,y:vals,name:'RE Capacity (MW)',
     marker:{color:colors},text:vals.map(v=>(v/1000).toFixed(1)+' GW'),textposition:'outside'},
  ],{...PLY('State-wise Installed RE Capacity (MW) — CEA'),
     yaxis:{title:'MW',gridcolor:'#094554'},xaxis:{tickangle:-30},
     margin:{t:36,r:16,b:80,l:70}},CFG);
}

async function loadSuryaGhar(){
  document.getElementById('surya-live').textContent = 'Fetching via browser automation… (may take 20-30s)';
  try{
    const d = await fetch('/api/pm_surya_ghar').then(r=>r.json());
    if(d.error){
      document.getElementById('surya-live').innerHTML = `<span style="color:var(--orange)">⚠ ${d.note||d.error}</span><br><a href="https://pmsuryaghar.gov.in" target="_blank" style="color:var(--cyan)">Open PM Surya Ghar Portal ↗</a>`;
      return;
    }
    const nums = d.nums?.length ? d.nums.join(' | ') : 'No structured data extracted';
    const counters = Object.values(d.counters||{}).join(' · ');
    document.getElementById('surya-live').innerHTML = `
      <div style="color:var(--base1);margin-bottom:8px"><b>Live numbers:</b> ${nums}</div>
      ${counters?`<div style="color:var(--cyan)">${counters}</div>`:''}
      <div style="color:var(--base01);font-size:10px;margin-top:6px">Fetched: ${d.fetched_at}</div>`;
  }catch(e){
    document.getElementById('surya-live').textContent = 'Error: '+e.message;
  }
}

async function loadPmKusum(){
  document.getElementById('kusum-live').textContent = 'Fetching via browser automation…';
  try{
    const d = await fetch('/api/pm_kusum').then(r=>r.json());
    if(d.error){
      document.getElementById('kusum-live').innerHTML = `<span style="color:var(--orange)">⚠ ${d.note||d.error}</span><br><a href="https://pmkusum.mnre.gov.in" target="_blank" style="color:var(--cyan)">Open PM KUSUM Portal ↗</a>`;
      return;
    }
    const nums = d.nums?.map(n=>n.join(' ')).join(' | ') || '';
    document.getElementById('kusum-live').innerHTML = `
      <div style="color:var(--base1)">${nums}</div>
      <div style="color:var(--base01);font-size:10px;margin-top:6px">Fetched: ${d.fetched_at}</div>`;
  }catch(e){
    document.getElementById('kusum-live').textContent = 'Error: '+e.message;
  }
}

// ── BESS Charts ─────────────────────────────────────
function drawBessCharts(){
  const yr=[2020,2021,2022,2023,2024,2025,2026,2027,2028,2029,2030];
  const hist=[0.1,0.3,0.8,1.5,4,null,null,null,null,null,null];
  const proj=[null,null,null,null,4,8,14,22,32,40,47];
  Plotly.newPlot('bess-chart',[
    {type:'bar',x:yr.slice(0,5),y:hist.slice(0,5),name:'Actual GWh',marker:{color:SL.orange,opacity:.85}},
    {type:'bar',x:yr.slice(4),y:proj.slice(4),name:'Projected GWh',marker:{color:SL.orange+'55',line:{color:SL.orange,width:1}}},
  ],{...PLY('India BESS Deployment (GWh)'),barmode:'group',margin:{t:36,r:16,b:40,l:50}},CFG);

  Plotly.newPlot('bess-proj-chart',[
    {type:'scatter',mode:'lines+markers',x:yr.slice(0,5),y:hist.slice(0,5),name:'Actual',line:{color:SL.orange,width:2},marker:{size:6}},
    {type:'scatter',mode:'lines+markers',x:yr.slice(4),y:proj.slice(4),name:'Projected',
     line:{color:SL.yellow,width:2,dash:'dash'},marker:{size:6},fill:'tozeroy',fillcolor:SL.yellow+'11'},
    {type:'scatter',mode:'lines',x:[2020,2030],y:[47,47],name:'Target 47 GWh',line:{color:SL.red,dash:'dot',width:1}},
  ],{...PLY('BESS Trajectory (GWh)'),margin:{t:36,r:16,b:40,l:50}},CFG);
}

// ── GH2 Charts ──────────────────────────────────────
function drawGH2Charts(){
  const yr=[2020,2021,2022,2023,2024,2025,2026,2027,2028,2029,2030];
  const cost=[6,5.5,4.8,4,3.5,2.8,2.2,1.7,1.3,1.1,1];
  Plotly.newPlot('gh2-chart',[
    {type:'scatter',mode:'lines+markers',x:yr,y:cost,name:'GH2 Cost ($/kg)',
     line:{color:SL.cyan,width:2.5},marker:{size:6},fill:'tozeroy',fillcolor:SL.cyan+'11'},
    {type:'scatter',mode:'lines',x:[2020,2030],y:[1,1],name:'$1/kg Target',line:{color:SL.green,dash:'dot',width:1.5}},
  ],{...PLY('Green Hydrogen Cost Trajectory India ($/kg)'),margin:{t:36,r:16,b:40,l:60}},CFG);

  Plotly.newPlot('gh2-cost-chart',[
    {type:'bar',x:yr,y:[0,0,.02,.08,.2,.5,1.2,2.1,3.2,4.2,5],name:'GH2 Production (MMT/yr)',marker:{color:SL.violet,opacity:.85}},
    {type:'scatter',mode:'lines',x:[2020,2030],y:[5,5],name:'NGHM Target',line:{color:SL.red,dash:'dot',width:1.5}},
  ],{...PLY('GH2 Production Projection (MMT/yr)'),margin:{t:36,r:16,b:40,l:60}},CFG);
}

// ── Analytics Tab ───────────────────────────────────
async function loadAnalytics(){
  const sym = document.getElementById('analytics-stock').value;
  const d = await fetch(`/api/analysis/${sym}`).then(r=>r.json());
  const hist=d.history, proj=d.projection, tech=d.technicals;

  const bb_up=hist.map((_,i,a)=>{if(i<19)return null;const sl=a.slice(i-19,i+1),m=sl.reduce((s,x)=>s+x.close,0)/20,sd=Math.sqrt(sl.reduce((s,x)=>s+(x.close-m)**2,0)/20);return m+2*sd});
  const bb_lo=hist.map((_,i,a)=>{if(i<19)return null;const sl=a.slice(i-19,i+1),m=sl.reduce((s,x)=>s+x.close,0)/20,sd=Math.sqrt(sl.reduce((s,x)=>s+(x.close-m)**2,0)/20);return m-2*sd});

  Plotly.newPlot('analytics-chart',[
    {type:'candlestick',x:hist.map(d=>d.date),open:hist.map(d=>d.open),high:hist.map(d=>d.high),low:hist.map(d=>d.low),close:hist.map(d=>d.close),name:sym,increasing:{line:{color:SL.green}},decreasing:{line:{color:SL.red}}},
    {type:'scatter',mode:'lines',x:hist.map(d=>d.date),y:bb_up,name:'BB Upper',line:{color:SL.red,width:1,dash:'dot'},hoverinfo:'skip'},
    {type:'scatter',mode:'lines',x:hist.map(d=>d.date),y:bb_lo,name:'BB Lower',line:{color:SL.green,width:1,dash:'dot'},fill:'tonexty',fillcolor:SL.blue+'09',hoverinfo:'skip'},
  ],{...PLY(sym+' — Candlestick + Bollinger'),xaxis:{rangeslider:{visible:false}},margin:{t:36,r:16,b:40,l:60}},CFG);

  if(proj.length)
    Plotly.newPlot('proj-chart',[
      {type:'scatter',mode:'lines',x:hist.slice(-30).map(d=>d.date),y:hist.slice(-30).map(d=>d.close),name:'Recent',line:{color:SL.cyan,width:2}},
      {type:'scatter',mode:'lines',x:proj.map(d=>d.date),y:proj.map(d=>d.projected),name:'90d Projection',line:{color:SL.yellow,width:2,dash:'dash'},fill:'tozeroy',fillcolor:SL.yellow+'09'},
    ],{...PLY('90-Day Projection'),margin:{t:36,r:16,b:40,l:60}},CFG);

  drawTechCards('analytics-tech', tech);

  // World Bank chart
  const wb = await fetch('/api/worldbank').then(r=>r.json());
  if(wb.renewable_pct?.length){
    const sorted = [...wb.renewable_pct].sort((a,b)=>a.year-b.year);
    Plotly.newPlot('wb-chart',[
      {type:'scatter',mode:'lines+markers',x:sorted.map(d=>d.year),y:sorted.map(d=>d.value),
       name:'Renewable %',line:{color:SL.cyan,width:2},fill:'tozeroy',fillcolor:SL.cyan+'22',marker:{size:5}},
    ],{...PLY('India: Renewable Electricity (% of total) — World Bank'),margin:{t:36,r:16,b:40,l:60}},CFG);
  }
}

// ── Alerts ──────────────────────────────────────────
const CAT_CLASS = {
  'SUPPLY CHAIN':'cat-supply','TRADE':'cat-trade','POLICY':'cat-policy',
  'BESS/GH2':'cat-bess','MARKET':'cat-market','COMPANIES':'cat-companies','GLOBAL':'cat-global'
};
async function loadAlerts(){
  const alerts = await fetch('/api/alerts').then(r=>r.json());
  const newCount = alerts.filter(a=>a.is_new).length;
  const badge = document.getElementById('alert-badge');
  if(newCount>0){
    badge.style.display='flex'; badge.textContent=newCount>9?'9+':newCount;
  }
  const body = document.getElementById('drawer-body');
  if(!alerts.length){ body.innerHTML='<div class="loader" style="padding:30px">No alerts matched</div>'; return; }
  body.innerHTML = alerts.map(a=>`
    <div class="alert-item${a.is_new?' new-alert':''}">
      <span class="alert-cat ${CAT_CLASS[a.category]||''}">${a.category}</span>
      ${a.is_new?'<span style="font-size:9px;color:var(--yellow);margin-left:6px">NEW</span>':''}
      <div class="alert-title"><a href="${a.link}" target="_blank">${a.title}</a></div>
      <div class="alert-source">${a.source} · ${a.date.substring(0,16)}</div>
      <div class="alert-kw">Keywords: ${a.keywords.join(', ')}</div>
    </div>`).join('');
}

function toggleDrawer(){
  const d=document.getElementById('alert-drawer');
  const o=document.getElementById('drawer-overlay');
  const open=d.classList.toggle('open');
  o.style.display=open?'block':'none';
  if(open){ loadAlerts(); document.getElementById('alert-badge').style.display='none'; }
}
function closeDrawer(){
  document.getElementById('alert-drawer').classList.remove('open');
  document.getElementById('drawer-overlay').style.display='none';
}

// ── Live TV ─────────────────────────────────────────
async function initLiveTv(){
  const channels = await fetch('/api/live_channels').then(r=>r.json());
  liveChannels = channels;
  const switcher = document.getElementById('channel-switcher');
  switcher.innerHTML = channels.map((ch,i)=>
    `<button class="ch-btn" id="ch-${i}" onclick="switchChannel(${i})" style="color:${ch.color}">${ch.name}</button>`
  ).join('');
  if(channels.length) switchChannel(0);
}

async function switchChannel(idx){
  document.querySelectorAll('.ch-btn').forEach((b,i)=>b.classList.toggle('active',i===idx));
  const ch = liveChannels[idx];
  currentChannel = ch;
  document.getElementById('tv-video-title').textContent = 'Loading '+ch.name+'…';
  document.getElementById('tv-current-title').textContent = ch.name;

  const frame = document.getElementById('tv-frame');
  // Try live_stream embed first
  frame.src = `https://www.youtube.com/embed/live_stream?channel=${ch.id}&autoplay=1&mute=0`;

  // Background: get latest video from RSS
  try{
    const d = await fetch(`/api/youtube_live/${ch.id}`).then(r=>r.json());
    if(d.video_id){
      document.getElementById('tv-video-title').textContent = d.title || ch.name;
      // Only override if live_stream fails (we can't detect that here)
    }
  }catch(e){}
}

// ── Global Tab ──────────────────────────────────────
async function loadGlobal(){
  initLiveTv();
  const d = await fetch('/api/global_re').then(r=>r.json());
  const grid = document.getElementById('global-stock-grid');
  grid.innerHTML = Object.values(d).map(q=>{
    const cls=q.change>=0?'up':'dn', arr=q.change>=0?'▲':'▼';
    return `<div class="stock-card"><div class="sc-name">${q.name}</div>
      <div class="sc-price">$${q.price}</div>
      <div class="sc-change ${cls}">${arr} ${Math.abs(q.change_pct)}%</div></div>`;
  }).join('');

  const yrs=[2015,2016,2017,2018,2019,2020,2021,2022,2023,2024];
  Plotly.newPlot('global-inv-chart',[
    {type:'bar',x:yrs,y:[286,302,334,332,363,501,750,891,1000,1200],name:'Global ($Bn)',marker:{color:SL.blue,opacity:.7}},
    {type:'bar',x:yrs,y:[10,12,15,20,14,12,22,25,30,35],name:'India ($Bn)',marker:{color:SL.cyan,opacity:.9}},
  ],{...PLY('Global vs India RE Investment ($Bn)'),barmode:'overlay',margin:{t:36,r:16,b:40,l:60}},CFG);

  // Normalised chart
  try{
    const [tan,icln]=await Promise.all([
      fetch('/api/history/TAN').then(r=>r.json()),
      fetch('/api/history/ICLN').then(r=>r.json()),
    ]);
    if(tan.length&&icln.length){
      const norm=arr=>{const b=arr[0].close;return arr.map(d=>({date:d.date,v:+(d.close/b*100).toFixed(2)}))};
      const s=norm(tan.slice(-252)), ic=norm(icln.slice(-252));
      Plotly.newPlot('norm-chart',[
        {type:'scatter',mode:'lines',x:s.map(d=>d.date),y:s.map(d=>d.v),name:'TAN (Solar ETF)',line:{color:SL.yellow,width:2}},
        {type:'scatter',mode:'lines',x:ic.map(d=>d.date),y:ic.map(d=>d.v),name:'ICLN (Global CE)',line:{color:SL.blue,width:2}},
      ],{...PLY('Global RE ETFs — Normalised (Base=100)'),margin:{t:36,r:16,b:40,l:60}},CFG);
    }
  }catch(e){}
}

// ── News Feed ─────────────────────────────────────
async function loadNews(){
  const articles = await fetch('/api/news').then(r=>r.json());
  document.getElementById('news-ts').textContent = 'Updated '+new Date().toLocaleTimeString('en-IN',{hour12:false,timeZone:'Asia/Kolkata'})+' IST';
  document.getElementById('news-feed').innerHTML = articles.map(a=>`
    <div class="news-item">
      <div class="news-source">${a.source}</div>
      <div class="news-title"><a href="${a.link}" target="_blank">${a.title}</a></div>
      <div class="news-date">${a.date}</div>
      ${a.summary?`<div class="news-summary">${a.summary}</div>`:''}
    </div>`).join('')||'<div class="loader">No news</div>';
}

// ── Boot ─────────────────────────────────────────
async function init(){
  const d = await fetch('/api/dashboard').then(r=>r.json());
  buildTicker(d.quotes);
  buildStockGrid(d.quotes);
  buildCommTable(d.commodities);
  loadMnreLive();
  loadChart();
  loadAlerts();
  loadNews();
  drawSolarCharts();
}
init();
setInterval(async()=>{const q=await fetch('/api/quotes').then(r=>r.json());buildTicker(q);buildStockGrid(q)},5*60*1000);
setInterval(loadAlerts, 10*60*1000);
setInterval(loadNews,   15*60*1000);
</script>
</body>
</html>

```