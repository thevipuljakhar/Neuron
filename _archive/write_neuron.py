"""Helper script to write neuron.py v2"""
import ast

src = r'''
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
            strs=[str(v).strip() for v in row.values if isinstance(v,str) and v.strip() and v.strip()!="NaN"]
            nums=[v for v in row.values if isinstance(v,(int,float)) and not isinstance(v,bool)]
            if strs and len(nums)>=2:
                label=strs[-1]
                try:
                    mw=float(nums[0]); pct=float(nums[1])
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
'''

open("D:/Polygon/Git Projects/Neuron/neuron.py","w",encoding="utf-8").write(src.strip())
ast.parse(src); print("Syntax OK -", len(src.splitlines()), "lines")
