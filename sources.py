"""
NEURON v11 — Source Registry & Ingestion Engine ("The Observatory")

540+ declarative sources: ≥180 India, ≥60 per continent. Four source types:
  rss    — direct RSS/Atom feed
  gnews  — Google News RSS standing query (free, region-targeted via gl=)
  gdelt  — GDELT 2.0 DOC API standing query (global full-text, 65 languages)
  api    — structured data fetcher living in neuron.py (counted, not ingested here)

A background worker rotates through tiers (T1 core 15 min · T2 hourly ·
T3 long-tail 6 h), stores deduped articles in SQLite (v11_articles) and tracks
per-source health (v11_source_health). Nothing here blocks a request thread,
and a dead source only ever costs its own slot.
"""
import hashlib
import json
import os
import random
import re
import sqlite3
import threading
import time
from datetime import datetime
from urllib.parse import quote_plus

import feedparser
import requests

DB_PATH = os.path.join(os.path.dirname(__file__), "neuron.db")

REGIONS = ["india", "asia", "europe", "africa", "north_america",
           "south_america", "oceania", "global"]

TIER_INTERVAL = {1: 900, 2: 3600, 3: 21600}      # seconds between fetches
RETENTION_DAYS = 30

# ── Registry builders ─────────────────────────────────────────────────────────
def S(sid, name, stype, region, category, tier, url="", query="", gl="IN", hl="en"):
    return {"id": sid, "name": name, "type": stype, "region": region,
            "category": category, "tier": tier, "url": url, "query": query,
            "gl": gl, "hl": hl}

def _gnews_url(query, gl="IN", hl="en"):
    ceid = f"{gl}:{hl}"
    return (f"https://news.google.com/rss/search?q={quote_plus(query)}"
            f"&hl={hl}-{gl}&gl={gl}&ceid={quote_plus(ceid)}")

def _gdelt_url(query):
    return ("https://api.gdeltproject.org/api/v2/doc/doc?query="
            f"{quote_plus(query)}&mode=artlist&maxrecords=30&format=json&timespan=3d")

SOURCES = []

def _add(*args, **kw):
    SOURCES.append(S(*args, **kw))

# ═══ INDIA — target ≥180 ══════════════════════════════════════════════════════
# 1. Direct RSS — curated specialist + business press (tier 1/2)
_INDIA_RSS = [
    ("in_mercom",      "Mercom India",            "https://www.mercomindia.com/feed", 1),
    ("in_pvmag",       "PV Magazine India",       "https://www.pv-magazine-india.com/feed/", 1),
    ("in_saur",        "Saur Energy",             "https://www.saurenergy.com/feed", 1),
    ("in_etenergy",    "ET EnergyWorld",          "https://energy.economictimes.indiatimes.com/rss/topstories", 1),
    ("in_eqmag",       "EQ Magazine",             "https://www.eqmagpro.com/feed/", 2),
    ("in_reglobal",    "REGlobal",                "https://reglobal.org/feed/", 2),
    ("in_jmk",         "JMK Research",            "https://jmkresearch.com/feed/", 2),
    ("in_solarquarter","Solar Quarter",           "https://solarquarter.com/feed/", 2),
    ("in_energetica",  "Energetica India",        "https://www.energetica-india.net/rss", 2),
    ("in_powerline",   "Powerline Magazine",      "https://powerline.net.in/feed/", 2),
    ("in_renpost",     "Renewable Energy Post IN","https://renewablewatch.in/feed/", 3),
    ("in_pib_power",   "PIB — Ministry of Power", "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3", 1),
]
for sid, name, url, tier in _INDIA_RSS:
    _add(sid, name, "rss", "india", "re_industry", tier, url=url)

# 2. Per-state RE coverage — Google News standing queries (T2/T3)
_IN_STATES = [
    "Rajasthan","Gujarat","Tamil Nadu","Karnataka","Maharashtra","Andhra Pradesh",
    "Madhya Pradesh","Telangana","Uttar Pradesh","Punjab","Haryana","Bihar",
    "Odisha","West Bengal","Kerala","Jharkhand","Chhattisgarh","Assam",
    "Himachal Pradesh","Uttarakhand","Goa","Tripura","Meghalaya","Manipur",
    "Nagaland","Mizoram","Arunachal Pradesh","Sikkim","Ladakh","Jammu Kashmir",
]
for st in _IN_STATES:
    sid = "in_state_" + st.lower().replace(" ", "_")
    tier = 2 if st in ("Rajasthan","Gujarat","Tamil Nadu","Karnataka","Maharashtra","Andhra Pradesh") else 3
    _add(sid, f"{st} RE news", "gnews", "india", "re_industry", tier,
         query=f'"{st}" (solar OR wind OR renewable OR "green hydrogen" OR battery storage)')

# 3. Theme standing queries — micro+macro factors that move Indian RE
_IN_THEMES = [
    ("almm",            'ALMM solar module list', 2),
    ("bcd_duty",        'basic customs duty solar modules India', 2),
    ("pli_solar",       'PLI scheme solar manufacturing India', 2),
    ("bess_tender",     'battery energy storage tender India', 1),
    ("green_h2",        'green hydrogen India electrolyzer', 2),
    ("curtailment",     'renewable curtailment India', 2),
    ("transmission",    'ISTS transmission renewable India', 2),
    ("discom_dues",     'DISCOM dues renewable generators', 2),
    ("rpo",             'renewable purchase obligation RPO India', 3),
    ("solar_tariff",    'solar tariff auction India Rs/kWh', 2),
    ("wind_auction",    'wind energy auction India SECI', 2),
    ("rooftop",         'rooftop solar India PM Surya Ghar', 2),
    ("kusum",           'PM-KUSUM solar pump scheme', 3),
    ("module_price",    'solar module price India', 2),
    ("cell_mfg",        'solar cell manufacturing India gigawatt', 2),
    ("wafer_ingot",     'wafer ingot manufacturing India solar', 3),
    ("polysilicon_in",  'polysilicon plant India', 3),
    ("land_acq",        'land acquisition solar park India', 3),
    ("grid_storage",    'pumped hydro storage India', 3),
    ("smart_meter",     'smart meter rollout India', 3),
    ("ev_charging",     'EV charging infrastructure India', 3),
    ("coal_phasedown",  'coal plant retirement India', 3),
    ("power_demand",    'peak power demand India record', 2),
    ("monsoon_power",   'monsoon impact power generation India', 3),
    ("heatwave_grid",   'heatwave electricity grid India', 3),
    ("rec_market",      'renewable energy certificate trading India', 3),
    ("carbon_credit",   'carbon credit trading scheme India', 3),
    ("offshore_wind_in",'offshore wind India Gujarat Tamil Nadu', 3),
    ("floating_solar",  'floating solar India reservoir', 3),
    ("agrivoltaics",    'agrivoltaics India', 3),
    ("nuclear_smr",     'small modular reactor India nuclear', 3),
    ("biofuel",         'ethanol biofuel compressed biogas India', 3),
    ("rare_earth_in",   'rare earth magnets India wind', 3),
    ("solar_export",    'India solar module export US', 2),
    ("china_import",    'India solar import China dependence', 2),
    ("inr_impact",      'rupee depreciation importers energy', 3),
    ("rbi_rates",       'RBI rate decision infrastructure lending', 3),
    ("budget_energy",   'union budget renewable energy allocation', 3),
    ("cop_india",       'India climate commitment NDC', 3),
    ("adani_green_t",   'Adani Green Energy', 2),
    ("tata_power_t",    'Tata Power renewable', 2),
    ("reliance_re",     'Reliance new energy giga factory', 2),
    ("waaree_t",        'Waaree Energies', 2),
    ("premier_t",       'Premier Energies solar', 2),
    ("saatvik_t",       'Saatvik Green Energy', 1),
    ("vikram_t",        'Vikram Solar', 3),
    ("goldi_t",         'Goldi Solar', 3),
    ("renew_t",         'ReNew Power', 3),
    ("suzlon_t",        'Suzlon wind order', 2),
    ("inox_wind_t",     'Inox Wind', 3),
    ("ntpc_green_t",    'NTPC Green Energy', 2),
    ("sjvn_t",          'SJVN renewable', 3),
    ("nhpc_t",          'NHPC hydro solar', 3),
    ("ireda_t",         'IREDA financing renewable', 2),
    ("pfc_rec_t",       'PFC REC power financing', 3),
    ("sterling_t",      'Sterling Wilson solar EPC', 3),
    ("borosil_t",       'Borosil Renewables solar glass', 3),
    ("websol_t",        'Websol Energy solar cell', 3),
    ("insolation_t",    'Insolation Energy', 3),
    ("juniper_t",       'Juniper Green Energy', 3),
    ("acme_t",          'ACME Solar', 3),
    ("avaada_t",        'Avaada Energy', 3),
    ("hero_future_t",   'Hero Future Energies', 3),
    ("o2_power_t",      'O2 Power renewable', 3),
    ("serentica_t",     'Serentica Renewables', 3),
    ("amp_energy_t",    'Amp Energy India', 3),
    ("brookfield_in",   'Brookfield renewable India', 3),
    ("emmvee_t",        'Emmvee solar IPO', 3),
]
for key, q, tier in _IN_THEMES:
    _add(f"in_theme_{key}", f"IN: {q[:40]}", "gnews", "india",
         "re_industry" if key.endswith("_t") else "policy", tier, query=q)

# 4. Government / institutional via site: queries (Google News indexes them)
_IN_GOV_SITES = [
    ("mnre",    "mnre.gov.in",            1), ("mop",     "powermin.gov.in",      2),
    ("cea",     "cea.nic.in",             2), ("cerc",    "cercind.gov.in",       2),
    ("seci",    "seci.co.in",             1), ("ireda",   "ireda.in",             3),
    ("gridin",  "grid-india.in",          3), ("posoco",  "posoco.in",            3),
    ("niti",    "niti.gov.in energy",     3), ("bee",     "beeindia.gov.in",      3),
    ("nise",    "nise.res.in",            3), ("niwe",    "niwe.res.in",          3),
    ("iex",     "iexindia.com",           2), ("pxil",    "powerexindia.in",      3),
    ("dgtr",    "dgtr.gov.in solar",      3), ("moef",    "moef.gov.in renewable",3),
    ("mines",   "mines.gov.in critical minerals", 3),
    ("dhi",     "heavyindustries.gov.in PLI", 3),
    ("pib_all", "pib.gov.in renewable",   2), ("sldc_guj","sldcguj.com",          3),
]
for key, site, tier in _IN_GOV_SITES:
    _add(f"in_gov_{key}", f"GOV: {site.split(' ')[0]}", "gnews", "india", "policy",
         tier, query=f"site:{site}")
# SERCs — state regulators (orders move tariffs & RPO enforcement)
for st in ["Rajasthan","Gujarat","Tamil Nadu","Karnataka","Maharashtra",
           "Andhra Pradesh","Madhya Pradesh","Telangana","Uttar Pradesh",
           "Punjab","Haryana","Odisha","West Bengal","Kerala","Bihar"]:
    _add(f"in_serc_{st.lower().replace(' ','_')}", f"SERC {st}", "gnews", "india",
         "policy", 3, query=f'"{st} Electricity Regulatory Commission" order')

# 4b. Think-tanks & business-press energy desks (analysis layer)
for key, site, tier in [
    ("ceew",    "ceew.in",                    3), ("ieefa",   "ieefa.org India",     2),
    ("teri",    "teriin.org",                 3), ("prayas",  "prayaspune.org",      3),
    ("wri_in",  "wri-india.org",              3), ("cstep",   "cstep.in",            3),
    ("cef_in",  "climate energy finance India",3), ("icra",   "ICRA renewable rating outlook", 3),
    ("crisil",  "CRISIL power renewable report", 3),
    ("et_pwr",  "economictimes.indiatimes.com power renewable", 2),
    ("bs_energy","business-standard.com renewable energy", 2),
    ("mint_en", "livemint.com energy solar",  2),
    ("hbl_en",  "thehindubusinessline.com renewable", 3),
    ("mc_en",   "moneycontrol.com renewable energy", 3),
    ("fe_en",   "financialexpress.com renewable", 3),
    ("dte",     "downtoearth.org.in energy",  3),
]:
    _add(f"in_press_{key}", f"IN press: {site[:30]}", "gnews", "india", "finance",
         tier, query=site if "site:" in site or "." not in site.split(' ')[0] else f"site:{site.split(' ')[0]} {' '.join(site.split(' ')[1:])}")

# 4c. DISCOMs & state utilities (payment risk, PPAs, curtailment ground truth)
for key, q in [
    ("guvnl",  "GUVNL Gujarat Urja tender PPA"), ("msedcl", "MSEDCL Maharashtra power"),
    ("tangedco","TANGEDCO Tamil Nadu"),          ("bescom", "BESCOM Karnataka"),
    ("uppcl",  "UPPCL Uttar Pradesh power"),     ("pspcl",  "PSPCL Punjab power"),
    ("jvvnl",  "Rajasthan DISCOM Jodhpur Jaipur"),("apdiscom","Andhra Pradesh DISCOM dues"),
    ("tsdiscom","Telangana DISCOM power"),       ("wbsedcl","WBSEDCL Bengal power"),
]:
    _add(f"in_discom_{key}", f"DISCOM: {q[:28]}", "gnews", "india", "grid", 3, query=q)

# 5. GDELT standing queries — multilingual catch-all for India
_IN_GDELT = [
    ("solar_in",   'solar India (tender OR auction OR manufacturing)'),
    ("wind_in",    'wind energy India'),
    ("storage_in", 'battery storage India'),
    ("h2_in",      'green hydrogen India'),
    ("grid_in",    'power grid India transmission'),
    ("policy_in",  'renewable policy India ministry'),
    ("trade_in",   'India solar trade duty tariff'),
    ("invest_in",  'renewable investment India billion'),
]
for key, q in _IN_GDELT:
    _add(f"in_gdelt_{key}", f"GDELT: {q[:38]}", "gdelt", "india", "re_industry", 2, query=q)

# 6. Structured API sources already live in neuron.py (counted in registry)
for key, name in [("mnre_live","MNRE physical progress"), ("cea_ic","CEA installed capacity"),
                  ("seci_t","SECI tenders"), ("seci_r","SECI results (LoA)"),
                  ("almm","ALMM List-I/II"), ("kusum","PM-KUSUM xlsx"),
                  ("surya","PM Surya Ghar xlsx"), ("mnre_state","MNRE state PDF"),
                  ("cea_gen","CEA generation"), ("india_macro","India macro (WB)")]:
    _add(f"in_api_{key}", name, "api", "india", "official_data", 1)

# ═══ ASIA (ex-India) — target ≥60 ═════════════════════════════════════════════
_ASIA_COUNTRIES = [
    ("CN","China"),("JP","Japan"),("KR","South Korea"),("VN","Vietnam"),
    ("ID","Indonesia"),("MY","Malaysia"),("TH","Thailand"),("PH","Philippines"),
    ("TW","Taiwan"),("PK","Pakistan"),("BD","Bangladesh"),("LK","Sri Lanka"),
    ("AE","UAE"),("SA","Saudi Arabia"),("QA","Qatar"),("IL","Israel"),
    ("TR","Turkey"),("KZ","Kazakhstan"),("SG","Singapore"),("UZ","Uzbekistan"),
]
for gl, cname in _ASIA_COUNTRIES:
    _add(f"as_{gl.lower()}", f"{cname} energy", "gnews", "asia", "re_industry",
         2 if gl in ("CN","JP","KR","VN","SA","AE") else 3,
         query=f"{cname} (solar OR wind OR renewable OR energy storage OR power grid)", gl="US")
_ASIA_THEMES = [
    ("poly_price",   'polysilicon price China', 1),
    ("cn_exports",   'China solar module export', 1),
    ("cn_curbs",     'China solar export restrictions technology', 2),
    ("cn_capacity",  'China solar manufacturing overcapacity', 2),
    ("lithium_cn",   'lithium battery price China CATL BYD', 2),
    ("cn_wind",      'China wind turbine export', 3),
    ("jp_offshore",  'Japan offshore wind auction', 3),
    ("kr_battery",   'Korea battery LG Samsung SK', 3),
    ("vn_solar",     'Vietnam solar wind power plan PDP8', 3),
    ("gulf_h2",      'Saudi UAE green hydrogen NEOM', 2),
    ("gulf_solar",   'Gulf solar tender lowest tariff', 3),
    ("asean_grid",   'ASEAN power grid interconnection', 3),
    ("cn_grid",      'China ultra high voltage grid', 3),
    ("semiconductor",'solar cell technology TOPCon HJT perovskite', 2),
    ("cn_rare",      'China rare earth export control', 2),
    ("strait",       'Taiwan strait shipping semiconductor risk', 3),
    ("cn_coal",      'China coal power approvals', 3),
    ("asia_lng",     'Asia LNG spot price JKM', 2),
]
for key, q, tier in _ASIA_THEMES:
    _add(f"as_theme_{key}", f"AS: {q[:38]}", "gnews", "asia", "supply_chain", tier, query=q, gl="US")
_ASIA_RSS = [
    ("as_pvtech",   "PV Tech",          "https://www.pv-tech.org/feed/", 1),
    ("as_taiyang",  "Taiyang News",     "https://taiyangnews.info/feed/", 2),
    ("as_energytrend","EnergyTrend",    "https://www.energytrend.com/rss.html", 3),
    ("as_asianpower","Asian Power",     "https://asian-power.com/rss.xml", 3),
]
for sid, name, url, tier in _ASIA_RSS:
    _add(sid, name, "rss", "asia", "re_industry", tier, url=url)
for key, q in [("cn_energy","China renewable energy policy"),
               ("asia_supply","solar supply chain Asia polysilicon wafer"),
               ("asia_trade","solar trade tariff Asia export"),
               ("gulf_energy","Gulf renewable hydrogen energy transition"),
               ("asia_grid","power grid blackout Asia"),
               ("asia_finance","renewable project financing Asia")]:
    _add(f"as_gdelt_{key}", f"GDELT: {q[:38]}", "gdelt", "asia", "geopolitics", 2, query=q)

# ═══ EUROPE — target ≥60 ══════════════════════════════════════════════════════
_EU_COUNTRIES = [
    ("DE","Germany"),("FR","France"),("ES","Spain"),("IT","Italy"),("GB","UK"),
    ("NL","Netherlands"),("PL","Poland"),("PT","Portugal"),("GR","Greece"),
    ("SE","Sweden"),("NO","Norway"),("DK","Denmark"),("FI","Finland"),
    ("RO","Romania"),("UA","Ukraine"),("IE","Ireland"),("BE","Belgium"),("AT","Austria"),
]
for gl, cname in _EU_COUNTRIES:
    _add(f"eu_{gl.lower()}", f"{cname} energy", "gnews", "europe", "re_industry",
         2 if gl in ("DE","ES","GB","FR") else 3,
         query=f"{cname} (solar OR wind OR renewable OR grid OR power price)", gl="US")
_EU_THEMES = [
    ("cbam",        'EU CBAM carbon border', 2),
    ("ets",         'EU ETS carbon price', 2),
    ("nzia",        'EU Net Zero Industry Act solar manufacturing', 2),
    ("offshore",    'offshore wind auction Europe North Sea', 2),
    ("h2bank",      'European hydrogen bank auction', 3),
    ("ttf_gas",     'TTF gas price Europe', 2),
    ("grid_eu",     'Europe grid congestion interconnector', 3),
    ("neg_price",   'negative electricity prices Europe solar', 3),
    ("re_permit",   'renewable permitting Europe reform', 3),
    ("solar_eu_mfg",'European solar manufacturer insolvency Meyer Burger', 3),
    ("wind_oem",    'Vestas Siemens Gamesa orders', 2),
    ("nuclear_eu",  'Europe nuclear new build SMR', 3),
    ("russia_energy",'Russia energy sanctions pipeline', 2),
    ("balkans",     'Balkans renewable auction', 3),
]
for key, q, tier in _EU_THEMES:
    _add(f"eu_theme_{key}", f"EU: {q[:38]}", "gnews", "europe", "policy", tier, query=q, gl="US")
_EU_RSS = [
    ("eu_euractiv",  "Euractiv Energy",      "https://www.euractiv.com/sections/energy/feed/", 2),
    ("eu_cleanwire", "Clean Energy Wire",    "https://www.cleanenergywire.org/rss.xml", 2),
    ("eu_energypost","Energy Post EU",       "https://energypost.eu/feed/", 3),
    ("eu_pvmag",     "PV Magazine Global",   "https://www.pv-magazine.com/feed/", 1),
    ("eu_windpower", "WindPower Monthly",    "https://www.windpowermonthly.com/rss", 3),
    ("eu_montel",    "Montel News",          "https://montelnews.com/rss", 3),
    ("eu_ember",     "Ember Climate",        "https://ember-climate.org/feed/", 3),
]
for sid, name, url, tier in _EU_RSS:
    _add(sid, name, "rss", "europe", "re_industry", tier, url=url)
for key, q in [("eu_policy","European Union renewable energy directive"),
               ("eu_grid","Europe electricity grid storage"),
               ("eu_industry","Europe solar wind manufacturing factory"),
               ("eu_carbon","Europe carbon market emissions"),
               ("eu_geo","Europe energy security supply")]:
    _add(f"eu_gdelt_{key}", f"GDELT: {q[:38]}", "gdelt", "europe", "geopolitics", 2, query=q)

# ═══ AFRICA — target ≥60 ══════════════════════════════════════════════════════
_AF_COUNTRIES = [
    "South Africa","Egypt","Morocco","Kenya","Nigeria","Ethiopia","Tanzania",
    "Ghana","Algeria","Tunisia","Namibia","Zambia","Zimbabwe","Senegal",
    "Ivory Coast","Mozambique","Angola","DR Congo","Botswana","Uganda",
    "Rwanda","Mauritania","Libya","Sudan","Cameroon",
]
for cname in _AF_COUNTRIES:
    sid = "af_" + cname.lower().replace(" ", "_")
    _add(sid, f"{cname} energy", "gnews", "africa", "re_industry",
         2 if cname in ("South Africa","Egypt","Morocco","Kenya","Nigeria") else 3,
         query=f"{cname} (solar OR wind OR renewable OR electricity OR power project)", gl="US")
_AF_THEMES = [
    ("jetp_sa",     'South Africa JETP just energy transition', 2),
    ("eskom",       'Eskom load shedding grid', 2),
    ("h2_namibia",  'Namibia green hydrogen Hyphen', 3),
    ("h2_morocco",  'Morocco green hydrogen ammonia', 3),
    ("h2_egypt",    'Egypt green hydrogen Suez', 3),
    ("desert_power",'Sahara desert solar power export Europe', 3),
    ("minigrid",    'mini-grid off-grid solar Africa', 3),
    ("geothermal_ke",'Kenya geothermal Olkaria', 3),
    ("cobalt_drc",  'DRC cobalt mining supply', 2),
    ("af_lithium",  'Zimbabwe lithium mining export', 3),
    ("af_finance",  'Africa renewable energy financing AfDB World Bank', 3),
    ("af_grid",     'Africa power pool interconnection transmission', 3),
    ("af_ipp",      'independent power producer Africa PPA signed', 3),
    ("af_battery",  'battery storage Africa project', 3),
    ("af_china",    'China Belt Road energy Africa investment', 3),
]
for key, q, tier in _AF_THEMES:
    _add(f"af_theme_{key}", f"AF: {q[:38]}", "gnews", "africa", "policy", tier, query=q, gl="US")
_AF_RSS = [
    ("af_esi",      "ESI Africa",          "https://www.esi-africa.com/feed/", 2),
    ("af_energy_portal","Africa Energy Portal", "https://africa-energy-portal.org/rss.xml", 3),
]
for sid, name, url, tier in _AF_RSS:
    _add(sid, name, "rss", "africa", "re_industry", tier, url=url)
for key, q in [("af_solar","solar project Africa megawatt"),
               ("af_wind","wind farm Africa"),
               ("af_policy","Africa energy policy electricity reform"),
               ("af_mining","Africa critical minerals mining lithium cobalt"),
               ("af_geo","Africa energy investment China Gulf"),
               ("af_h2","green hydrogen Africa")]:
    _add(f"af_gdelt_{key}", f"GDELT: {q[:38]}", "gdelt", "africa", "geopolitics", 2, query=q)

# ═══ NORTH AMERICA — target ≥60 ═══════════════════════════════════════════════
_NA_GEO = [
    ("us","United States",2),("ca","Canada",3),("mx","Mexico",3),
    ("us_ca","California",2),("us_tx","Texas",2),("us_ny","New York state",3),
    ("us_fl","Florida",3),("us_az","Arizona",3),("us_nv","Nevada",3),
    ("us_ga","Georgia",3),("us_oh","Ohio",3),("us_il","Illinois",3),
]
for key, gname, tier in _NA_GEO:
    _add(f"na_{key}", f"{gname} energy", "gnews", "north_america", "re_industry", tier,
         query=f"{gname} (solar OR wind OR renewable OR battery storage OR grid)", gl="US")
_NA_THEMES = [
    ("ira",        'Inflation Reduction Act clean energy tax credit', 1),
    ("solar_tariff','", 'US solar tariff AD CVD Southeast Asia', 1),
    ("ercot",      'ERCOT Texas grid prices', 3),
    ("caiso",      'CAISO California grid solar curtailment', 3),
    ("ferc",       'FERC transmission interconnection ruling', 3),
    ("queue",      'interconnection queue solar storage US', 3),
    ("us_mfg",     'US solar manufacturing factory gigawatt', 2),
    ("us_offshore",'US offshore wind project', 3),
    ("us_battery", 'US battery storage deployment record', 2),
    ("us_nuclear", 'US nuclear SMR restart', 3),
    ("us_data_ctr",'data center power demand US utilities', 2),
    ("us_fed",     'Federal Reserve rate decision', 2),
    ("us_china_tr",'US China trade tariff section 301 solar', 1),
    ("uflpa",      'UFLPA solar polysilicon customs detention', 2),
    ("us_permits", 'US renewable permitting public lands', 3),
    ("ca_minerals",'Canada critical minerals lithium', 3),
    ("mx_energy",  'Mexico energy reform renewable', 3),
    ("us_doe",     'Department of Energy loan grant award', 3),
    ("us_ev",      'US EV sales battery plant', 3),
    ("ptc_itc",    'production tax credit investment tax credit guidance', 3),
]
for key, q, tier in _NA_THEMES:
    key = key.replace("','", "")
    _add(f"na_theme_{key}", f"NA: {q[:38]}", "gnews", "north_america", "policy", tier, query=q, gl="US")
_NA_RSS = [
    ("na_utilitydive","Utility Dive",        "https://www.utilitydive.com/feeds/news/", 2),
    ("na_canary",     "Canary Media",        "https://www.canarymedia.com/rss.xml", 2),
    ("na_rew",        "Renewable Energy World","https://www.renewableenergyworld.com/feed/", 3),
    ("na_cleantechnica","CleanTechnica",     "https://cleantechnica.com/feed/", 2),
    ("na_eia",        "EIA Today in Energy", "https://www.eia.gov/rss/todayinenergy.xml", 2),
    ("na_solarbuilder","Solar Builder",      "https://solarbuildermag.com/feed/", 3),
]
for sid, name, url, tier in _NA_RSS:
    _add(sid, name, "rss", "north_america", "re_industry", tier, url=url)
for key, q in [("na_solar","United States solar policy tariff"),
               ("na_grid","US grid reliability storage"),
               ("na_trade","US solar import tariff trade"),
               ("na_invest","clean energy investment United States billion")]:
    _add(f"na_gdelt_{key}", f"GDELT: {q[:38]}", "gdelt", "north_america", "geopolitics", 2, query=q)

# ═══ SOUTH AMERICA — target ≥60 ═══════════════════════════════════════════════
_SA_COUNTRIES = [
    "Brazil","Chile","Argentina","Colombia","Peru","Uruguay","Paraguay",
    "Bolivia","Ecuador","Venezuela","Guyana","Suriname",
]
for cname in _SA_COUNTRIES:
    sid = "sa_" + cname.lower()
    _add(sid, f"{cname} energy", "gnews", "south_america", "re_industry",
         2 if cname in ("Brazil","Chile","Argentina") else 3,
         query=f"{cname} (solar OR wind OR renewable OR energia OR power project)", gl="US")
_SA_THEMES = [
    ("lithium_triangle",'lithium triangle Chile Argentina Bolivia', 2),
    ("atacama',",       'Atacama solar Chile', 3),
    ("br_auction",      'Brazil energy auction leilão', 2),
    ("br_wind",         'Brazil wind northeast', 3),
    ("br_solar_dg",     'Brazil distributed generation solar', 3),
    ("h2_chile",        'Chile green hydrogen Magallanes', 3),
    ("h2_brazil",       'Brazil green hydrogen Ceará', 3),
    ("copper_cl",       'Chile Peru copper production', 2),
    ("hydro_drought",   'Brazil hydropower drought reservoir', 3),
    ("ar_vaca",         'Argentina energy Vaca Muerta lithium', 3),
    ("co_transition",   'Colombia energy transition wind Guajira', 3),
    ("sa_grid",         'South America transmission interconnection', 3),
    ("sa_china_inv",    'China investment Latin America energy mining', 2),
    ("br_industry",     'Brazil solar module manufacturing tariff', 3),
    ("sa_finance",      'Latin America renewable project finance IDB', 3),
]
for key, q, tier in _SA_THEMES:
    key = key.replace("',", "")
    _add(f"sa_theme_{key}", f"SA: {q[:38]}", "gnews", "south_america", "supply_chain", tier, query=q, gl="US")
_SA_RSS = [
    ("sa_pvmag_latam","PV Magazine LatAm", "https://www.pv-magazine-latam.com/feed/", 3),
]
for sid, name, url, tier in _SA_RSS:
    _add(sid, name, "rss", "south_america", "re_industry", tier, url=url)
for key, q in [("sa_solar","solar wind project Brazil Chile Argentina"),
               ("sa_lithium","lithium mining South America export"),
               ("sa_policy","Latin America energy policy auction"),
               ("sa_hydro","hydropower South America drought"),
               ("sa_geo","Latin America energy investment geopolitics"),
               ("sa_h2","green hydrogen Latin America"),
               ("sa_copper","copper supply Chile Peru disruption"),
               ("sa_trade","Brazil solar import tariff China")]:
    _add(f"sa_gdelt_{key}", f"GDELT: {q[:38]}", "gdelt", "south_america", "geopolitics", 2, query=q)

# ═══ OCEANIA — target ≥60 ═════════════════════════════════════════════════════
_OC_GEO = [
    ("au","Australia",2),("au_nsw","New South Wales",3),("au_qld","Queensland",3),
    ("au_vic","Victoria Australia",3),("au_sa","South Australia",3),
    ("au_wa","Western Australia",3),("au_tas","Tasmania",3),
    ("nz","New Zealand",3),("pg","Papua New Guinea",3),("fj","Fiji Pacific islands",3),
]
for key, gname, tier in _OC_GEO:
    _add(f"oc_{key}", f"{gname} energy", "gnews", "oceania", "re_industry", tier,
         query=f"{gname} (solar OR wind OR renewable OR battery OR grid)", gl="AU")
_OC_THEMES = [
    ("aemo",       'AEMO electricity market NEM', 2),
    ("rooftop_au", 'Australia rooftop solar record', 3),
    ("big_battery",'Australia big battery Tesla Neoen', 2),
    ("snowy",      'Snowy 2.0 pumped hydro', 3),
    ("au_h2",      'Australia green hydrogen Gladstone', 3),
    ("au_lithium", 'Australia lithium mine Pilbara', 2),
    ("au_rare",    'Australia rare earths Lynas', 3),
    ("au_cis",     'Capacity Investment Scheme auction Australia', 3),
    ("au_transm",  'Australia transmission Marinus VNI', 3),
    ("au_coal_exit",'Australia coal plant closure', 3),
    ("au_offshore",'Australia offshore wind Gippsland', 3),
    ("au_solar_mfg",'Australia solar manufacturing SunShot', 3),
    ("nz_geo",     'New Zealand geothermal renewable', 3),
    ("pacific_cc", 'Pacific islands climate energy', 3),
    ("au_india",   'Australia India critical minerals trade', 2),
    ("au_export",  'Sun Cable Australia energy export', 3),
    ("au_gas",     'Australia LNG gas export east coast', 3),
    ("au_cop",     'Australia climate policy safeguard mechanism', 3),
    ("au_ev",      'Australia EV battery storage home', 3),
    ("au_grid_sec",'Australia grid security inertia', 3),
]
for key, q, tier in _OC_THEMES:
    _add(f"oc_theme_{key}", f"OC: {q[:38]}", "gnews", "oceania", "policy", tier, query=q, gl="AU")
_OC_RSS = [
    ("oc_reneweconomy","RenewEconomy",        "https://reneweconomy.com.au/feed/", 1),
    ("oc_pvmag_au",    "PV Magazine Australia","https://www.pv-magazine-australia.com/feed/", 2),
    ("oc_energy_matters","Energy Matters AU",  "https://www.energymatters.com.au/feed/", 3),
    ("oc_arena",       "ARENA news",           "https://arena.gov.au/feed/", 3),
]
for sid, name, url, tier in _OC_RSS:
    _add(sid, name, "rss", "oceania", "re_industry", tier, url=url)
for key, q in [("oc_solar","Australia solar wind project"),
               ("oc_minerals","Australia lithium rare earth critical minerals"),
               ("oc_policy","Australia energy policy market"),
               ("oc_h2","green hydrogen Australia"),
               ("oc_grid","Australia grid battery storage"),
               ("oc_trade","Australia energy export Asia")]:
    _add(f"oc_gdelt_{key}", f"GDELT: {q[:38]}", "gdelt", "oceania", "geopolitics", 2, query=q)

# ═══ GLOBAL / CROSS-CUTTING ═══════════════════════════════════════════════════
_GLOBAL = [
    ("gl_iea_rss",   "IEA News",          "rss",   "https://www.iea.org/api/rss/news.xml", 2, ""),
    ("gl_irena",     "IRENA newsroom",    "gnews", "", 2, "site:irena.org"),
    ("gl_bnef",      "BloombergNEF",      "gnews", "", 2, "BloombergNEF renewable solar battery"),
    ("gl_woodmac",   "Wood Mackenzie RE", "gnews", "", 3, "Wood Mackenzie solar wind storage forecast"),
    ("gl_freight",   "Container freight", "gnews", "", 2, "container freight rates Red Sea shipping"),
    ("gl_oil",       "Oil markets",       "gnews", "", 2, "OPEC oil price decision"),
    ("gl_cop",       "UNFCCC / COP",      "gnews", "", 3, "COP climate negotiations finance"),
    ("gl_imf",       "IMF outlook",       "gnews", "", 3, "IMF world economic outlook"),
    ("gl_perovskite","Perovskite R&D",    "gnews", "", 3, "perovskite solar efficiency record"),
    ("gl_battery_tech","Battery tech",    "gnews", "", 2, "solid state sodium ion battery breakthrough"),
    ("gl_grid_ai",   "AI power demand",   "gnews", "", 2, "AI data center electricity demand"),
    ("gl_minerals",  "Critical minerals", "gnews", "", 2, "critical minerals supply chain IEA"),
    ("gl_carbon",    "Carbon markets",    "gnews", "", 3, "voluntary carbon market price"),
    ("gl_climate_x", "Extreme weather grids","gnews","", 3, "extreme weather power grid blackout"),
    ("gl_gdelt_energy","GDELT: energy transition global","gdelt","",2,"energy transition investment global"),
    ("gl_gdelt_solar","GDELT: solar manufacturing global","gdelt","",2,"solar manufacturing capacity expansion"),
    ("gl_gdelt_geo", "GDELT: energy geopolitics","gdelt","",2,"energy geopolitics sanctions supply"),
]
for sid, name, stype, url, tier, q in _GLOBAL:
    _add(sid, name, stype, "global", "macro", tier, url=url, query=q, gl="US")
# Structured global APIs (Phase C/D fetchers in neuron.py)
for key, name in [("openmeteo","Open-Meteo irradiance/wind forecasts"),
                  ("comtrade","UN Comtrade India solar HS imports"),
                  ("worldbank","World Bank indicators"),
                  ("gdelt_vol","GDELT volume timelines (novelty radar)"),
                  ("yf_comm","Yahoo Finance commodities/FX"),
                  ("yf_glob","Yahoo Finance global RE equities"),
                  ("irena_cap","IRENA installed RE capacity by country (PxWeb)")]:
    _add(f"gl_api_{key}", name, "api", "global", "official_data", 1)


# ═══ REGIONAL DEPTH PACKS — second ring of standing queries (tier 3) ══════════
_DEPTH = {
 "asia": [
    ("mn","Mongolia coal renewable"),("om","Oman green hydrogen"),("kw","Kuwait solar"),
    ("bh","Bahrain energy"),("jo","Jordan solar wind"),("np","Nepal hydropower India export"),
    ("bt","Bhutan hydro India"),("mm","Myanmar power crisis"),("kh","Cambodia solar"),
    ("la","Laos hydropower export"),("cn_bess","China grid energy storage gigafactory"),
    ("cn_hydro","China hydropower Tibet Yarlung"),("jp_pero","Japan perovskite solar Sekisui"),
    ("kr_nuc","Korea nuclear export reactor"),("iran_energy","Iran energy sanctions oil"),
 ],
 "europe": [
    ("cz","Czech energy nuclear solar"),("hu","Hungary solar battery"),("bg","Bulgaria renewable"),
    ("hr","Croatia renewable"),("rs","Serbia energy China"),("ch","Switzerland hydro solar"),
    ("sk","Slovakia energy"),("lt","Baltic states energy grid Russia"),
    ("eu_heat","Europe heat pump sales"),("eu_ev","Europe EV battery gigafactory"),
    ("eu_biome","Europe biomethane biogas"),("north_stream","Baltic North Sea energy infrastructure security"),
    ("eu_intercon","Channel interconnector UK Europe electricity"),
    ("eu_solar_imp","Europe solar import China inventory"),("uk_cfd","UK CfD auction offshore wind"),
    ("de_eeg","Germany EEG solar subsidy reform"),("es_pv","Spain solar PPA merchant"),
    ("it_agri","Italy agrivoltaics auction"),("pl_coal","Poland coal exit nuclear"),
    ("ua_grid","Ukraine grid attacks reconstruction"),
 ],
 "africa": [
    ("af_solar_home","solar home systems pay-as-you-go Africa"),
    ("af_gas","Africa gas pipeline Nigeria Morocco"),("af_dam","Grand Ethiopian Renaissance Dam"),
    ("af_sahel","Sahel solar electrification"),("af_redcorr","Lobito corridor minerals"),
    ("za_remi","South Africa REIPPP renewable auction"),("za_grid","South Africa transmission grid expansion"),
    ("eg_wind","Egypt wind Gulf of Suez"),("ma_xlinks","Morocco Xlinks UK power cable"),
    ("ke_offgrid","Kenya off-grid power Africa"),("ng_grid","Nigeria grid collapse power reform"),
    ("gh_energy","Ghana energy debt IPP"),("tz_lng","Tanzania LNG hydro"),
    ("af_uran","Niger Namibia uranium"),("af_solar_mfg","solar panel assembly factory Africa"),
 ],
 "north_america": [
    ("us_pjm","PJM capacity auction prices"),("us_miso","MISO grid queue"),
    ("us_nyiso","New York grid offshore"),("us_southeast","Georgia Carolinas solar utility"),
    ("us_hawaii","Hawaii renewable grid"),("us_puerto","Puerto Rico grid solar"),
    ("us_tribal","tribal lands solar DOE"),("us_agri","agrivoltaics US farmland solar"),
    ("us_recycling","solar panel recycling US"),("us_thin","First Solar thin film cadmium"),
    ("us_resi","US residential solar Sunrun Sunnova"),("us_community","community solar US state"),
    ("us_transm_perm","US transmission permitting reform grid"),("us_hydro","US hydropower relicensing"),
    ("us_geoth","enhanced geothermal Fervo US"),("us_fusion","fusion energy investment US"),
    ("ca_hydro","Hydro-Quebec BC Hydro export"),("mx_solar","Mexico solar auction CFE"),
    ("us_uslca","US solar supply chain traceability"),("us_grid_cyber","US grid cybersecurity attack"),
 ],
 "south_america": [
    ("br_grid","Brazil grid curtailment ONS"),("br_offshore","Brazil offshore wind law"),
    ("br_battery","Brazil battery storage auction"),("br_ethanol","Brazil ethanol sugarcane energy"),
    ("cl_grid","Chile transmission Kimal Lo Aguirre"),("cl_desal","Chile desalination mining solar"),
    ("ar_lithium","Argentina lithium salar investment"),("ar_renov","Argentina RenovAr renewable"),
    ("pe_energy","Peru energy auction solar"),("co_offshore","Colombia offshore wind auction"),
    ("ec_hydro","Ecuador hydropower blackout"),("uy_h2","Uruguay green hydrogen"),
    ("py_itaipu","Itaipu Paraguay Brazil power"),("bo_lithium","Bolivia lithium YLB"),
    ("ve_grid","Venezuela power grid"),("gy_oil","Guyana oil energy"),
    ("sa_evs","Latin America EV adoption"),("sa_carbon","Amazon carbon credits energy"),
    ("sa_mercosur","Mercosur trade energy"),("sa_drought","La Nina drought hydropower South America"),
    ("br_aneel","ANEEL Brazil regulator tariff"),("cl_cne","Chile CNE energy auction"),
    ("br_solar_mfg","Brazil solar module factory BYD"),("sa_transmission","Brazil transmission auction lot"),
    ("sa_wind_oem","wind turbine factory Brazil Nordex WEG"),
 ],
 "oceania": [
    ("au_rooftop_vpp","virtual power plant Australia VPP"),("au_evs","Australia EV uptake policy"),
    ("au_smelter","Tomago aluminium smelter renewable"),("au_greenmetal","green iron steel Australia"),
    ("au_hydro_tas","Tasmania hydro battery of the nation"),("au_solar_farm","Australia solar farm approved"),
    ("au_wind_farm","Australia wind farm construction"),("au_nem_reform","NEM market reform capacity"),
    ("au_network","Ausgrid Powerlink network investment"),("au_retail","Australia electricity retail prices"),
    ("au_uranium","Australia uranium mining policy"),("au_csiro","CSIRO GenCost renewable"),
    ("au_apvi","Australia PV institute rooftop data"),("nz_onslow","New Zealand Onslow pumped hydro"),
    ("nz_wind","New Zealand wind solar consent"),("pac_solar","Pacific islands solar microgrid"),
    ("au_critical_h","Australia hydrogen headstart"),("au_queensland_h2","Queensland hydrogen CQ-H2"),
    ("au_sun_cable","Sun Cable Darwin Singapore"),("au_battery_mfg","Australia battery manufacturing"),
 ],
}
for region, packs in _DEPTH.items():
    gl = "AU" if region == "oceania" else "US"
    for key, q in packs:
        _add(f"{region[:2]}_depth_{key}", f"{region[:2].upper()}+: {q[:36]}", "gnews",
             region, "re_industry", 3, query=q, gl=gl)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 21 — SOURCE EXPANSION  (target: ≥1000 total)
# Adds ~530 new sources: direct RSS, gnews, gdelt, api
# Organised by category; IDs are globally unique (p21_ prefix for new ones).
# ═══════════════════════════════════════════════════════════════════════════════

# ── P21-A: New direct RSS feeds — global specialist publications ───────────────
_P21_GLOBAL_RSS = [
    # Energy storage
    ("p21_en_storage",    "Energy Storage News",      "https://www.energy-storage.news/feed/",                          1),
    ("p21_ess_news",      "ESS News",                 "https://www.ess-news.com/feed/",                                  2),
    # Offshore wind
    ("p21_offshorewind",  "Offshore Wind Biz",        "https://www.offshorewind.biz/feed/",                             1),
    ("p21_renews",        "Renews.biz",               "https://renews.biz/feed/",                                        2),
    ("p21_offshoreeng",   "Offshore Energy",          "https://www.offshore-energy.biz/feed/",                          2),
    # Hydrogen
    ("p21_h2view",        "H2 View",                  "https://www.h2-view.com/news/all-news/feed/",                     1),
    ("p21_h2central",     "Hydrogen Central",         "https://hydrogen-central.com/feed/",                              2),
    ("p21_h2int",         "H2 International",         "https://www.h2-international.com/feed/",                          2),
    ("p21_h2insight",     "Hydrogen Insight",         "https://www.hydrogeninsight.com/feed/",                           1),
    # Recharge / Renewables Now
    ("p21_recharge",      "Recharge News",            "https://www.rechargenews.com/latest/feed/",                       1),
    ("p21_ren_now",       "Renewables Now",           "https://renewablesnow.com/feed/",                                 1),
    ("p21_ren_now_solar", "Renewables Now Solar",     "https://renewablesnow.com/news/solar/feed/",                      2),
    ("p21_ren_now_wind",  "Renewables Now Wind",      "https://renewablesnow.com/news/wind/feed/",                       2),
    ("p21_ren_now_h2",    "Renewables Now H2",        "https://renewablesnow.com/news/hydrogen/feed/",                   2),
    ("p21_ren_now_bess",  "Renewables Now Storage",   "https://renewablesnow.com/news/energy-storage/feed/",             2),
    # PV Magazine editions
    ("p21_pvmag_usa",     "PV Magazine USA",          "https://www.pv-magazine-usa.com/feed/",                          2),
    ("p21_pvmag_de",      "PV Magazine Germany",      "https://www.pv-magazine.de/feed/",                               3),
    ("p21_pvmag_fr",      "PV Magazine France",       "https://www.pv-magazine.fr/feed/",                               3),
    ("p21_pvmag_it",      "PV Magazine Italy",        "https://www.pv-magazine.it/feed/",                               3),
    ("p21_pvmag_es",      "PV Magazine Spain",        "https://www.pv-magazine.es/feed/",                               3),
    ("p21_pvmag_cn",      "PV Magazine China",        "https://www.pv-magazine-china.com/feed/",                        3),
    # Carbon / climate
    ("p21_carbon_brief",  "Carbon Brief",             "https://www.carbonbrief.org/feed/",                               2),
    ("p21_carbon_pulse",  "Carbon Pulse",             "https://carbon-pulse.com/feed/",                                  2),
    ("p21_clim_home",     "Climate Home News",        "https://www.climatechangenews.com/feed/",                         3),
    ("p21_inside_clim",   "Inside Climate News",      "https://insideclimatenews.org/feed/",                             3),
    ("p21_yale_e360",     "Yale E360",                "https://e360.yale.edu/feed",                                      3),
    # Finance / ESG
    ("p21_esg_dive",      "ESG Dive",                 "https://www.esgdive.com/feeds/news.rss",                          3),
    ("p21_enviro_fin",    "Environmental Finance",    "https://www.environmental-finance.com/content/news/rss.xml",      3),
    ("p21_greenbiz",      "GreenBiz",                 "https://www.greenbiz.com/rss.xml",                               3),
    # Power / utility
    ("p21_power_mag",     "Power Magazine",           "https://www.powermag.com/feed/",                                  2),
    ("p21_power_eng",     "Power Engineering Int'l",  "https://www.power-eng.com/rss/content/",                         3),
    ("p21_sol_pw_world",  "Solar Power World",        "https://www.solarpowerworldonline.com/feed/",                     2),
    ("p21_wind_pw_eng",   "Wind Power Engineering",   "https://www.windpowerengineering.com/feed/",                      3),
    ("p21_energypost",    "Energy Post Global",       "https://energypost.eu/feed/",                                     2),
    ("p21_re_world2",     "Renewable Energy World",   "https://www.renewableenergyworld.com/feed/",                      2),
    # Geopolitics / maritime
    ("p21_diplomat",      "The Diplomat",             "https://thediplomat.com/feed/",                                   2),
    ("p21_chatham",       "Chatham House",            "https://www.chathamhouse.org/feed",                               3),
    ("p21_geopol_mon",    "Geopolitical Monitor",     "https://www.geopoliticalmonitor.com/feed/",                       3),
    ("p21_splash",        "Splash 247 Maritime",      "https://splash247.com/feed/",                                     2),
    ("p21_hellenic_ship", "Hellenic Shipping News",   "https://www.hellenicshippingnews.com/rss-feeds/",                 2),
    # Asia sustainability
    ("p21_eco_biz",       "Eco-Business Asia",        "https://www.eco-business.com/news/rss/",                          2),
    ("p21_ren_asia",      "Renewables.Asia",          "https://renewables.asia/feed/",                                   2),
    # Africa energy
    ("p21_af_energy_biz", "Africa Energy Business",  "https://www.africa-energy.com/rss/",                              3),
    # BNEF blog
    ("p21_bnef_blog",     "BNEF Blog",                "https://about.bnef.com/blog/feed/",                               2),
    # Middle East
    ("p21_mees",          "MEES Energy",              "https://www.mees.com/rss",                                        3),
    ("p21_energywatch",   "EnergyWatch Nordics",      "https://energywatch.com/service/rss/",                            3),
    # India additions
    ("p21_in_powertoday", "Power Today India",        "https://www.powertoday.in/feed/",                                 3),
    ("p21_in_energyline", "EnergyLine India",         "https://www.energylineindia.com/feed/",                           3),
    ("p21_in_ppdigest",   "Power Peak Digest",        "https://powerpeakdigest.com/feed/",                               3),
    ("p21_in_pvind2",     "PV Magazine India",        "https://www.pv-magazine-india.com/feed/",                         1),
    ("p21_in_cleanmin",   "Clean Energy Min India",   "https://cleanmin.org/feed/",                                      3),
    # Academic / research
    ("p21_nat_energy",    "Nature Energy",            "https://www.nature.com/nenergy.rss",                              3),
    ("p21_joule_cell",    "Joule (Cell Press)",       "https://www.cell.com/joule/rss.xml",                              3),
    ("p21_irena_news",    "IRENA Newsroom",           "https://www.irena.org/rss/news",                                  2),
    # EIA
    ("p21_eia_rss2",      "EIA Today in Energy 2",   "https://www.eia.gov/rss/todayinenergy.xml",                       2),
]
for sid, name, url, tier in _P21_GLOBAL_RSS:
    region = "india" if "_in_" in sid else "global"
    cat    = "re_industry"
    _add(sid, name, "rss", region, cat, tier, url=url)

# ── P21-B: New India gnews — additional company trackers ──────────────────────
_P21_IN_COMPANIES = [
    ("greenko_t",      "Greenko renewable storage",               2),
    ("azure_t",        "Azure Power solar India",                 2),
    ("jsw_energy_t",   "JSW Energy renewable hydrogen",           2),
    ("torrent_t",      "Torrent Power renewable",                 3),
    ("cesc_t",         "CESC renewable generation",               3),
    ("tpddl_t",        "Tata Power Delhi renewable",              3),
    ("adani_es_t",     "Adani Energy Solutions transmission",     2),
    ("powergrid_t",    "Power Grid Corporation India transmission",2),
    ("bse_re_t",       "BSE renewable energy listing IPO",        3),
    ("mspl_t",         "MSPL solar India",                        3),
    ("amp_india_t",    "AMP Energy India solar",                  3),
    ("opal_t",         "Opal renewable energy India",             3),
    ("ayana_t",        "Ayana Renewable Power India",             3),
    ("eden_t",         "Eden Renewables India",                   3),
    ("clp_t",          "CLP India wind solar",                    3),
    ("fortum_t",       "Fortum India solar",                      3),
    ("scatec_t",       "Scatec solar India",                      3),
    ("engie_in_t",     "Engie India renewable",                   3),
    ("enel_in_t",      "Enel India green power",                  3),
    ("softbank_in_t",  "SoftBank Energy India",                   3),
    ("bny_in_t",       "Blackrock renewable India",               3),
    ("iex2_t",         "IEX power exchange real time market",     2),
    ("pxil2_t",        "PXIL power exchange India",               3),
    ("cppib_in_t",     "CPPIB Canada Pension renewable India",    3),
    ("leap_in_t",      "Leap Green Energy India",                 3),
    ("sembcorp_t",     "Sembcorp India renewable",                3),
    ("orix_t",         "ORIX India renewable",                    3),
    ("continuum_t",    "Continuum Green Energy India",            3),
    ("mahindra_re_t",  "Mahindra Susten renewable India",         3),
    ("sterlite_t",     "Sterlite Power transmission",             3),
    ("adani_trnx_t",   "Adani Green Energy transmission expansion",2),
    ("waaree2_t",      "Waaree Energies module export",           2),
    ("vikramsol2_t",   "Vikram Solar TOPCon cell",                3),
    ("saatvik2_t",     "Saatvik Green Energy cell manufacturing", 1),
    ("premier2_t",     "Premier Energies IPO cell production",    2),
    ("goldi2_t",       "Goldi Solar module India",                3),
    ("axitec_t",       "Axitec solar India import",               3),
    ("first_solar_in", "First Solar India thin film",             3),
    ("canadian_in",    "Canadian Solar India project",            3),
    ("longi_in",       "LONGi India solar module",                2),
    ("jinko_in",       "JinkoSolar India module",                 2),
    ("trina_in",       "Trina Solar India panel",                 2),
]
for key, q, tier in _P21_IN_COMPANIES:
    _add(f"p21_in_co_{key}", f"IN co: {q[:40]}", "gnews", "india", "re_industry", tier, query=q)

# ── P21-C: New India gnews — sector/theme depth ────────────────────────────────
_P21_IN_THEMES = [
    # Grid / system operation
    ("nldc_grid",     "NLDC real time grid dispatch India",          2),
    ("rldc_grid",     "RLDC regional load dispatch India",           3),
    ("grid_freq",     "India grid frequency 50Hz ancillary",         3),
    ("vgf_scheme",    "viability gap funding solar India SECI",      2),
    ("rts_tender",    "round-the-clock renewable tender India",      2),
    ("hybrid_tender", "solar wind hybrid tender India",              1),
    ("fdre_tender",   "firm dispatchable renewable energy India",    2),
    ("peak_power",    "peak power demand MW India record",           2),
    ("demandside",    "demand response flexibility India utility",   3),
    # Manufacturing
    ("acc_batt",      "ACC battery cell PLI scheme India production",2),
    ("inverter_mfg",  "solar inverter manufacturing India",          3),
    ("tracker_mfg",   "solar tracker manufacturer India",            3),
    ("cable_re",      "power cable manufacturer renewable India",    3),
    ("transformer_mfg","transformer manufacturer India power grid",  3),
    ("semiconductor_in","semiconductor India solar cell wafer fab",  3),
    ("electrolysis",  "electrolyzer manufacturer India green hydrogen",3),
    # Financing
    ("ireda_ncd",     "IREDA bond NCD green financing India",        2),
    ("pfc_bond",      "PFC REC green bond India",                    3),
    ("sbi_green",     "SBI green loan renewable India",              3),
    ("mufg_re_in",    "MUFG Japan renewable project finance India",  3),
    ("adb_india_re",  "ADB Asian Development Bank India renewable",  3),
    ("ifc_india_re",  "IFC World Bank India clean energy loan",      3),
    ("masala_bond",   "masala bond renewable energy India",          3),
    ("yieldco_in",    "InvIT infrastructure trust renewable India",  2),
    # Policy/regulatory
    ("must_run",      "must run status renewable power India",       3),
    ("c_and_i",       "commercial industrial open access solar India",2),
    ("banking_energy","energy banking policy India",                 3),
    ("wheeling",      "wheeling charges renewable cross-state India",3),
    ("sgst_waiver",   "GST waiver solar module India",               3),
    ("dcr",           "domestic content requirement solar India",    2),
    ("repowering",    "wind repowering India old turbines",          3),
    ("solar_park",    "solar park SECI NTPC development India",      2),
    ("ultra_mega",    "ultra mega renewable energy park India",      2),
    ("green_tariff",  "green tariff open access renewable India",    3),
    ("carbon_tax_in", "carbon tax emission India budget",            3),
    ("ets_india",     "emissions trading scheme India launch 2026",  2),
    ("pac_scheme",    "perform achieve trade PAT energy scheme India",3),
    ("beestar",       "BEE star rating solar equipment India",       3),
    # Trade / supply chain
    ("antidumping_in","anti-dumping duty solar cells India",         2),
    ("pvx_price",     "solar PV module spot price India dollar",     1),
    ("tracker_import","solar tracker import duty India",             3),
    ("steel_re",      "steel galvanized structure renewable India",  3),
    ("copper_cable",  "copper price India cable cost renewable",     3),
    # Technology
    ("perovskite_in", "perovskite solar India research lab",         3),
    ("bifacial_re",   "bifacial solar module yield India",           3),
    ("topcon_cell",   "TOPCon solar cell efficiency India",          3),
    ("hjt_india",     "heterojunction HJT solar cell India",         3),
    ("agri_solar_in", "agrivoltaic agriculture solar India pilot",   3),
    ("floatpv_in",    "floating solar PV India MW tender",           3),
    ("vanadium_in",   "vanadium flow battery India storage",         3),
    ("compressed_air","compressed air energy storage India",         3),
    ("pumped_hydro",  "pumped storage hydro India 2026 MW",          2),
    ("gravity_store", "gravity energy storage India",                3),
    # Demand sectors
    ("steelgreen_in", "green steel hydrogen DRI India",              2),
    ("cementgreen",   "green cement renewable India factory",        3),
    ("datacentre_in", "data centre power renewable India MW",        2),
    ("ammonia_green", "green ammonia India export port",             2),
    ("methanol_green","green methanol India",                        3),
    # Regional / state (additional states)
    ("jk_re",         "Jammu Kashmir solar wind renewable",          3),
    ("ne_re",         "Northeast India renewable hydro solar",       3),
    ("island_re",     "Andaman Lakshadweep island renewable India",  3),
    ("coal_belt_re",  "coal region Jharkhand Odisha renewable India",3),
]
for key, q, tier in _P21_IN_THEMES:
    _add(f"p21_in_th_{key}", f"IN th: {q[:40]}", "gnews", "india", "policy", tier, query=q)

# Additional India GDELT standing queries
_P21_IN_GDELT = [
    ("bess_in",       "battery storage BESS India megawatt project"),
    ("h2_in2",        "green hydrogen India port ammonia export"),
    ("tender_in",     "solar wind tender auction India SECI NTPC MW"),
    ("discom_in",     "DISCOM payment dues renewable generator India"),
    ("mfg_in",        "solar manufacturing gigawatt factory India PLI"),
    ("grid_in2",      "transmission grid renewable curtailment India"),
    ("fin_in",        "green finance bond loan renewable India billion"),
    ("policy_in2",    "renewable energy policy amendment India ministry"),
    ("trade_in2",     "solar module import export duty India China"),
    ("demand_in",     "electricity demand peak India summer GW"),
]
for key, q in _P21_IN_GDELT:
    _add(f"p21_in_gd_{key}", f"GDELT: {q[:38]}", "gdelt", "india", "re_industry", 2, query=q)

# ── P21-D: New Asia sources ────────────────────────────────────────────────────
_P21_ASIA_COUNTRIES = [
    ("AF","Afghanistan",3),("NP","Nepal",3),("MM","Burma Myanmar",3),
    ("KH","Cambodia",3), ("LA","Laos",3),  ("BN","Brunei",3),
    ("MN","Mongolia",3), ("GE","Georgia",3),("AM","Armenia",3),
    ("AZ","Azerbaijan",3),("OM","Oman",3), ("YE","Yemen",3),
    ("JO","Jordan",3),   ("LB","Lebanon",3),("IQ","Iraq",3),
    ("SY","Syria",3),    ("KW","Kuwait",3), ("BH","Bahrain",3),
    ("TM","Turkmenistan",3),("TJ","Tajikistan",3),("KG","Kyrgyzstan",3),
]
for gl, cname, tier in _P21_ASIA_COUNTRIES:
    _add(f"p21_as_{gl.lower()}", f"{cname} energy", "gnews", "asia", "re_industry", tier,
         query=f"{cname} (solar OR wind OR renewable OR electricity OR energy project)", gl="US")

_P21_ASIA_THEMES = [
    ("china_perovskite",  "China perovskite solar commercialisation", 2),
    ("china_hjt",         "China HJT TOPCon solar cell factory", 2),
    ("china_bess_export", "China battery CATL BESS export overseas", 2),
    ("china_wind_float",  "China floating offshore wind project GW", 3),
    ("china_h2_pipeline", "China hydrogen pipeline west east", 3),
    ("china_nuclear",     "China nuclear power reactor AP1000", 3),
    ("china_grid_reform", "China electricity market reform spot price", 2),
    ("china_coal_cap",    "China coal power cap phaseout 2035", 3),
    ("japan_gx",          "Japan GX green transformation policy bond", 2),
    ("japan_smr",         "Japan small modular reactor SMR", 3),
    ("japan_ammonia",     "Japan ammonia cofiring power plant", 2),
    ("korea_cf100",       "Korea carbon free energy RE100", 3),
    ("korea_bess",        "Korea battery storage ESS fire safety", 3),
    ("taiwan_offshore",   "Taiwan offshore wind tender Changfang", 2),
    ("taiwan_solar",      "Taiwan rooftop solar agrivoltaic", 3),
    ("vietnam_pdp8",      "Vietnam power development plan PDP8 LNG", 2),
    ("vietnam_just_t",    "Vietnam just energy transition JETP", 2),
    ("indonesia_ets",     "Indonesia emissions trading carbon ETS", 2),
    ("indonesia_geo",     "Indonesia geothermal energy development", 3),
    ("ph_offshore",       "Philippines offshore wind tender PNOC", 2),
    ("ph_battery",        "Philippines battery storage island grid", 3),
    ("th_solar_farm",     "Thailand floating solar reservoir project", 3),
    ("my_re100",          "Malaysia renewable energy MIDA RE100", 3),
    ("sg_re_import",      "Singapore renewable energy import cable", 2),
    ("sg_h2_hub",         "Singapore hydrogen hub bunkering port", 2),
    ("kz_solar_wind",     "Kazakhstan solar wind steppe renewable", 3),
    ("uz_solar_project",  "Uzbekistan solar wind auction GW", 3),
    ("pak_re_tariff",     "Pakistan renewable energy tariff NEPRA", 3),
    ("bd_solar_rooftop",  "Bangladesh solar rooftop rural mini-grid", 3),
    ("gulf_solar_record", "Saudi UAE Qatar solar tariff record low", 2),
    ("neom_h2",           "NEOM green hydrogen ammonia Saudi Arabia", 2),
    ("uae_masdar",        "Masdar UAE renewable project overseas", 2),
    ("israel_solar",      "Israel solar storage grid", 3),
    ("turkey_wind",       "Turkey wind solar auction MW", 3),
    ("asean_interconnect","ASEAN power grid interconnection APAEC", 2),
    ("asia_datacenter",   "data centre power renewable Asia Singapore Japan", 2),
    ("asia_copper",       "copper supply demand Asia grid EV battery", 2),
    ("asia_ship_green",   "green shipping fuel Asia methanol ammonia LNG", 2),
    ("asia_ev_battery",   "Asia EV battery supply chain cobalt nickel", 2),
]
for key, q, tier in _P21_ASIA_THEMES:
    _add(f"p21_as_th_{key}", f"AS th: {q[:40]}", "gnews", "asia", "re_industry", tier, query=q, gl="US")

_P21_ASIA_RSS = [
    ("p21_as_renew_asia", "Renewables.Asia",          "https://renewables.asia/feed/",        2),
    ("p21_as_eco_biz",    "Eco-Business Asia",        "https://www.eco-business.com/news/rss/",2),
    ("p21_as_pvtech_bess","PV Tech Storage",          "https://www.pv-tech.org/category/storage/feed/", 2),
    ("p21_as_taiyang2",   "Taiyang News Cell",        "https://taiyangnews.info/category/technology/feed/", 3),
]
for sid, name, url, tier in _P21_ASIA_RSS:
    _add(sid, name, "rss", "asia", "re_industry", tier, url=url)

_P21_ASIA_GDELT = [
    ("as_bess",     "battery storage Asia China deployment gigawatt"),
    ("as_h2_exp",   "green hydrogen Asia export port ammonia"),
    ("as_offshore2","offshore wind Asia Pacific tender auction"),
    ("as_supply2",  "solar supply chain wafer module Asia China"),
    ("as_trade2",   "solar trade tariff US Asia Vietnam Cambodia"),
    ("as_grid2",    "power grid Asia electricity market reform"),
    ("as_mineral2", "critical mineral lithium cobalt Asia China supply"),
    ("as_ev2",      "electric vehicle battery Asia demand growth"),
]
for key, q in _P21_ASIA_GDELT:
    _add(f"p21_as_gd_{key}", f"GDELT: {q[:38]}", "gdelt", "asia", "geopolitics", 2, query=q)

# ── P21-E: New Europe sources ──────────────────────────────────────────────────
_P21_EU_COUNTRIES = [
    ("ME","Montenegro"),("MK","North Macedonia"),("AL","Albania"),
    ("XK","Kosovo"),    ("BA","Bosnia Herzegovina"),("MD","Moldova"),
    ("BY","Belarus"),   ("IS","Iceland"),("LV","Latvia"),
    ("EE","Estonia"),   ("LT","Lithuania"),("MO","Monaco"),
    ("LU","Luxembourg"),("SI","Slovenia"),("CY","Cyprus"),("MT","Malta"),
]
for gl, cname in _P21_EU_COUNTRIES:
    _add(f"p21_eu_{gl.lower()}", f"{cname} energy", "gnews", "europe", "re_industry", 3,
         query=f"{cname} (solar OR wind OR renewable OR grid OR power)", gl="US")

_P21_EU_THEMES = [
    ("eu_dsm",          "EU demand side flexibility smart grid", 3),
    ("eu_agg",          "EU aggregator virtual power plant demand response", 3),
    ("eu_ppa",          "corporate power purchase agreement PPA Europe", 2),
    ("eu_hydrogen_net", "European hydrogen backbone pipeline network", 2),
    ("eu_nzia_tender",  "NZIA auction European solar wind manufacturing tender", 2),
    ("eu_cfd_offshore", "contracts for difference CfD offshore wind Europe", 2),
    ("eu_interconnect2","electricity interconnector cable Europe upgrade", 2),
    ("eu_perovskite",   "perovskite solar Europe research commercialise", 3),
    ("eu_agri_pv",      "agrivoltaics agri-PV Europe approval", 3),
    ("eu_community_en", "community energy cooperative Europe citizen", 3),
    ("eu_storage_gwh",  "Europe grid battery storage GWh project", 2),
    ("eu_grid_invest",  "European grid investment TSO upgrade billion", 2),
    ("eu_solar_inst",   "Europe solar installation rooftop commercial GW", 2),
    ("uk_offshore",     "UK offshore wind CfD Hornsea project", 2),
    ("uk_gbis",         "UK Great British Insulation Scheme heat pump", 3),
    ("uk_nuclear",      "UK nuclear Sizewell Hinkley new build", 3),
    ("de_h2_import",    "Germany hydrogen import pipeline Morocco", 3),
    ("de_solar_record", "Germany solar record generation GW", 2),
    ("de_wind_north",   "Germany North Sea offshore wind expansion", 2),
    ("fr_nuclear_rerun","France nuclear reactor restart EDF", 2),
    ("fr_solar_agri",   "France agrivoltaics AO/FV auction", 3),
    ("es_solar_ppa",    "Spain solar merchant PPA unsubsidised GW", 2),
    ("es_battery",      "Spain battery storage BESS project GWh", 3),
    ("it_south_pv",     "Italy southern solar zone GW saturation", 3),
    ("pl_offshore",     "Poland offshore Baltic wind tender", 3),
    ("nl_wind_storm",   "Netherlands offshore wind Borssele IJmuiden", 3),
    ("nordics_price",   "Nordic electricity price winter negative", 2),
    ("eu_flexibility",  "EU electricity market flexibility reform capacity", 2),
    ("eu_critical_raw", "EU critical raw materials act lithium cobalt", 2),
    ("eu_deforestation","EU deforestation regulation biomass bioenergy", 3),
    ("eu_methane_reg",  "EU methane regulation gas import LNG", 3),
    ("turkey_export",   "Turkey solar wind electricity export Balkans", 3),
    ("balkans_energy",  "Western Balkans energy community renewable", 3),
    ("ua_rebuild",      "Ukraine energy infrastructure rebuild solar wind", 2),
]
for key, q, tier in _P21_EU_THEMES:
    _add(f"p21_eu_th_{key}", f"EU th: {q[:40]}", "gnews", "europe", "policy", tier, query=q, gl="US")

_P21_EU_RSS = [
    ("p21_eu_re_news",    "Renewables Now EU",        "https://renewablesnow.com/news/europe/feed/",  2),
    ("p21_eu_energypost2","Energy Post EU",           "https://energypost.eu/feed/",                  2),
    ("p21_eu_ember2",     "Ember Climate Blog",       "https://ember-climate.org/feed/",              3),
    ("p21_eu_agora",      "Agora Energiewende",       "https://www.agora-energiewende.de/en/feed/",   3),
    ("p21_eu_recharge2",  "Recharge Wind",            "https://www.rechargenews.com/wind/feed/",      2),
    ("p21_eu_offshwind",  "Offshore Wind EU",         "https://www.offshorewind.biz/region/europe/feed/", 2),
]
for sid, name, url, tier in _P21_EU_RSS:
    _add(sid, name, "rss", "europe", "re_industry", tier, url=url)

_P21_EU_GDELT = [
    ("eu_offshore2",  "offshore wind Europe North Sea auction tender"),
    ("eu_h2_pipe",    "European hydrogen pipeline import Africa Gulf"),
    ("eu_bess2",      "battery storage Europe grid GWh project"),
    ("eu_solar2",     "solar energy Europe record capacity GW"),
    ("eu_price",      "electricity price Europe market reform"),
    ("eu_heat",       "heat pump Europe sales installation"),
]
for key, q in _P21_EU_GDELT:
    _add(f"p21_eu_gd_{key}", f"GDELT: {q[:38]}", "gdelt", "europe", "geopolitics", 2, query=q)

# ── P21-F: New Africa sources ──────────────────────────────────────────────────
_P21_AF_COUNTRIES = [
    "Djibouti","Eritrea","Somalia","Comoros","Malawi","Lesotho","Eswatini",
    "Gabon","Republic of Congo","Central African Republic","Chad","Niger",
    "Burkina Faso","Mali","Guinea","Sierra Leone","Liberia","Togo","Benin",
    "Cape Verde","São Tomé and Príncipe","Equatorial Guinea","Burundi","South Sudan",
]
for cname in _P21_AF_COUNTRIES:
    sid = "p21_af_" + cname.lower().replace(" ","_").replace("ã","a").replace("é","e")
    _add(sid, f"{cname} energy", "gnews", "africa", "re_industry", 3,
         query=f"{cname} (solar OR electricity OR renewable OR mini-grid OR power)", gl="US")

_P21_AF_THEMES = [
    ("af_solar_farm2",   "utility scale solar farm Africa MW tender",       2),
    ("af_windfarm2",     "wind farm Africa coastal project MW",              2),
    ("af_offgrid2",      "off-grid solar home system Africa rural electrification",3),
    ("af_bess2",         "battery storage Africa project mini-grid BESS",   3),
    ("af_h2_export",     "green hydrogen export Africa Europe pipeline",     2),
    ("af_copper2",       "DRC Zambia copper mine renewable power",          2),
    ("af_rare2",         "rare earth cobalt lithium DRC Namibia mining",    2),
    ("af_jetp2",         "JETP just transition Africa South Africa Kenya",  2),
    ("af_grid2",         "electricity access Africa sub-Saharan grid",      2),
    ("af_iipp",          "independent power producer IPP Africa PPA signed",2),
    ("af_china2",        "China BRI energy Africa power dam investment",    2),
    ("af_us_invest",     "US Prosper Africa clean energy investment",       3),
    ("af_eu_global",     "EU Global Gateway Africa renewable energy",       3),
    ("eg_solar_tender",  "Egypt solar wind auction MW tender",              2),
    ("eg_green_h2",      "Egypt green hydrogen Suez ammonia export",        2),
    ("ma_solar_export",  "Morocco Xlinks solar cable UK export",            2),
    ("ma_green_h2",      "Morocco green hydrogen IRESEN plant",             3),
    ("za_re_auction",    "South Africa REIPPP round renewable auction MW",  2),
    ("za_eskom_reform",  "Eskom unbundling distribution reform",            2),
    ("ke_geothermal",    "Kenya geothermal Olkaria GDC MW new well",       3),
    ("ng_power_reform",  "Nigeria power sector privatisation gas grid",     3),
    ("tn_solar",         "Tunisia solar wind export undersea cable",        3),
    ("af_carbon_cr",     "Africa carbon credit forest solar project",       3),
    ("af_critical_min",  "Africa critical minerals battery supply China",   2),
    ("af_uranium",       "Niger Namibia uranium mine supply nuclear",       3),
]
for key, q, tier in _P21_AF_THEMES:
    _add(f"p21_af_th_{key}", f"AF th: {q[:40]}", "gnews", "africa", "policy", tier, query=q, gl="US")

_P21_AF_GDELT = [
    ("af_solar3",   "solar energy Africa megawatt project"),
    ("af_h2_3",     "green hydrogen Africa export ammonia"),
    ("af_mineral3", "Africa cobalt lithium copper mine supply"),
    ("af_finance3", "Africa energy investment World Bank AfDB"),
    ("af_grid3",    "electricity grid access Africa rural"),
    ("af_policy3",  "Africa energy policy reform renewable"),
]
for key, q in _P21_AF_GDELT:
    _add(f"p21_af_gd_{key}", f"GDELT: {q[:38]}", "gdelt", "africa", "geopolitics", 2, query=q)

# ── P21-G: New North America sources ──────────────────────────────────────────
_P21_NA_GEO = [
    ("us_mn",   "Minnesota renewable energy storage",  3),
    ("us_mi",   "Michigan solar utility scale",        3),
    ("us_nc",   "North Carolina solar utility",        3),
    ("us_va",   "Virginia offshore wind data center",  3),
    ("us_me",   "Maine offshore wind New England",     3),
    ("us_ma",   "Massachusetts offshore wind Vineyard",3),
    ("us_co",   "Colorado solar wind transmission",    3),
    ("us_id",   "Idaho geothermal solar",              3),
    ("us_mt",   "Montana wind solar transmission",     3),
    ("us_nm",   "New Mexico solar land renewable",     3),
    ("us_ok",   "Oklahoma wind solar Panhandle",       3),
    ("us_ks",   "Kansas wind solar Midwest",           3),
    ("us_ia",   "Iowa wind energy farm",               3),
    ("us_nd",   "North Dakota wind oil gas renewable", 3),
    ("us_sd",   "South Dakota wind solar",             3),
    ("us_wi",   "Wisconsin renewable energy mandate",  3),
    ("us_wy",   "Wyoming coal wind solar transition",  3),
    ("ca_on",   "Ontario Canada solar wind contract",  3),
    ("ca_ab",   "Alberta Canada solar wind market",    3),
    ("ca_bc",   "British Columbia hydro clean energy", 3),
    ("ca_qc",   "Quebec Canada hydropower export",     3),
    ("mx_cfmx", "Mexico CFE renewable nationalise",    3),
]
for key, desc, tier in _P21_NA_GEO:
    _add(f"p21_na_{key}", f"NA: {desc[:38]}", "gnews", "north_america", "re_industry", tier,
         query=desc, gl="US")

_P21_NA_THEMES = [
    ("us_repowering",   "US wind repowering blade extension farm",          3),
    ("us_storage_itc",  "US standalone storage ITC investment tax credit",  2),
    ("us_hydrogen_hub", "US clean hydrogen hub DOE H2Hubs",                 2),
    ("us_nuclear_res",  "US nuclear restart Three Mile Island Diablo",      3),
    ("us_smr2",         "US small modular reactor NuScale X-energy",        3),
    ("us_fusion2",      "US fusion energy Commonwealth TAE",                3),
    ("us_geo2",         "US enhanced geothermal Fervo project",             3),
    ("us_community2",   "US community solar subscriber low income",         3),
    ("us_agri2",        "US agrivoltaics dual land use solar farm",         3),
    ("us_supply_ch",    "US clean energy supply chain domestic content",    2),
    ("us_grid_mod",     "US grid modernisation FERC rule interconnection",  2),
    ("us_corp_ppa",     "corporate PPA power purchase agreement US RE100",  2),
    ("us_micro",        "US microgrid military campus resilience",          3),
    ("us_ldes",         "US long duration energy storage LDES iron air",    2),
    ("us_vpp",          "US virtual power plant aggregator utility demand", 3),
    ("us_ev_grid",      "US vehicle-to-grid V2G bidirectional charging",    3),
    ("us_permit_reform","US permitting streamline NEPA reform renewable",   2),
    ("us_offshore2",    "US offshore wind Atlantic Gulf Mexico project",    2),
    ("us_solar_roof2",  "US residential rooftop solar NEM net metering",   3),
    ("us_decarb_heat",  "US building decarbonisation heat pump IRA rebate", 3),
    ("ca_net_zero",     "Canada net zero 2050 clean electricity grid",      3),
    ("mx_solar_park",   "Mexico Sonora solar park PV GW private",          3),
    ("us_rare_earth",   "US rare earth critical mineral mine domestic",     2),
    ("us_grid_cyber2",  "US grid cybersecurity NERC critical infrastructure",3),
    ("us_coal_retire2", "US coal plant retirement early just transition",   3),
]
for key, q, tier in _P21_NA_THEMES:
    _add(f"p21_na_th_{key}", f"NA th: {q[:40]}", "gnews", "north_america", "policy", tier, query=q, gl="US")

_P21_NA_RSS = [
    ("p21_na_solar_ind",  "Solar Industries",        "https://solarindustrymag.com/feed/",                 3),
    ("p21_na_canary2",    "Canary Media Grid",       "https://www.canarymedia.com/topics/grid/rss.xml",     2),
    ("p21_na_energyinn",  "Energy News Network",     "https://energy-news-network.com/feed/",               3),
    ("p21_na_greentech2", "Greentech Media",         "https://www.greentechmedia.com/feed",                 2),
]
for sid, name, url, tier in _P21_NA_RSS:
    _add(sid, name, "rss", "north_america", "re_industry", tier, url=url)

_P21_NA_GDELT = [
    ("na_grid2",    "US grid investment transmission renewable storage"),
    ("na_h2_2",     "United States clean hydrogen hub production"),
    ("na_supply2",  "US solar wind domestic manufacturing supply chain"),
    ("na_policy2",  "US renewable energy policy tax credit IRA"),
    ("na_offshore2","US offshore wind Atlantic project approval"),
]
for key, q in _P21_NA_GDELT:
    _add(f"p21_na_gd_{key}", f"GDELT: {q[:38]}", "gdelt", "north_america", "geopolitics", 2, query=q)

# ── P21-H: New South America sources ──────────────────────────────────────────
_P21_SA_COUNTRIES_NEW = [
    "Honduras","Guatemala","El Salvador","Nicaragua","Costa Rica","Panama",
    "Cuba","Haiti","Jamaica","Trinidad and Tobago","Belize","Dominican Republic",
]
for cname in _P21_SA_COUNTRIES_NEW:
    sid = "p21_sa_" + cname.lower().replace(" ","_")
    _add(sid, f"{cname} energy", "gnews", "south_america", "re_industry", 3,
         query=f"{cname} (solar OR renewable OR wind OR electricity OR energy)", gl="US")

_P21_SA_THEMES = [
    ("br_h2_port",      "Brazil green hydrogen export port Pecém Suape",    2),
    ("br_leilao",       "Brazil energy leilão auction solar wind storage",  2),
    ("br_aneel2",       "ANEEL Brazil tariff regulatory decision",          3),
    ("br_onshore_wnd",  "Brazil onshore wind northeast Ceará new project",  2),
    ("br_solar_north",  "Brazil solar northeast generation peak curtail",   3),
    ("cl_bess_atacama", "Chile battery storage BESS Atacama curtailment",   2),
    ("cl_h2_export2",   "Chile green hydrogen export Europe Japan 2026",    2),
    ("cl_lithium_soc",  "Chile lithium SQM Codelco nationalisation",       2),
    ("cl_solar_record", "Chile solar record low tariff GW",                 3),
    ("ar_batt_tender",  "Argentina battery storage BESS tender",            3),
    ("ar_vaca_gas",     "Argentina Vaca Muerta LNG gas pipeline export",    3),
    ("co_wind_guajira", "Colombia Guajira offshore onshore wind",           3),
    ("pe_solar_pv",     "Peru solar PV utility tender auction",             3),
    ("sa_ev_latam",     "Latin America EV electric vehicle charging grid",  3),
    ("sa_copper2",      "Chile Peru copper mine output demand renewable",   2),
    ("sa_grid2",        "South America grid interconnection Brazil Chile",  3),
    ("sa_h2_ammon",     "South America green ammonia export fertiliser",    2),
    ("sa_finclimate",   "Latin America climate finance IDB CAF green bond", 3),
    ("sa_floating",     "Brazil floating solar reservoir hydropower",       3),
    ("sa_bioe",         "Brazil ethanol biofuel sugarcane SAF aviation",    3),
    ("mx_solar2",       "Mexico solar private utility investment ban CFE",  2),
    ("mx_nearshore",    "Mexico nearshoring energy data center factory",    3),
]
for key, q, tier in _P21_SA_THEMES:
    _add(f"p21_sa_th_{key}", f"SA th: {q[:40]}", "gnews", "south_america", "supply_chain", tier, query=q, gl="US")

_P21_SA_RSS = [
    ("p21_sa_pvlatam2", "PV Mag LatAm News", "https://www.pv-magazine-latam.com/noticias/feed/", 2),
    ("p21_sa_energiae", "Energía Estratégica","https://www.energiaestrategica.com/feed/",         2),
    ("p21_sa_elec_int", "Electricidad Int.",  "https://electricidadinteractiva.com/feed/",        3),
    ("p21_sa_pv_br",    "PV Magazine Brasil", "https://www.pv-magazine.com.br/feed/",            2),
]
for sid, name, url, tier in _P21_SA_RSS:
    _add(sid, name, "rss", "south_america", "re_industry", tier, url=url)

_P21_SA_GDELT = [
    ("sa_solar3",   "solar wind project Brazil Chile Argentina GW"),
    ("sa_h2_3",     "green hydrogen South America ammonia export"),
    ("sa_copper3",  "Chile Peru copper lithium mine supply chain"),
    ("sa_finance3", "Latin America clean energy finance IDB CAF"),
    ("sa_grid3",    "South America grid electricity interconnection"),
    ("sa_ev3",      "electric vehicle EV battery Latin America"),
]
for key, q in _P21_SA_GDELT:
    _add(f"p21_sa_gd_{key}", f"GDELT: {q[:38]}", "gdelt", "south_america", "geopolitics", 2, query=q)

# ── P21-I: New Oceania sources ─────────────────────────────────────────────────
_P21_OC_THEMES = [
    ("au_grid_ops",    "AEMO NEM grid operations 5-minute settlement", 2),
    ("au_rooftop2",    "Australia rooftop solar two million homes GW",  3),
    ("au_battery2",    "Australia big battery Waratah Neoen BESS GWh", 2),
    ("au_green_steel", "Australia green iron steel Pilbara hydrogen",   2),
    ("au_ccs",         "Australia carbon capture storage Gorgon CCS",  3),
    ("au_critical2",   "Australia critical minerals strategy fund",    2),
    ("au_export2",     "Australia energy export cable Asia Sun Cable",  3),
    ("au_nuclear_deb", "Australia nuclear debate SMR debate policy",   3),
    ("au_hydrogen2",   "Australia hydrogen headstart export Japan",     2),
    ("au_offshore2",   "Australia offshore wind zone environmental",    3),
    ("au_gas_dom",     "Australia domestic gas price cap east coast",  3),
    ("nz_transpower",  "New Zealand Transpower grid investment",       3),
    ("nz_geothermal",  "New Zealand geothermal Contact Mercury",       3),
    ("nz_h2",          "New Zealand hydrogen green export Japan",      3),
    ("nz_ev",          "New Zealand EV uptake charging grid",          3),
    ("pac_microgrid",  "Pacific islands microgrid solar diesel replace",3),
    ("au_retail2",     "Australia electricity retailer price hike bill",3),
    ("au_tech_solar",  "Australia solar technology research UNSW ANU", 3),
    ("au_ev_mandate",  "Australia EV fuel efficiency standard mandate", 3),
    ("au_inertia",     "Australia synchronous condenser grid inertia", 3),
    ("au_copper3",     "Australia copper mine project BHP South32",    3),
    ("png_hydro",      "Papua New Guinea hydropower LNG renewables",   3),
]
for key, q, tier in _P21_OC_THEMES:
    _add(f"p21_oc_th_{key}", f"OC th: {q[:40]}", "gnews", "oceania", "policy", tier, query=q, gl="AU")

_P21_OC_GDELT = [
    ("oc_bess3",    "Australia battery storage project GWh BESS"),
    ("oc_green3",   "Australia green hydrogen iron export Japan"),
    ("oc_mineral3", "Australia lithium cobalt rare earth critical mineral"),
    ("oc_grid3",    "Australia New Zealand grid stability renewable"),
    ("oc_policy3",  "Australia energy policy climate safeguard"),
]
for key, q in _P21_OC_GDELT:
    _add(f"p21_oc_gd_{key}", f"GDELT: {q[:38]}", "gdelt", "oceania", "geopolitics", 2, query=q)

# ── P21-J: New Global themes & cross-cutting ──────────────────────────────────
_P21_GLOBAL_THEMES = [
    # Technology frontier
    ("perovskite2",   "perovskite tandem solar efficiency record breakthrough",   2),
    ("topcon_hiku",   "TOPCon HJT solar module efficiency watt peak",             2),
    ("bifacial2",     "bifacial solar module tracking performance ratio",         2),
    ("pv_recycling",  "solar panel recycling end of life PV waste",               3),
    ("wind_ow_float", "floating offshore wind technology cost FOWT",              2),
    ("wind_blade",    "wind turbine blade recycling composite",                   3),
    ("ldes2",         "long duration energy storage iron air flow battery GWh",   2),
    ("solid_state",   "solid state battery energy density EV grid",               2),
    ("sodium_ion",    "sodium ion battery CATL cost commercial",                  2),
    ("flow_battery",  "vanadium redox flow battery utility scale MW",             3),
    ("gravity_store2","gravity energy storage ARES Gravitricity GWh",             3),
    ("geotherm2",     "enhanced geothermal system EGS project US",                3),
    ("fusion2",       "fusion energy net gain ITER Commonwealth Laser",           3),
    # Supply chain / commodities
    ("silicon_price", "polysilicon price China $/kg module cost",                 1),
    ("wafer_price",   "solar wafer price mono PERC $/piece",                      2),
    ("module_price2", "solar module price all-in $/W spot",                       1),
    ("inverter_price","solar inverter price utility residential $/W",             3),
    ("lithi_price",   "lithium carbonate hydroxide price $/tonne LME",           1),
    ("cobalt_price",  "cobalt price LME $/tonne DRC supply",                     2),
    ("nickel_price",  "nickel price LME battery NMC $/tonne",                   2),
    ("copper_price",  "copper price LME $/tonne supply demand",                  1),
    ("steel_price",   "steel HR coil price $/tonne renewable structure",         3),
    ("aluminium_prc", "aluminium price LME $/tonne solar frame",                 3),
    ("rare_earth_pr", "rare earth neodymium dysprosium price $/kg",              2),
    ("silicon_supply","silicon carbide SiC semiconductor power inverter",        3),
    ("shipping_cost", "container freight rate Drewry Shanghai SCFI",             2),
    ("lng_price",     "LNG spot price JKM TTF Asia Europe $/mmbtu",              1),
    ("coal_price",    "thermal coal price Newcastle API2 $/tonne",               2),
    ("gas_price",     "natural gas price Henry Hub TTF NBP",                     2),
    ("oil_price",     "crude oil Brent WTI OPEC price cut",                      1),
    # Finance / macro
    ("dxy_macro",     "US dollar index DXY impact emerging market debt",         2),
    ("fed_rates",     "US Federal Reserve rate decision energy financing",       2),
    ("ecb_rates",     "ECB rate decision Europe green bond",                     3),
    ("green_bond2",   "green bond issuance sovereign corporate $/billion",       2),
    ("carbon_price2", "EU ETS carbon credit price €/tonne auction",              2),
    ("vcm_price",     "voluntary carbon market offset price $/tonne VCS",        3),
    ("esg_fund",      "ESG fund sustainable investment inflow outflow",          3),
    ("cpi_energy",    "consumer price index energy component inflation",         2),
    # Geopolitics
    ("us_china_re",   "US China competition solar battery trade war decoupling", 1),
    ("indo_pacific",  "Indo-Pacific clean energy supply chain US India Japan",   2),
    ("bri_energy",    "China Belt Road energy project new financing",            3),
    ("mena_energy",   "MENA Middle East North Africa energy transition",         2),
    ("climate_fin",   "climate finance 100 billion developing nations COP",     2),
    ("loss_damage",   "loss damage climate fund developing nations",             3),
    ("un_sdg7",       "UN SDG7 energy access rural electrification progress",   3),
    ("iea_outlook",   "IEA World Energy Outlook net zero scenario 2030",        2),
    ("irena_stats",   "IRENA installed capacity statistics renewable 2025",     2),
    ("ipcc_climate",  "IPCC climate science report warming 1.5 degree",         3),
]
for key, q, tier in _P21_GLOBAL_THEMES:
    _add(f"p21_gl_th_{key}", f"GL th: {q[:40]}", "gnews", "global", "macro", tier, query=q, gl="US")

_P21_GLOBAL_GDELT = [
    ("gl_tech2",     "solar wind technology breakthrough efficiency record"),
    ("gl_supply3",   "solar module battery supply chain price decline"),
    ("gl_finance3",  "renewable energy investment record billion global"),
    ("gl_policy3",   "renewable energy policy subsidy support government"),
    ("gl_h2_3",      "green hydrogen project announcement GW billion"),
    ("gl_storage3",  "battery energy storage utility project GWh"),
    ("gl_mineral3",  "critical minerals lithium cobalt supply demand"),
    ("gl_climate3",  "climate change extreme heat flooding energy impact"),
    ("gl_trade3",    "clean energy trade tariff export restriction"),
    ("gl_ai_energy", "artificial intelligence data center energy demand power"),
]
for key, q in _P21_GLOBAL_GDELT:
    _add(f"p21_gl_gd_{key}", f"GDELT: {q[:38]}", "gdelt", "global", "macro", 2, query=q)

# ── P21-K: New structured API sources ─────────────────────────────────────────
_P21_API_SOURCES = [
    # Free data APIs (fetchers to be wired in neuron.py)
    ("p21_api_ember",        "Ember Electricity API (200+ countries)"),
    ("p21_api_energy_charts","Energy-Charts API (Germany hourly generation)"),
    ("p21_api_entsoe",       "ENTSO-E Transparency Platform (Europe)"),
    ("p21_api_opsd",         "Open Power System Data (EU)"),
    ("p21_api_neso_uk",      "NESO UK Grid API (demand, generation)"),
    ("p21_api_aemo2",        "AEMO NEM API (Australia real-time)"),
    ("p21_api_datagov_in",   "data.gov.in Power & Energy datasets"),
    ("p21_api_nordpool",     "Nord Pool day-ahead prices (Nordics)"),
    ("p21_api_euenergy",     "euenergy.live ENTSO-E day-ahead (41 zones)"),
    ("p21_api_carbon_pulse", "Carbon Pulse (carbon market news scrape)"),
    ("p21_api_pvwatts",      "NREL PVWatts solar resource API"),
    ("p21_api_globalsolar",  "Global Solar Atlas irradiance API"),
    ("p21_api_copernicus",   "Copernicus ERA5 reanalysis climate data"),
    ("p21_api_un_comtrade2", "UN Comtrade HS8541 solar module trade data"),
    ("p21_api_wb_climate",   "World Bank Climate Change Knowledge Portal"),
    ("p21_api_imf2",         "IMF Primary Commodity Prices (monthly)"),
    ("p21_api_bls",          "BLS US producer price index energy"),
    ("p21_api_ceic",         "CEIC India industrial production data"),
    ("p21_api_lme",          "LME commodity prices via Yahoo Finance"),
    ("p21_api_icap",         "ICAP ETS carbon price allowance explorer"),
]
for key, name in _P21_API_SOURCES:
    _add(key, name, "api", "global", "official_data", 1)

# ── Registry sanity (import-time, loud) ───────────────────────────────────────
def registry_counts():
    out = {}
    for s in SOURCES:
        out[s["region"]] = out.get(s["region"], 0) + 1
    out["total"] = len(SOURCES)
    return out

_ids = [s["id"] for s in SOURCES]
assert len(_ids) == len(set(_ids)), "duplicate source ids in registry"
_c = registry_counts()
assert _c["india"] >= 180, f"India sources {_c['india']} < 180"
for _r in ["asia", "europe", "africa", "north_america", "south_america", "oceania"]:
    assert _c[_r] >= 60, f"{_r} sources {_c[_r]} < 60"


# ── Storage ───────────────────────────────────────────────────────────────────
def init_v11_tables():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS v11_articles(
        uid TEXT PRIMARY KEY, source_id TEXT, region TEXT, category TEXT,
        title TEXT, link TEXT, summary TEXT, published_dt TEXT,
        tone REAL, fetched_ts REAL)""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_v11_art_region ON v11_articles(region, fetched_ts)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_v11_art_ts ON v11_articles(fetched_ts)")
    con.execute("""CREATE TABLE IF NOT EXISTS v11_source_health(
        source_id TEXT PRIMARY KEY, region TEXT, tier INTEGER,
        ok INTEGER DEFAULT 0, err INTEGER DEFAULT 0,
        last_ok REAL, last_err REAL, last_msg TEXT, last_items INTEGER)""")
    con.execute("""CREATE TABLE IF NOT EXISTS v11_kv(
        key TEXT PRIMARY KEY, value TEXT, ts REAL)""")
    # P14 Item 8 — "Living memory": durable per-entity lifecycle ledger.
    # Raw articles still age out at RETENTION_DAYS; only the structured fact
    # (status, date, capacity, players) is kept indefinitely here, so storage
    # stays tiny while the durable signal survives the 30-day window.
    con.execute("""CREATE TABLE IF NOT EXISTS v14_entity_ledger(
        entity_id TEXT PRIMARY KEY, entity_type TEXT, title TEXT,
        first_seen REAL, last_seen REAL, status TEXT,
        status_history TEXT, state TEXT, capacity_mw REAL,
        key_players TEXT, last_source_uid TEXT)""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_v14_type ON v14_entity_ledger(entity_type, last_seen)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_v14_state ON v14_entity_ledger(state)")
    con.commit(); con.close()


# ── P14 Item 8 — Living-memory entity extraction ──────────────────────────────
# Status keywords mirror neuron.py's PROJECT_WIN / COMMISSIONING classifier
# (neuron.py:227-228), extended with tender-lifecycle stages. This is NOT a new
# ML model — pure keyword extension of the existing classification, now
# persisted instead of discarded after 30 days. Ordered by lifecycle rank so a
# single article picks its strongest signal.
_ENTITY_STATUS_KW = [
    # (status, rank, keywords)
    ("stalled",      0, ["stalled","scrapped","cancelled","canceled","shelved",
                          "terminated","withdrawn","abandoned"]),
    ("announced",    1, ["announces","plans to","to set up","to build","proposed",
                          "floats tender","invites bids","tender floated","rfp issued",
                          "to develop","signs mou","mou signed"]),
    ("bid_open",     2, ["bid open","bids open","bid submission","auction","e-reverse auction",
                          "bidding","bids invited","bid deadline","technical bid"]),
    ("awarded",      3, ["wins order","bags order","awarded","l1 bidder","letter of award",
                          " loa ","emerges l1","lowest bidder","bid win","wins bid",
                          "project awarded","secures order","gets order","wins contract"]),
    ("commissioned", 4, ["commissions","commissioned","inaugurates","operationalises",
                          "operationalised","goes live","begins operations","first unit",
                          "capacity operationalised","coc received","formally inaugurated"]),
]
_STATUS_RANK = {s: r for s, r, _ in _ENTITY_STATUS_KW}

_INDIAN_STATES = [
    "andhra pradesh","arunachal pradesh","assam","bihar","chhattisgarh","goa",
    "gujarat","haryana","himachal pradesh","jharkhand","karnataka","kerala",
    "madhya pradesh","maharashtra","manipur","meghalaya","mizoram","nagaland",
    "odisha","punjab","rajasthan","sikkim","tamil nadu","telangana","tripura",
    "uttar pradesh","uttarakhand","west bengal","ladakh","jammu and kashmir",
    "delhi","puducherry","chandigarh",
]
# Known RE players for key_players tagging — kept small/curated; extraction is
# match-only (no NER) to avoid noise.
_RE_PLAYERS = [
    "adani green","adani","ntpc","nhpc","sjvn","tata power","torrent power",
    "suzlon","inox wind","ireda","seci","reliance","jsw energy","jsw",
    "renew","renew power","acme","azure power","greenko","avaada","vena energy",
    "waaree","premier energies","sembcorp","o2 power","hero future energies",
    "tata power renewable","juniper green","serentica",
    # ── Added in Parallel Track B ─────────────────────────────────────────────
    "premier energy","goldi solar","vikram solar","renewsys","jakson green",
    "navitas solar","tata power solar","avaada solar","acme solar",
    "emmvee solar","solex energy","websol energy","indo solar","xl energy",
    "hhv solar","zodiac energy","radiance renewables","saatvik solar",
    "waaree solar","adani solar","gautam solar","insolation energy",
    "pixon solar","greenvision","renewsys india","arka jain solar",
    "loom solar","utl solar","flin energy","orb energy",
]
_TENDER_HINTS  = ["tender","auction","bid","rfp","rfs","e-reverse","empanel"]
_POLICY_HINTS  = ["policy","notification","scheme","guidelines","mnre","cabinet",
                  "approves","notifies","rpo","obligation","amendment","draft rules"]

_CAP_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(gw|mw)\b", re.I)

def _extract_capacity_mw(text):
    best = None
    for m in _CAP_RE.finditer(text):
        try:
            val = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        if m.group(2).lower() == "gw":
            val *= 1000.0
        # Take the largest figure mentioned — headline capacity, not a sub-figure.
        if best is None or val > best:
            best = val
    return best

def _extract_state(text):
    for st in _INDIAN_STATES:
        if st in text:
            return st.title()
    return None

def _extract_players(text):
    found = []
    for p in _RE_PLAYERS:
        if p in text and p.title() not in found:
            found.append(p.title())
    return found[:5]

def _classify_status(text):
    """Return (status, rank) for the strongest lifecycle signal, or (None,None)."""
    hit = None
    for status, rank, kws in _ENTITY_STATUS_KW:
        if any(k in text for k in kws):
            # commissioned/awarded outrank announced; keep the highest non-stalled
            # rank seen, but a 'stalled' mention always wins (it's terminal news).
            if status == "stalled":
                return ("stalled", 0)
            if hit is None or rank > hit[1]:
                hit = (status, rank)
    return hit if hit else (None, None)

def _entity_anchor_id(entity_type, state, capacity_mw, title):
    toks = re.sub(r"[^a-z0-9 ]", "", (title or "").lower()).split()[:4]
    cap = str(int(capacity_mw)) if capacity_mw else "x"
    raw = f"{entity_type}|{state or 'x'}|{cap}|{'-'.join(toks)}"
    return hashlib.md5(raw.encode("utf-8", "ignore")).hexdigest()[:16]

def _find_existing_entity(con, entity_type, state, capacity_mw):
    """Fuzzy match the same real-world asset across its lifecycle. A single
    asset changes entity_type as it matures (a *tender* becomes a *project* once
    *commissioned*), so matching anchors on (state, capacity), NOT on type:
      - both capacity AND state known  → match on those regardless of type
        (a tender + a project at the same MW in the same state is one asset).
      - only one anchor known          → also require same entity_type, to
        avoid collapsing unrelated rows that merely share a state or a MW figure.
    Returns the most-recently-seen matching row or None."""
    rows = con.execute(
        "SELECT entity_id,status,status_history,capacity_mw,state,first_seen,entity_type "
        "FROM v14_entity_ledger ORDER BY last_seen DESC").fetchall()
    strong = bool(capacity_mw and state)
    for r in rows:
        eid, status, hist, cap, st, first_seen, etype = r
        if state and st and state != st:
            continue
        if capacity_mw and cap:
            if abs(capacity_mw - cap) / max(capacity_mw, cap) > 0.08:
                continue
        elif capacity_mw or cap:
            continue   # one side has a capacity figure, the other doesn't
        if not strong and etype != entity_type:
            continue   # weak anchor → don't merge across types
        return r[:6]
    return None

def _record_entity(con, title, summary, source_uid, now):
    """Extract a tracked entity from one article and upsert it. Returns the
    entity_id if something was recorded, else None. Pure keyword extraction."""
    text = ((title or "") + " " + (summary or "")).lower()
    status, rank = _classify_status(text)
    if not status:
        return None
    capacity_mw = _extract_capacity_mw(text)
    state = _extract_state(text)
    players = _extract_players(text)
    # Noise filter: a status verb alone isn't enough — require a real-world
    # anchor (a capacity figure or a recognised state) before opening a row.
    if not (capacity_mw or state):
        return None
    if any(h in text for h in _TENDER_HINTS):
        etype = "tender"
    elif any(h in text for h in _POLICY_HINTS):
        etype = "policy"
    else:
        etype = "project"

    existing = _find_existing_entity(con, etype, state, capacity_mw)
    if existing:
        eid, cur_status, hist_json, cap, st, first_seen = existing
        try:
            hist = json.loads(hist_json) if hist_json else []
        except Exception:
            hist = []
        cur_rank = _STATUS_RANK.get(cur_status, -1)
        # Invariant: status only moves forward in lifecycle rank (stalled may
        # interrupt anytime). No commissioned→awarded regressions get recorded.
        advance = (status == "stalled" and cur_status != "stalled") or rank > cur_rank
        if advance:
            hist.append({"status": status, "ts": now, "source_uid": source_uid})
            new_status = status
        else:
            new_status = cur_status
        merged_players = list(dict.fromkeys(
            (json.loads(con.execute("SELECT key_players FROM v14_entity_ledger WHERE entity_id=?",
                                     (eid,)).fetchone()[0] or "[]")) + players))[:5]
        con.execute(
            "UPDATE v14_entity_ledger SET last_seen=?, status=?, status_history=?, "
            "capacity_mw=COALESCE(capacity_mw,?), state=COALESCE(state,?), "
            "key_players=?, last_source_uid=? WHERE entity_id=?",
            (now, new_status, json.dumps(hist), capacity_mw, state,
             json.dumps(merged_players), source_uid, eid))
        return eid
    # New entity.
    eid = _entity_anchor_id(etype, state, capacity_mw, title)
    hist = [{"status": status, "ts": now, "source_uid": source_uid}]
    con.execute(
        "INSERT OR IGNORE INTO v14_entity_ledger "
        "(entity_id,entity_type,title,first_seen,last_seen,status,status_history,"
        "state,capacity_mw,key_players,last_source_uid) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (eid, etype, (title or "")[:300], now, now, status, json.dumps(hist),
         state, capacity_mw, json.dumps(players), source_uid))
    return eid


def _uid(link, title):
    return hashlib.md5(((link or "") + "|" + (title or "")).encode("utf-8", "ignore")).hexdigest()


def _store_articles(src, items):
    if not items:
        return 0
    con = sqlite3.connect(DB_PATH, timeout=15)
    n = 0
    now = time.time()
    for it in items:
        try:
            uid = _uid(it.get("link"), it.get("title"))
            cur = con.execute(
                """INSERT OR IGNORE INTO v11_articles
                   (uid,source_id,region,category,title,link,summary,published_dt,tone,fetched_ts)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (uid, src["id"], src["region"],
                 src["category"], (it.get("title") or "")[:300], it.get("link") or "",
                 (it.get("summary") or "")[:600], it.get("published") or "",
                 it.get("tone"), now))
            n += cur.rowcount
            # P14 Item 8 — only feed genuinely-new articles to the living-memory
            # ledger (rowcount==1). Failure here must never break ingestion.
            if cur.rowcount and src.get("region") == "india":
                try:
                    _record_entity(con, it.get("title"), it.get("summary"), uid, now)
                except Exception:
                    pass
        except Exception:
            pass
    con.commit(); con.close()
    return n


def _mark(src, ok, msg="", items=0):
    try:
        con = sqlite3.connect(DB_PATH, timeout=15)
        con.execute("""INSERT INTO v11_source_health
            (source_id,region,tier,ok,err,last_ok,last_err,last_msg,last_items)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source_id) DO UPDATE SET
              ok = ok + excluded.ok, err = err + excluded.err,
              last_ok  = COALESCE(excluded.last_ok,  last_ok),
              last_err = COALESCE(excluded.last_err, last_err),
              last_msg = excluded.last_msg, last_items = excluded.last_items,
              region = excluded.region, tier = excluded.tier""",
            (src["id"], src["region"], src["tier"], 1 if ok else 0, 0 if ok else 1,
             time.time() if ok else None, None if ok else time.time(),
             msg[:160], items))
        con.commit(); con.close()
    except Exception:
        pass


# ── Fetchers ──────────────────────────────────────────────────────────────────
_HDR = {"User-Agent": "Mozilla/5.0 (NEURON local monitor)"}

def _fetch_feed(url):
    r = requests.get(url, headers=_HDR, timeout=15)
    fp = feedparser.parse(r.content)
    items = []
    for e in fp.entries[:30]:
        items.append({"title": e.get("title", ""), "link": e.get("link", ""),
                      "summary": e.get("summary", "")[:600],
                      "published": e.get("published", "") or e.get("updated", "")})
    return items

def _fetch_gdelt(url):
    r = requests.get(url, headers=_HDR, timeout=20)
    js = r.json()
    items = []
    for a in (js.get("articles") or [])[:30]:
        items.append({"title": a.get("title", ""), "link": a.get("url", ""),
                      "summary": a.get("sourcecountry", "") + " · " + a.get("domain", ""),
                      "published": a.get("seendate", ""),
                      "tone": a.get("tone")})
    return items

def fetch_source(src):
    """Fetch one source; returns stored-new-article count. Never raises."""
    try:
        if src["type"] == "rss":
            items = _fetch_feed(src["url"])
        elif src["type"] == "gnews":
            items = _fetch_feed(_gnews_url(src["query"], src.get("gl", "IN"), src.get("hl", "en")))
        elif src["type"] == "gdelt":
            items = _fetch_gdelt(_gdelt_url(src["query"]))
        else:           # api sources are fetched by neuron.py's own fetchers
            _mark(src, True, "api source (external fetcher)", 0)
            return 0
        n = _store_articles(src, items)
        _mark(src, True, "", len(items))
        return n
    except Exception as e:
        _mark(src, False, str(e))
        return 0


# ── Background worker ─────────────────────────────────────────────────────────
_next_due = {}
_worker_started = False
INGEST_STATS = {"cycles": 0, "fetched": 0, "new_articles": 0, "started_at": None}

def _due_sources(now):
    due = []
    for s in SOURCES:
        if s["type"] == "api":
            continue
        nd = _next_due.get(s["id"], 0)
        if now >= nd:
            due.append(s)
    # tier 1 first, then longest-overdue
    due.sort(key=lambda s: (s["tier"], _next_due.get(s["id"], 0)))
    return due

def _worker_loop():
    from concurrent.futures import ThreadPoolExecutor
    # Stagger initial schedule so 500 sources don't fire at boot:
    # T1 within 2 min, T2 within 20 min, T3 within 2 h.
    now = time.time()
    spread = {1: 120, 2: 1200, 3: 7200}
    for s in SOURCES:
        _next_due[s["id"]] = now + random.uniform(5, spread[s["tier"]])
    INGEST_STATS["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    # P15 A5 — write a heartbeat the instant the worker is alive, so /api/health
    # can tell "starting up" from "dead" before the first fetch cycle completes.
    try:
        kv_set("worker_heartbeat", str(time.time()))
    except Exception:
        pass
    last_prune = 0
    while True:
        try:
            now = time.time()
            batch = _due_sources(now)[:8]            # gentle: ≤8 fetches/min
            if batch:
                with ThreadPoolExecutor(max_workers=4) as ex:
                    results = list(ex.map(fetch_source, batch))
                INGEST_STATS["fetched"] += len(batch)
                INGEST_STATS["new_articles"] += sum(results)
                for s in batch:
                    _next_due[s["id"]] = now + TIER_INTERVAL[s["tier"]] * random.uniform(0.9, 1.15)
            INGEST_STATS["cycles"] += 1
            if now - last_prune > 6 * 3600:          # retention prune
                last_prune = now
                try:
                    con = sqlite3.connect(DB_PATH, timeout=15)
                    con.execute("DELETE FROM v11_articles WHERE fetched_ts < ?",
                                (now - RETENTION_DAYS * 86400,))
                    con.commit(); con.close()
                except Exception:
                    pass
            # P15 A5 — heartbeat + live stats every cycle (~60s). A stale heartbeat
            # is the watchdog signal: /api/health flags the worker DEAD, never silent.
            try:
                kv_set("worker_heartbeat", str(now))
                kv_set("ingest_stats", json.dumps(INGEST_STATS))
            except Exception:
                pass
        except Exception:
            pass
        time.sleep(60)

def start_ingestion():
    global _worker_started
    if _worker_started:
        return
    _worker_started = True
    init_v11_tables()
    threading.Thread(target=_worker_loop, daemon=True).start()


# ── Query helpers (used by neuron.py routes & intel layer) ────────────────────
def source_stats():
    init_v11_tables()
    con = sqlite3.connect(DB_PATH, timeout=15)
    health = {}
    for row in con.execute("""SELECT region,
            SUM(CASE WHEN last_ok IS NOT NULL AND (last_err IS NULL OR last_ok>last_err) THEN 1 ELSE 0 END),
            COUNT(*) FROM v11_source_health GROUP BY region"""):
        health[row[0]] = {"healthy": row[1] or 0, "tracked": row[2]}
    arts = {}
    for row in con.execute("""SELECT region, COUNT(*) FROM v11_articles
            WHERE fetched_ts > ? GROUP BY region""", (time.time() - 86400,)):
        arts[row[0]] = row[1]
    total_arts = con.execute("SELECT COUNT(*) FROM v11_articles").fetchone()[0]
    con.close()
    counts = registry_counts()
    return {"registry": counts, "health_by_region": health,
            "articles_24h_by_region": arts, "articles_total": total_arts,
            "ingest": INGEST_STATS,
            "tiers": {t: sum(1 for s in SOURCES if s["tier"] == t) for t in (1, 2, 3)}}

def _entity_row_to_dict(r):
    try: hist = json.loads(r[6]) if r[6] else []
    except Exception: hist = []
    try: players = json.loads(r[9]) if r[9] else []
    except Exception: players = []
    return {"entity_id": r[0], "entity_type": r[1], "title": r[2],
            "first_seen": r[3], "last_seen": r[4], "status": r[5],
            "status_history": hist, "state": r[7], "capacity_mw": r[8],
            "key_players": players}

_ENTITY_COLS = ("entity_id,entity_type,title,first_seen,last_seen,status,"
                "status_history,state,capacity_mw,key_players")

def entity_pipeline(query=None, limit=80):
    """P14 Item 8 consumption: known-pipeline lifecycle facts. `query` fuzzy-
    matches a state or a company/player; empty query returns the most-recently-
    active entities. This is the durable structured memory the intelligence
    layer queries instead of only the last 48h of news."""
    init_v11_tables()
    con = sqlite3.connect(DB_PATH, timeout=15)
    rows = con.execute(
        f"SELECT {_ENTITY_COLS} FROM v14_entity_ledger ORDER BY last_seen DESC").fetchall()
    con.close()
    out = [_entity_row_to_dict(r) for r in rows]
    if query:
        q = query.strip().lower()
        out = [e for e in out
               if (e["state"] and q in e["state"].lower())
               or q in (e["title"] or "").lower()
               or any(q in p.lower() for p in e["key_players"])]
    return out[:limit]

def entity_ledger_stats():
    """Counts + a data-integrity invariant for smoke_test: no status_history
    that regresses in lifecycle rank (e.g. commissioned recorded before
    awarded)."""
    init_v11_tables()
    con = sqlite3.connect(DB_PATH, timeout=15)
    rows = con.execute(
        f"SELECT {_ENTITY_COLS} FROM v14_entity_ledger").fetchall()
    con.close()
    by_status, by_type, orphan_jumps = {}, {}, 0
    for r in rows:
        e = _entity_row_to_dict(r)
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1
        by_type[e["entity_type"]] = by_type.get(e["entity_type"], 0) + 1
        last_rank = -1
        for h in e["status_history"]:
            rk = _STATUS_RANK.get(h.get("status"), -1)
            if h.get("status") == "stalled":
                continue   # terminal interrupt, allowed at any point
            if rk < last_rank:
                orphan_jumps += 1
                break
            last_rank = rk
    return {"total": len(rows), "by_status": by_status, "by_type": by_type,
            "orphan_status_jumps": orphan_jumps}


# ── P15 A3 — Entity correction (living memory must be editable + auditable) ────
# A false entity (wrong state, phantom capacity) would otherwise persist forever.
# Corrections are reversible: every delete/patch snapshots the prior row into
# v15_entity_audit BEFORE changing the ledger, so "don't lose data" holds even
# while the user fixes mistakes. A delete archives, it does not destroy.
def _init_entity_audit(con):
    con.execute("""CREATE TABLE IF NOT EXISTS v15_entity_audit(
        id INTEGER PRIMARY KEY AUTOINCREMENT, entity_id TEXT, op TEXT,
        before_json TEXT, after_json TEXT, reason TEXT, ts REAL)""")

_PATCHABLE = {"status", "state", "capacity_mw", "title", "entity_type", "key_players"}

def delete_entity(entity_id, reason=""):
    """Archive then remove a single ledger row. The full prior row is preserved
    in v15_entity_audit, so the memory is recoverable — never silently gone."""
    init_v11_tables()
    con = sqlite3.connect(DB_PATH, timeout=15)
    _init_entity_audit(con)
    row = con.execute(
        f"SELECT {_ENTITY_COLS},last_source_uid FROM v14_entity_ledger WHERE entity_id=?",
        (entity_id,)).fetchone()
    if not row:
        con.close()
        return {"ok": False, "error": "entity not found", "entity_id": entity_id}
    before = _entity_row_to_dict(row)
    con.execute("INSERT INTO v15_entity_audit(entity_id,op,before_json,after_json,reason,ts) "
                "VALUES (?,?,?,?,?,?)",
                (entity_id, "delete", json.dumps(before), None, reason[:300], time.time()))
    con.execute("DELETE FROM v14_entity_ledger WHERE entity_id=?", (entity_id,))
    con.commit(); con.close()
    return {"ok": True, "deleted": entity_id, "archived": True, "before": before}

def patch_entity(entity_id, fields, reason=""):
    """Correct fields on one entity. Whitelisted columns only; before/after are
    audited. Returns the updated entity."""
    bad = set(fields) - _PATCHABLE
    if bad:
        return {"ok": False, "error": f"non-patchable fields: {sorted(bad)}"}
    init_v11_tables()
    con = sqlite3.connect(DB_PATH, timeout=15)
    _init_entity_audit(con)
    row = con.execute(
        f"SELECT {_ENTITY_COLS},last_source_uid FROM v14_entity_ledger WHERE entity_id=?",
        (entity_id,)).fetchone()
    if not row:
        con.close()
        return {"ok": False, "error": "entity not found", "entity_id": entity_id}
    before = _entity_row_to_dict(row)
    sets, args = [], []
    for k, v in fields.items():
        if k == "key_players":
            v = json.dumps(v if isinstance(v, list) else [v])
        elif k == "capacity_mw" and v is not None:
            try: v = float(v)
            except (TypeError, ValueError):
                con.close(); return {"ok": False, "error": "capacity_mw must be numeric"}
        sets.append(f"{k}=?"); args.append(v)
    sets.append("last_seen=?"); args.append(time.time())
    args.append(entity_id)
    con.execute(f"UPDATE v14_entity_ledger SET {','.join(sets)} WHERE entity_id=?", args)
    after_row = con.execute(
        f"SELECT {_ENTITY_COLS},last_source_uid FROM v14_entity_ledger WHERE entity_id=?",
        (entity_id,)).fetchone()
    after = _entity_row_to_dict(after_row)
    con.execute("INSERT INTO v15_entity_audit(entity_id,op,before_json,after_json,reason,ts) "
                "VALUES (?,?,?,?,?,?)",
                (entity_id, "patch", json.dumps(before), json.dumps(after), reason[:300], time.time()))
    con.commit(); con.close()
    return {"ok": True, "patched": entity_id, "before": before, "after": after}


# ── P15 A5 — Worker watchdog view (read by /api/health) ───────────────────────
def worker_health():
    """Heartbeat freshness for the ingestion daemon. >5 min stale ⇒ DEAD, loudly,
    so the worker can never die in silence."""
    hb = kv_get("worker_heartbeat")
    now = time.time()
    age = (now - float(hb)) if hb else None
    if age is None:
        status = "UNKNOWN"
    elif age <= 300:
        status = "ALIVE"
    else:
        status = "DEAD"
    stats = None
    raw = kv_get("ingest_stats")
    if raw:
        try: stats = json.loads(raw)
        except Exception: stats = None
    return {"status": status, "heartbeat_age_seconds": round(age) if age is not None else None,
            "last_heartbeat_ts": float(hb) if hb else None, "ingest": stats}


def recent_articles(region=None, hours=24, limit=60):
    init_v11_tables()
    con = sqlite3.connect(DB_PATH, timeout=15)
    q = """SELECT source_id,region,category,title,link,summary,published_dt,tone,fetched_ts
           FROM v11_articles WHERE fetched_ts > ?"""
    args = [time.time() - hours * 3600]
    if region:
        q += " AND region = ?"; args.append(region)
    q += " ORDER BY fetched_ts DESC LIMIT ?"; args.append(limit)
    rows = con.execute(q, args).fetchall()
    con.close()
    return [{"source_id": r[0], "region": r[1], "category": r[2], "title": r[3],
             "link": r[4], "summary": r[5], "published": r[6], "tone": r[7],
             "fetched_ts": r[8]} for r in rows]

def region_velocity(hours=24):
    """Articles/hour by region now vs the trailing 7-day baseline — the pulse."""
    init_v11_tables()
    con = sqlite3.connect(DB_PATH, timeout=15)
    now = time.time()
    out = {}
    for region in REGIONS:
        cur = con.execute("""SELECT COUNT(*) FROM v11_articles
            WHERE region=? AND fetched_ts > ?""", (region, now - hours * 3600)).fetchone()[0]
        base = con.execute("""SELECT COUNT(*) FROM v11_articles
            WHERE region=? AND fetched_ts BETWEEN ? AND ?""",
            (region, now - 8 * 86400, now - 86400)).fetchone()[0]
        baseline_per_day = base / 7.0 if base else 0
        ratio = (cur / max(baseline_per_day, 1)) if baseline_per_day else None
        out[region] = {"last24h": cur, "baseline_per_day": round(baseline_per_day, 1),
                       "ratio": round(ratio, 2) if ratio else None}
    con.close()
    return out

def kv_set(key, value):
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.execute("INSERT OR REPLACE INTO v11_kv(key,value,ts) VALUES (?,?,?)",
                (key, value, time.time()))
    con.commit(); con.close()

def kv_get(key, max_age=None):
    con = sqlite3.connect(DB_PATH, timeout=15)
    row = con.execute("SELECT value, ts FROM v11_kv WHERE key=?", (key,)).fetchone()
    con.close()
    if not row:
        return None
    if max_age and time.time() - row[1] > max_age:
        return None
    return row[0]
