#!/usr/bin/env python3
"""Thu thập dữ liệu chính thức NOAA/NWS + số liệu mô hình cho bản tin thời tiết Mỹ (mặc định: toàn quốc).

Ví dụ:
  python3 tong_hop_nws.py                      # toàn quốc (mặc định)
  python3 tong_hop_nws.py --area TX,OK         # một/nhiều bang
  python3 tong_hop_nws.py --point 29.76,-95.37 --name Houston
  python3 tong_hop_nws.py --city "Denver, CO"
  python3 tong_hop_nws.py --no-models          # bỏ phần mô hình (nhanh hơn)
  python3 tong_hop_nws.py --json               # dữ liệu thô

Nguồn chính thức: api.weather.gov (cảnh báo, dự báo 7 ngày, AFD, SPC Day 1–3 text, WPC discussions),
SPC (GeoJSON nguy cơ, Mesoscale Discussion, Storm Reports), WPC (ERO), NHC (bão + Tropical Weather Outlook), CPC (6–10/8–14).
Mô hình (tham khảo): Open-Meteo — GFS, ECMWF IFS, ICON, GEM và ensemble GEFS/ECMWF.
Chỉ dùng thư viện chuẩn Python 3.9+. Mỗi nguồn chạy độc lập: nguồn lỗi được liệt kê ở cuối để kiểm tra tay.
"""
import argparse, concurrent.futures as cf, csv, datetime as dt, html, io, json, re, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

try:
    from zoneinfo import ZoneInfo
    ET_TZ = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    ET_TZ = dt.timezone(dt.timedelta(hours=-5))

UA = {"User-Agent": "thoi-tiet-my-skill (weather briefing)", "Accept": "application/geo+json, application/json, */*"}
NOW = dt.datetime.now(dt.timezone.utc)
ERRORS = []

# Thành phố chính mỗi bang (lat, lon).
CITIES = {
    "AL": [("Birmingham", 33.52, -86.81), ("Montgomery", 32.38, -86.30), ("Mobile", 30.69, -88.04), ("Huntsville", 34.73, -86.59)],
    "AK": [("Anchorage", 61.22, -149.90), ("Fairbanks", 64.84, -147.72), ("Juneau", 58.30, -134.42)],
    "AZ": [("Phoenix", 33.45, -112.07), ("Tucson", 32.22, -110.97), ("Flagstaff", 35.20, -111.65)],
    "AR": [("Little Rock", 34.75, -92.29), ("Fayetteville", 36.06, -94.16), ("Jonesboro", 35.84, -90.70)],
    "CA": [("Los Angeles", 34.05, -118.24), ("San Francisco", 37.77, -122.42), ("Sacramento", 38.58, -121.49), ("San Diego", 32.72, -117.16)],
    "CO": [("Denver", 39.74, -104.99), ("Colorado Springs", 38.83, -104.82), ("Grand Junction", 39.06, -108.55)],
    "CT": [("Hartford", 41.76, -72.68), ("New Haven", 41.31, -72.92)],
    "DE": [("Wilmington DE", 39.74, -75.55), ("Dover", 39.16, -75.52)],
    "DC": [("Washington", 38.90, -77.04)],
    "FL": [("Miami", 25.76, -80.19), ("Orlando", 28.54, -81.38), ("Tampa", 27.95, -82.46), ("Jacksonville", 30.33, -81.66), ("Tallahassee", 30.44, -84.28)],
    "GA": [("Atlanta", 33.75, -84.39), ("Savannah", 32.08, -81.09), ("Macon", 32.84, -83.63)],
    "HI": [("Honolulu", 21.31, -157.86), ("Hilo", 19.72, -155.09)],
    "ID": [("Boise", 43.62, -116.20), ("Idaho Falls", 43.49, -112.03), ("Coeur d'Alene", 47.68, -116.78)],
    "IL": [("Chicago", 41.88, -87.63), ("Springfield IL", 39.78, -89.65), ("Peoria", 40.69, -89.59)],
    "IN": [("Indianapolis", 39.77, -86.16), ("Fort Wayne", 41.08, -85.14), ("Evansville", 37.97, -87.57)],
    "IA": [("Des Moines", 41.59, -93.62), ("Cedar Rapids", 41.98, -91.67), ("Sioux City", 42.50, -96.40)],
    "KS": [("Wichita", 37.69, -97.34), ("Topeka", 39.05, -95.68), ("Dodge City", 37.75, -100.02)],
    "KY": [("Louisville", 38.25, -85.76), ("Lexington", 38.04, -84.50), ("Paducah", 37.08, -88.60)],
    "LA": [("New Orleans", 29.95, -90.07), ("Baton Rouge", 30.45, -91.19), ("Shreveport", 32.53, -93.75), ("Lake Charles", 30.23, -93.22)],
    "ME": [("Portland ME", 43.66, -70.26), ("Bangor", 44.80, -68.77), ("Caribou", 46.86, -68.01)],
    "MD": [("Baltimore", 39.29, -76.61), ("Salisbury", 38.36, -75.60), ("Hagerstown", 39.64, -77.72)],
    "MA": [("Boston", 42.36, -71.06), ("Worcester", 42.26, -71.80), ("Springfield MA", 42.10, -72.59)],
    "MI": [("Detroit", 42.33, -83.05), ("Grand Rapids", 42.96, -85.67), ("Marquette", 46.54, -87.40)],
    "MN": [("Minneapolis", 44.98, -93.27), ("Duluth", 46.79, -92.10), ("Rochester MN", 44.02, -92.47)],
    "MS": [("Jackson MS", 32.30, -90.18), ("Gulfport", 30.37, -89.09), ("Tupelo", 34.26, -88.70)],
    "MO": [("St. Louis", 38.63, -90.20), ("Kansas City", 39.10, -94.58), ("Springfield MO", 37.21, -93.29)],
    "MT": [("Billings", 45.78, -108.50), ("Missoula", 46.87, -113.99), ("Great Falls", 47.50, -111.30)],
    "NE": [("Omaha", 41.26, -95.93), ("Lincoln", 40.81, -96.70), ("North Platte", 41.12, -100.77)],
    "NV": [("Las Vegas", 36.17, -115.14), ("Reno", 39.53, -119.81), ("Elko", 40.83, -115.76)],
    "NH": [("Manchester", 42.99, -71.46), ("Concord", 43.21, -71.54)],
    "NJ": [("Newark", 40.74, -74.17), ("Atlantic City", 39.36, -74.42), ("Trenton", 40.22, -74.76)],
    "NM": [("Albuquerque", 35.08, -106.65), ("Las Cruces", 32.32, -106.76), ("Roswell", 33.39, -104.52)],
    "NY": [("New York", 40.71, -74.01), ("Buffalo", 42.89, -78.88), ("Albany", 42.65, -73.76), ("Syracuse", 43.05, -76.15)],
    "NC": [("Charlotte", 35.23, -80.84), ("Raleigh", 35.78, -78.64), ("Asheville", 35.60, -82.55), ("Wilmington NC", 34.23, -77.94)],
    "ND": [("Fargo", 46.88, -96.79), ("Bismarck", 46.81, -100.78), ("Minot", 48.23, -101.30)],
    "OH": [("Columbus", 39.96, -83.00), ("Cleveland", 41.50, -81.69), ("Cincinnati", 39.10, -84.51)],
    "OK": [("Oklahoma City", 35.47, -97.52), ("Tulsa", 36.15, -95.99), ("Lawton", 34.61, -98.39)],
    "OR": [("Portland OR", 45.52, -122.68), ("Medford", 42.33, -122.87), ("Bend", 44.06, -121.32)],
    "PA": [("Philadelphia", 39.95, -75.17), ("Pittsburgh", 40.44, -80.00), ("Harrisburg", 40.27, -76.88), ("Scranton", 41.41, -75.66)],
    "RI": [("Providence", 41.82, -71.41)],
    "SC": [("Columbia SC", 34.00, -81.03), ("Charleston SC", 32.78, -79.93), ("Greenville SC", 34.85, -82.40)],
    "SD": [("Sioux Falls", 43.55, -96.73), ("Rapid City", 44.08, -103.23), ("Aberdeen", 45.46, -98.49)],
    "TN": [("Nashville", 36.16, -86.78), ("Memphis", 35.15, -90.05), ("Knoxville", 35.96, -83.92), ("Chattanooga", 35.05, -85.31)],
    "TX": [("Houston", 29.76, -95.37), ("Dallas", 32.78, -96.80), ("San Antonio", 29.42, -98.49), ("Austin", 30.27, -97.74),
           ("Lubbock", 33.58, -101.86), ("El Paso", 31.76, -106.49), ("Corpus Christi", 27.80, -97.40), ("Amarillo", 35.22, -101.83)],
    "UT": [("Salt Lake City", 40.76, -111.89), ("St. George", 37.10, -113.58), ("Moab", 38.57, -109.55)],
    "VT": [("Burlington", 44.48, -73.21), ("Montpelier", 44.26, -72.58)],
    "VA": [("Richmond", 37.54, -77.44), ("Norfolk", 36.85, -76.29), ("Roanoke", 37.27, -79.94), ("Arlington", 38.88, -77.10)],
    "WA": [("Seattle", 47.61, -122.33), ("Spokane", 47.66, -117.43), ("Yakima", 46.60, -120.51)],
    "WV": [("Charleston WV", 38.35, -81.63), ("Morgantown", 39.63, -79.96), ("Beckley", 37.78, -81.19)],
    "WI": [("Milwaukee", 43.04, -87.91), ("Madison", 43.07, -89.40), ("Green Bay", 44.51, -88.01)],
    "WY": [("Cheyenne", 41.14, -104.82), ("Casper", 42.87, -106.31), ("Jackson", 43.48, -110.76)],
    "PR": [("San Juan", 18.47, -66.11), ("Ponce", 18.01, -66.61)],
    "VI": [("Charlotte Amalie", 18.34, -64.93)],
    "GU": [("Hagatna", 13.48, 144.75)],
}
CITY_STATE = {c[0]: st for st, v in CITIES.items() for c in v}
# Bản tin toàn quốc: thành phố trải đều các vùng (dùng cho nguy cơ SPC/WPC và mô hình).
NATIONAL_SCAN = ["Seattle", "Portland OR", "San Francisco", "Los Angeles", "Phoenix", "Las Vegas", "Salt Lake City", "Boise", "Billings",
                 "Denver", "Albuquerque", "Bismarck", "Sioux Falls", "Minneapolis", "Omaha", "Kansas City", "Oklahoma City", "Dallas",
                 "Houston", "San Antonio", "New Orleans", "Memphis", "Chicago", "Detroit", "St. Louis", "Nashville", "Indianapolis",
                 "Columbus", "Atlanta", "Birmingham", "Miami", "Tampa", "Charlotte", "Raleigh", "Washington", "Philadelphia",
                 "New York", "Boston", "Buffalo", "Pittsburgh", "Portland ME", "Anchorage", "Honolulu"]
# Bản tin toàn quốc: thành phố lấy dự báo 7 ngày chính thức NWS.
NATIONAL_FORECAST = ["New York", "Washington", "Atlanta", "Miami", "Chicago", "Minneapolis", "Dallas", "Houston", "Denver", "Phoenix",
                     "Los Angeles", "Seattle"]

PRIORITY = [
    "Tornado Emergency", "Flash Flood Emergency", "Extreme Wind Warning", "Tornado Warning", "Flash Flood Warning", "Storm Surge Warning",
    "Hurricane Warning", "Severe Thunderstorm Warning", "Tsunami Warning", "Blizzard Warning", "Ice Storm Warning", "Tropical Storm Warning",
    "Snow Squall Warning", "Dust Storm Warning", "Extreme Heat Warning", "Excessive Heat Warning", "Extreme Cold Warning",
    "Winter Storm Warning", "Lake Effect Snow Warning", "High Wind Warning", "Flood Warning", "Red Flag Warning", "Coastal Flood Warning",
    "Tornado Watch", "Severe Thunderstorm Watch", "Hurricane Watch", "Storm Surge Watch", "Tropical Storm Watch", "Flash Flood Watch",
    "Flood Watch", "Winter Storm Watch", "Extreme Heat Watch", "Extreme Cold Watch", "High Wind Watch", "Fire Weather Watch",
    "Winter Weather Advisory", "Heat Advisory", "Cold Weather Advisory", "Wind Advisory", "Flood Advisory", "Dense Fog Advisory",
    "Freeze Warning", "Frost Advisory", "Air Quality Alert", "Special Weather Statement",
]
SEV = {"Extreme": 0, "Severe": 1, "Moderate": 2, "Minor": 3, "Unknown": 4}
SPC_RANK = {"TSTM": 0, "MRGL": 1, "SLGT": 2, "ENH": 3, "MDT": 4, "HIGH": 5}
SPC_TXT = {"TSTM": "General t-storms", "MRGL": "Marginal (1/5)", "SLGT": "Slight (2/5)", "ENH": "Enhanced (3/5)", "MDT": "Moderate (4/5)", "HIGH": "High (5/5)"}
ERO_TXT = {1: "Marginal (1/4)", 2: "Slight (2/4)", 3: "Moderate (3/4)", 4: "High (4/4)"}

# Mô hình Open-Meteo và ngưỡng "tín hiệu" (đơn vị Mỹ).
DET_MODELS = ["gfs_seamless", "ecmwf_ifs025", "icon_seamless", "gem_seamless"]
ENS_MODELS = ["gfs025", "ecmwf_ifs025"]
DAILY = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "snowfall_sum", "wind_gusts_10m_max"]
THRESH = {  # tên: (biến, phép so sánh, ngưỡng, mô tả)
    "heavy_rain": ("precipitation_sum", ">=", 1.5, "mưa ≥1.5 in/ngày"),
    "snow": ("snowfall_sum", ">=", 3.0, "tuyết ≥3 in/ngày"),
    "wind": ("wind_gusts_10m_max", ">=", 50.0, "gió giật ≥50 mph"),
    "heat": ("temperature_2m_max", ">=", 100.0, "cao nhất ≥100°F"),
    "cold": ("temperature_2m_min", "<=", 10.0, "thấp nhất ≤10°F"),
}


# ---------------- tiện ích ----------------
def get(url, as_json=True, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return json.loads(data) if as_json else data.decode("utf-8", "replace")


def safe(label, fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception as e:
        ERRORS.append(f"{label}: {type(e).__name__}: {str(e)[:160]}")
        return None


def parse_time(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_time(s):
    """Giờ địa phương của sản phẩm + giờ ET (chuẩn cho bản tin toàn quốc)."""
    t = parse_time(s)
    if not t:
        return "—"
    e = t.astimezone(ET_TZ)
    loc = t.strftime("%a %b %d %I:%M %p").replace(" 0", " ")
    off = t.utcoffset()
    h = int(off.total_seconds() // 3600) if off is not None else 0
    return f"{loc} (UTC{h:+d}) = {e.strftime('%a %I:%M %p').replace(' 0', ' ')} {e.tzname()}"


def clean(text, n=None):
    t = re.sub(r"[ \t]+", " ", text or "").strip()
    return t if n is None or len(t) <= n else t[:n] + "…"


def in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def in_geom(lon, lat, geom):
    if not geom:
        return False
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"] if geom["type"] == "MultiPolygon" else []
    return any(p and in_ring(lon, lat, p[0]) and not any(in_ring(lon, lat, h) for h in p[1:]) for p in polys)


# ---------------- NWS ----------------
def alerts(area=None, point=None):
    q = {"status": "actual"}
    if area and area != "US":
        q["area"] = area
    if point:
        q["point"] = f"{point[0]:.4f},{point[1]:.4f}"
    d = get("https://api.weather.gov/alerts/active?" + urllib.parse.urlencode(q))
    out = []
    for f in d.get("features", []):
        p = f["properties"]
        end = parse_time(p.get("ends") or p.get("expires"))
        if end and end < NOW:
            continue
        params = p.get("parameters") or {}
        ev = p.get("event", "")
        desc = (p.get("description") or "").strip()
        if ev == "Tornado Warning" and "TORNADO EMERGENCY" in desc.upper():
            ev = "Tornado Emergency"
        if ev == "Flash Flood Warning" and "FLASH FLOOD EMERGENCY" in desc.upper():
            ev = "Flash Flood Emergency"
        if "PARTICULARLY DANGEROUS SITUATION" in desc.upper() and "Watch" in ev:
            ev = "PDS " + ev
        ugc = (p.get("geocode") or {}).get("UGC") or []
        out.append({
            "event": ev, "severity": p.get("severity", "Unknown"), "urgency": p.get("urgency"),
            "states": sorted({u[:2] for u in ugc}), "area": p.get("areaDesc", ""), "sender": p.get("senderName", ""),
            "onset": p.get("onset") or p.get("effective"), "ends": p.get("ends") or p.get("expires"),
            "headline": (params.get("NWSheadline") or [p.get("headline") or ""])[0],
            "maxWindGust": (params.get("maxWindGust") or [None])[0], "maxHailSize": (params.get("maxHailSize") or [None])[0],
            "tornadoDetection": (params.get("tornadoDetection") or [None])[0],
            "description": desc, "id": p.get("id"),
        })

    def rank(a):
        ev = a["event"].replace("PDS ", "")
        return (PRIORITY.index(ev) if ev in PRIORITY else len(PRIORITY), SEV.get(a["severity"], 4))

    out.sort(key=rank)
    return out


def point_info(lat, lon):
    p = get(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}")["properties"]
    return {"wfo": p.get("gridId"), "forecast": p.get("forecast"), "tz": p.get("timeZone")}


def forecast(url, days):
    return get(url)["properties"]["periods"][: days * 2]


def latest_product(ptype, loc=None):
    url = f"https://api.weather.gov/products/types/{ptype}" + (f"/locations/{loc}" if loc else "")
    g = get(url).get("@graph") or []
    if not g:
        return None
    return get(f"https://api.weather.gov/products/{g[0]['id']}")


def afd(wfo, chars=1500):
    prod = latest_product("AFD", wfo)
    if not prod:
        return None
    text = prod.get("productText", "")
    m = re.search(r"\.(KEY MESSAGES|SYNOPSIS|WHAT HAS CHANGED)[^\n]*\n(.*?)(?=\n&&|\n\.[A-Z][A-Z /]+\.\.\.)", text, re.S)
    return {"wfo": wfo, "issued": prod.get("issuanceTime"), "text": clean(m.group(0) if m else text, chars)}


def spc_text(day):
    """Đoạn SUMMARY của SPC Day 1/2/3 Convective Outlook (SWODY1/2/3)."""
    prod = latest_product(f"SWODY{day}")
    if not prod:
        return None
    text = prod.get("productText", "")
    m = re.search(r"\.\.\.SUMMARY\.\.\.\s*(.*?)(?:\n\s*\n|\n\.\.\.)", text, re.S)
    risk = re.findall(r"\.\.\.THERE IS A[N]? (\w+(?: \w+)?) RISK[^.]*?\.\.\.", text)
    return {"issued": prod.get("issuanceTime"), "summary": clean((m.group(1) if m else text[:600]).replace("\n", " "), 700),
            "headlines": [clean(h) for h in risk][:3]}


def wpc_disc(ptype, chars=2500):
    """WPC Short Range (PMDSPD) / Extended (PMDEPD) Forecast Discussion."""
    prod = latest_product(ptype)
    if not prod:
        return None
    text = prod.get("productText", "")
    body = re.split(r"\n\s*\n", text, maxsplit=3)
    body = "\n\n".join(body[2:]) if len(body) > 3 else text
    return {"issued": prod.get("issuanceTime"), "text": clean(body, chars)}


# ---------------- SPC / WPC / NHC / CPC ----------------
def spc_geo(day):
    return get(f"https://www.spc.noaa.gov/products/outlook/day{day}otlk_cat.nolyr.geojson").get("features", [])


def ero_geo(day):
    return get(f"https://www.wpc.ncep.noaa.gov/exper/eromap/geojson/Day{day}_Latest.geojson").get("features", [])


def spc_at(features, lat, lon):
    best = None
    for f in features or []:
        lab = (f.get("properties") or {}).get("LABEL")
        if lab in SPC_RANK and in_geom(lon, lat, f.get("geometry")) and (best is None or SPC_RANK[lab] > SPC_RANK[best]):
            best = lab
    return best


def ero_at(features, lat, lon):
    best = 0
    for f in features or []:
        txt = " ".join(str(v) for v in (f.get("properties") or {}).values()).upper()
        m = re.search(r"\b(HIGH|MODERATE|SLIGHT|MARGINAL|MDT|SLGT|MRGL)\b", txt)
        lvl = {"MARGINAL": 1, "MRGL": 1, "SLIGHT": 2, "SLGT": 2, "MODERATE": 3, "MDT": 3, "HIGH": 4}.get(m.group(1), 0) if m else 0
        if lvl > best and in_geom(lon, lat, f.get("geometry")):
            best = lvl
    return best


def rss(url, max_items=10):
    root = ET.fromstring(get(url, as_json=False))
    out = []
    for it in root.iter("item"):
        out.append({k: (it.findtext(k) or "").strip() for k in ("title", "link", "pubDate", "description")})
    return out[:max_items]


def spc_mds():
    items = rss("https://www.spc.noaa.gov/products/spcmdrss.xml", 15)
    return [{"title": i["title"], "link": i["link"], "pubDate": i["pubDate"],
             "text": clean(re.sub(r"<[^>]+>", " ", html.unescape(i["description"])), 500)} for i in items]


def storm_reports(which):
    """SPC Storm Reports (12Z–12Z). which = today | yesterday."""
    raw = get(f"https://www.spc.noaa.gov/climo/reports/{which}_filtered.csv", as_json=False)
    kind, out = None, {"tornado": [], "wind": [], "hail": []}
    for row in csv.reader(io.StringIO(raw)):
        if not row:
            continue
        if row[0] == "Time":
            kind = {"F_Scale": "tornado", "Speed": "wind", "Size": "hail"}.get(row[1])
            continue
        if kind and len(row) >= 8:
            out[kind].append({"time": row[0], "mag": row[1], "loc": row[2], "county": row[3], "state": row[4], "comments": row[7][:200]})
    return out


def nhc():
    return get("https://www.nhc.noaa.gov/CurrentStorms.json").get("activeStorms", [])


def nhc_two():
    out = {}
    for basin, url in (("Atlantic", "https://www.nhc.noaa.gov/index-at.xml"), ("East Pacific", "https://www.nhc.noaa.gov/index-ep.xml")):
        for it in rss(url, 30):
            if "Tropical Weather Outlook" in it["title"]:
                out[basin] = clean(re.sub(r"<[^>]+>", " ", html.unescape(it["description"])), 1200)
                break
    return out


def cpc(kind):
    """CPC 6–10 / 8–14 day prognostic discussion (trích)."""
    page = get("https://www.cpc.ncep.noaa.gov/products/predictions/610day/fxus06.html", as_json=False)
    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    text = re.sub(r"\s+", " ", text)
    m = re.search(r"(6-10 DAY OUTLOOK FOR .*?)(?=8-14 DAY OUTLOOK FOR)", text) if kind == "610" else re.search(r"(8-14 DAY OUTLOOK FOR .*?)(?=FORECASTER|THE NEXT SET|$)", text)
    return clean(m.group(1) if m else text[:1500], 1500)


# ---------------- Mô hình (Open-Meteo) ----------------
def om_det(lat, lon, days):
    q = {"latitude": lat, "longitude": lon, "daily": ",".join(DAILY), "models": ",".join(DET_MODELS), "forecast_days": days,
         "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch", "timezone": "auto"}
    return get("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(q))


def om_ens(lat, lon, model, days):
    q = {"latitude": lat, "longitude": lon, "daily": ",".join(DAILY), "models": model, "forecast_days": days,
         "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch", "timezone": "auto"}
    return get("https://ensemble-api.open-meteo.com/v1/ensemble?" + urllib.parse.urlencode(q))


def _hit(v, op, th):
    return v is not None and (v >= th if op == ">=" else v <= th)


def model_signals(name, det, ens):
    """Trả về danh sách tín hiệu: thành phố, ngày, hiện tượng, số mô hình đồng ý, % ensemble, khoảng giá trị."""
    out = []
    if not det:
        return out
    daily = det.get("daily") or {}
    dates = daily.get("time") or []
    for key, (var, op, th, label) in THRESH.items():
        for i, day in enumerate(dates):
            vals = {}
            for m in DET_MODELS:
                arr = daily.get(f"{var}_{m}")
                if arr and i < len(arr) and arr[i] is not None:
                    vals[m] = arr[i]
            if not vals:
                continue
            agree = [m for m, v in vals.items() if _hit(v, op, th)]
            if not agree:
                continue
            ens_pct = {}
            for em, ed in (ens or {}).items():
                ed = (ed or {}).get("daily") or {}
                members = [ed[k][i] for k in ed if k.startswith(var) and isinstance(ed[k], list) and i < len(ed[k]) and ed[k][i] is not None]
                if members:
                    ens_pct[em] = round(100 * sum(_hit(v, op, th) for v in members) / len(members))
            out.append({"place": name, "date": day, "day_index": i + 1, "hazard": key, "label": label,
                        "agree": f"{len(agree)}/{len(vals)}", "models_hit": agree,
                        "range": f"{min(vals.values()):.1f}–{max(vals.values()):.1f}", "ensemble_pct": ens_pct})
    return out


# ---------------- Chấm điểm độ hot & gom đề tài ----------------
_ADJ_RAW = {
    "AL": "FL GA MS TN", "AZ": "CA CO NM NV UT", "AR": "LA MO MS OK TN TX", "CA": "AZ NV OR", "CO": "AZ KS NE NM OK UT WY",
    "CT": "MA NY RI", "DE": "MD NJ PA", "DC": "MD VA", "FL": "AL GA", "GA": "AL FL NC SC TN", "ID": "MT NV OR UT WA WY",
    "IL": "IA IN KY MO WI", "IN": "IL KY MI OH", "IA": "IL MN MO NE SD WI", "KS": "CO MO NE OK", "KY": "IL IN MO OH TN VA WV",
    "LA": "AR MS TX", "ME": "NH", "MD": "DE PA VA WV DC", "MA": "CT NH NY RI VT", "MI": "IN OH WI", "MN": "IA ND SD WI",
    "MS": "AL AR LA TN", "MO": "AR IA IL KS KY NE OK TN", "MT": "ID ND SD WY", "NE": "CO IA KS MO SD WY", "NV": "AZ CA ID OR UT",
    "NH": "MA ME VT", "NJ": "DE NY PA", "NM": "AZ CO OK TX", "NY": "CT MA NJ PA VT", "NC": "GA SC TN VA", "ND": "MN MT SD",
    "OH": "IN KY MI PA WV", "OK": "AR CO KS MO NM TX", "OR": "CA ID NV WA", "PA": "DE MD NJ NY OH WV", "RI": "CT MA", "SC": "GA NC",
    "SD": "IA MN MT ND NE WY", "TN": "AL AR GA KY MO MS NC VA", "TX": "AR LA NM OK", "UT": "AZ CO ID NV WY", "VT": "MA NH NY",
    "VA": "KY MD NC TN WV DC", "WA": "ID OR", "WV": "KY MD OH PA VA", "WI": "IA IL MI MN", "WY": "CO ID MT NE SD UT",
}
ADJ = {}
for _s, _n in _ADJ_RAW.items():
    for _t in _n.split():
        ADJ.setdefault(_s, set()).add(_t)
        ADJ.setdefault(_t, set()).add(_s)

REGION = {}
for _r, _ss in {"Northeast": "ME NH VT MA RI CT NY NJ PA", "Mid-Atlantic": "DE MD DC VA WV", "Southeast": "NC SC GA FL",
                "South": "AL MS LA AR TN KY", "Midwest": "OH IN IL MI WI MN IA MO", "Northern Plains": "ND SD NE",
                "Southern Plains": "TX OK KS", "Rockies": "MT WY CO UT ID", "Southwest": "AZ NM NV", "West Coast": "CA OR WA",
                "Alaska": "AK", "Hawaii": "HI", "Caribbean": "PR VI", "Pacific Islands": "GU AS MP"}.items():
    for _s in _ss.split():
        REGION[_s] = _r

CAT_VI = {"severe": "Dông mạnh/lốc xoáy", "tropical": "Bão nhiệt đới", "flood": "Mưa lớn/lũ", "winter": "Bão tuyết/băng giá",
          "cold": "Rét đậm/đóng băng", "heat": "Nắng nóng", "fire": "Cháy rừng", "wind": "Gió mạnh/bão bụi",
          "coastal": "Ngập ven biển/sóng lớn", "other": "Khác (sương mù, không khí…)"}
CAT_EN = {"severe": "Severe Storms", "tropical": "Tropical", "flood": "Flooding Rain", "winter": "Winter Storm", "cold": "Arctic Cold",
          "heat": "Heat Wave", "fire": "Fire Danger", "wind": "High Winds", "coastal": "Coastal Flooding", "other": "Weather"}

# Trọng số cảnh báo (điểm cho cảnh báo đầu tiên của loại đó trong bang).
ALERT_W = {
    "Tornado Emergency": 60, "Flash Flood Emergency": 60, "Extreme Wind Warning": 60, "Hurricane Warning": 50, "Storm Surge Warning": 40,
    "PDS Tornado Watch": 35, "Tsunami Warning": 50, "Blizzard Warning": 28, "Ice Storm Warning": 28, "Tropical Storm Warning": 25,
    "Tornado Warning": 18, "Hurricane Watch": 25, "Extreme Heat Warning": 18, "Excessive Heat Warning": 18, "Extreme Cold Warning": 18,
    "Winter Storm Warning": 16, "Tornado Watch": 16, "Flash Flood Warning": 14, "Storm Surge Watch": 15, "Lake Effect Snow Warning": 14,
    "Snow Squall Warning": 8, "Dust Storm Warning": 10, "Tropical Storm Watch": 12, "High Wind Warning": 9, "Red Flag Warning": 7,
    "Severe Thunderstorm Watch": 9, "Severe Thunderstorm Warning": 5, "Winter Storm Watch": 9, "Flood Warning": 6, "Flash Flood Watch": 6,
    "Extreme Heat Watch": 7, "Extreme Cold Watch": 7, "Coastal Flood Warning": 7, "Flood Watch": 4, "High Wind Watch": 4,
    "Fire Weather Watch": 3, "Winter Weather Advisory": 3, "Heat Advisory": 3, "Cold Weather Advisory": 2, "Wind Advisory": 2,
    "Freeze Warning": 2, "Coastal Flood Advisory": 1, "Flood Advisory": 1, "Dense Fog Advisory": 1, "Air Quality Alert": 1,
}
SPC_PTS = {"MRGL": 3, "SLGT": 8, "ENH": 16, "MDT": 28, "HIGH": 40}
ERO_PTS = {1: 2, 2: 6, 3: 18, 4: 30}
SIG_PTS = {"CAO": 6, "TRUNG BÌNH": 3}
SIG_CAT = {"heavy_rain": "flood", "snow": "winter", "wind": "wind", "heat": "heat", "cold": "cold"}
SOLO = 45        # bang đạt điểm này → đề tài riêng
STORY_MIN = 15   # dưới mức này không thành đề tài


def event_cat(ev):
    e = ev.replace("PDS ", "")
    rules = [("tropical", ("Hurricane", "Tropical Storm", "Storm Surge", "Typhoon")), ("severe", ("Tornado", "Severe Thunderstorm", "Extreme Wind")),
             ("flood", ("Flood",)), ("winter", ("Blizzard", "Ice Storm", "Winter", "Snow", "Lake Effect", "Freezing")),
             ("cold", ("Cold", "Freeze", "Frost", "Wind Chill")), ("heat", ("Heat",)), ("fire", ("Red Flag", "Fire")),
             ("wind", ("Wind", "Dust")), ("coastal", ("Coastal", "Surf", "Rip Current", "Tsunami"))]
    if e.startswith("Coastal Flood"):
        return "coastal"
    for cat, keys in rules:
        if any(k in e for k in keys):
            return cat
    return "other"


def _conf(s):
    n = int(s["agree"].split("/")[0])
    top = max(s["ensemble_pct"].values()) if s["ensemble_pct"] else 0
    return "CAO" if n >= 3 and top >= 50 else "TRUNG BÌNH" if n >= 2 or top >= 30 else "THẤP"


def score_states(d):
    """Điểm theo bang và theo loại sự kiện: {state: {cat: {"now": x, "soon": y, "why": [..]}}}."""
    S = {}

    def add(st, cat, pts, why, soon=False):
        if not st or pts <= 0:
            return
        c = S.setdefault(st, {}).setdefault(cat, {"now": 0.0, "soon": 0.0, "why": []})
        c["soon" if soon else "now"] += pts
        c["why"].append(why)

    counts = {}
    for a in d.get("alerts") or []:
        for st in a["states"]:
            counts[(st, a["event"])] = counts.get((st, a["event"]), 0) + 1
    for (st, ev), n in counts.items():
        w = ALERT_W.get(ev, 1)
        add(st, event_cat(ev), w * min(1 + 0.3 * (n - 1), 2.5), f"{ev} ×{n}")

    best_spc, best_ero = {}, {}
    for r in d.get("risk") or []:
        st = r.get("state")
        for day, lab in (r.get("spc") or {}).items():
            if lab in SPC_PTS:
                k = (st, int(day))
                if SPC_PTS[lab] > SPC_PTS.get(best_spc.get(k), 0):
                    best_spc[k] = lab
        for day, lvl in (r.get("ero") or {}).items():
            if lvl:
                k = (st, int(day))
                best_ero[k] = max(best_ero.get(k, 0), lvl)
    for (st, day), lab in best_spc.items():
        add(st, "severe", SPC_PTS[lab] / day, f"SPC D{day} {SPC_TXT[lab]}", soon=day > 1)
    for (st, day), lvl in best_ero.items():
        add(st, "flood", ERO_PTS[lvl] / day, f"WPC ERO D{day} {ERO_TXT[lvl]}", soon=day > 1)

    for which, mult in (("today", 1.0), ("yesterday", 0.6)):
        r = (d.get("reports") or {}).get(which) or {}
        per = {}
        for k in ("tornado", "wind", "hail"):
            for x in r.get(k, []):
                per.setdefault(x["state"], {"tornado": 0, "wind": 0, "hail": 0, "bighail": 0})[k] += 1
                if k == "hail" and x["mag"].isdigit() and int(x["mag"]) >= 200:
                    per[x["state"]]["bighail"] += 1
        for st, c in per.items():
            pts = (min(c["tornado"] * 7, 45) + min(c["wind"], 15) + min(c["hail"], 10) + min(c["bighail"] * 3, 12)) * mult
            add(st, "severe", pts, f"Storm reports {which}: {c['tornado']} tornado, {c['wind']} wind, {c['hail']} hail")

    sig = {}
    for s in d.get("signals") or []:
        conf = _conf(s)
        st = CITY_STATE.get(s["place"])
        if conf in SIG_PTS and st:
            k = (st, SIG_CAT[s["hazard"]], s["date"])
            if SIG_PTS[conf] > sig.get(k, (0, ""))[0]:
                sig[k] = (SIG_PTS[conf], f"Mô hình {s['date']}: {s['label']} tại {s['place']} ({s['agree']}, tin cậy {conf})")
    per_cat = {}
    for (st, cat, _), (pts, why) in sig.items():
        per_cat.setdefault((st, cat), []).append((pts, why))
    for (st, cat), lst in per_cat.items():
        lst.sort(reverse=True)
        add(st, cat, min(sum(p for p, _ in lst), 18), lst[0][1] + (f" (+{len(lst) - 1} ngày khác)" if len(lst) > 1 else ""), soon=True)
    return S


def _components(states, cat_of):
    seen, comps = set(), []
    for s in sorted(states):
        if s in seen:
            continue
        comp, stack = [], [s]
        seen.add(s)
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in ADJ.get(x, ()):
                if y in states and y not in seen and cat_of[y] == cat_of[s]:
                    seen.add(y)
                    stack.append(y)
        comps.append(sorted(comp))
    return comps


def build_stories(d):
    S = score_states(d)
    total = {st: {cat: v["now"] + v["soon"] for cat, v in cats.items()} for st, cats in S.items()}
    main_cat = {st: max(c, key=c.get) for st, c in total.items() if c}
    score = {st: round(sum(total[st].values())) for st in main_cat}
    hot = {st for st, sc in score.items() if sc >= STORY_MIN / 2}  # bang có tín hiệu đáng kể mới được gom
    stories = []

    def make(states, kind):
        cats = {}
        for st in states:
            for cat, v in total[st].items():
                cats[cat] = cats.get(cat, 0) + v
        cat = max(cats, key=cats.get)
        now = sum(S[st][c]["now"] for st in states for c in S[st])
        soon = sum(S[st][c]["soon"] for st in states for c in S[st])
        ranked = sorted((score[st] for st in states), reverse=True)
        sc = round(ranked[0] + 0.5 * sum(ranked[1:]))  # khu vực: bang mạnh nhất + nửa điểm các bang còn lại
        regions = []
        for st in sorted(states, key=lambda s: -score[s]):
            if REGION.get(st, st) not in regions:
                regions.append(REGION.get(st, st))
        if kind == "solo":
            name = f"{STATE_NAME.get(states[0], states[0])} {CAT_EN[cat]}"
        else:
            name = f"{' & '.join(regions[:2])} {CAT_EN[cat]}"
        why = []
        for st in sorted(states, key=lambda s: -score[s])[:4]:
            for c in sorted(S[st], key=lambda c: -total[st][c])[:2]:
                why.append(f"{st}: " + "; ".join(S[st][c]["why"][:3]))
        tier = "RẤT HOT" if sc >= 70 else "HOT" if sc >= 40 else "ĐÁNG CHÚ Ý" if sc >= STORY_MIN else "PHỤ"
        return {"name": name, "kind": "Bang riêng" if kind == "solo" else "Khu vực", "category": cat, "category_vi": CAT_VI[cat],
                "timing": "Đang diễn ra / hôm nay" if now >= soon else "Sắp tới (ngày 2–10)", "score": sc, "tier": tier,
                "states": sorted(states, key=lambda s: -score[s]), "state_scores": {s: score[s] for s in states},
                "other_hazards": sorted({CAT_VI[c] for st in states for c in total[st] if c != cat and total[st][c] >= 5}),
                "why": why}

    # Gom theo hệ thống (bang liền kề, cùng loại sự kiện) trước, rồi mới tách bang đủ hot ra video riêng.
    # Các bang còn lại của cùng hệ thống vẫn là MỘT video khu vực (kể cả khi không còn liền kề sau khi tách).
    for comp in _components(hot, main_cat):
        solo = [st for st in comp if score[st] >= SOLO]
        rest = [st for st in comp if st not in solo]
        solo_names = [STATE_NAME.get(st, st) for st in solo]
        group = []
        for st in solo:
            x = make([st], "solo")
            group.append(x)
        if rest:
            x = make(rest, "region")
            if solo:
                x["name"] += f" (outside {' & '.join(solo_names)})"
            if x["score"] >= STORY_MIN:
                group.append(x)
        if len(comp) > 1:
            system = ", ".join(sorted(comp, key=lambda s: -score[s]))
            for x in group:
                x["related"] = [y["name"] for y in group if y is not x]
                x["system"] = system
        stories += group
    stories.sort(key=lambda s: -s["score"])
    return stories


STATE_NAME = {"AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado", "CT": "Connecticut",
              "DE": "Delaware", "DC": "Washington D.C.", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
              "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
              "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
              "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
              "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
              "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
              "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
              "PR": "Puerto Rico", "VI": "U.S. Virgin Islands", "GU": "Guam", "AS": "American Samoa"}


def render_stories(stories):
    L = ["## 0. BẢNG XẾP HẠNG ĐỀ TÀI (điểm tự động — Claude điều chỉnh theo tin tức đã xác thực)"]
    if not stories:
        L.append("- Không có đề tài nào đạt ngưỡng. → Làm 1 video tổng hợp toàn quốc (dự báo 7 ngày + sự kiện sắp tới).")
        return "\n".join(L)
    L.append(f"Quy tắc: bang ≥{SOLO} điểm → video riêng; các bang liền kề cùng loại sự kiện → gộp 1 video khu vực (điểm = bang mạnh nhất + ½ các bang còn lại); đề tài <{STORY_MIN} điểm bỏ. Mức: ≥70 RẤT HOT, 40–69 HOT, {STORY_MIN}–39 ĐÁNG CHÚ Ý.")
    L.append("| # | Đề tài (tên gợi ý) | Loại | Hiện tượng | Thời điểm | Điểm | Mức | Bang (điểm) |")
    L.append("|---|---|---|---|---|---|---|---|")
    for i, s in enumerate(stories, 1):
        sts = ", ".join(f"{st} {s['state_scores'][st]}" for st in s["states"])
        L.append(f"| {i} | {s['name']} | {s['kind']} | {s['category_vi']} | {s['timing']} | {s['score']} | {s['tier']} | {sts} |")
    L.append("")
    for i, s in enumerate(stories, 1):
        L.append(f"**#{i} {s['name']}** — lý do:")
        for w in s["why"]:
            L.append(f"  - {w}")
        if s["other_hazards"]:
            L.append(f"  - Hiện tượng khác trong vùng: {', '.join(s['other_hazards'])}")
        if s.get("related"):
            L.append(f"  - Cùng hệ thống thời tiết ({s['system']}) với: {'; '.join(s['related'])} → nhắc chéo trong video, không lặp nội dung")
    return "\n".join(L)


# ---------------- tổng hợp ----------------
def resolve_places(args):
    if args.city:
        q = args.city.split(",")[0].strip()
        d = get("https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode({"name": q, "count": 10, "countryCode": "US"}))
        res = d.get("results") or []
        if "," in args.city:
            st = args.city.split(",")[1].strip().lower()
            res = [r for r in res if st in (r.get("admin1") or "").lower() or st == (r.get("admin1_code") or "").lower()] or res
        if not res:
            raise SystemExit(f"Không tìm thấy thành phố: {args.city}")
        r = res[0]
        return None, (r["latitude"], r["longitude"]), [(r["name"], r["latitude"], r["longitude"])], [r["name"]]
    if args.point:
        lat, lon = (float(x) for x in args.point.split(","))
        name = args.name or f"{lat:.2f},{lon:.2f}"
        return None, (lat, lon), [(name, lat, lon)], [name]
    area = (args.area or "US").upper().replace(" ", "")
    allc = {c[0]: c for v in CITIES.values() for c in v}
    if area == "US":
        return "US", None, [allc[n] for n in NATIONAL_SCAN], NATIONAL_FORECAST
    scan = []
    for st in area.split(","):
        if st not in CITIES:
            raise SystemExit(f"Mã bang không hợp lệ: {st}")
        scan += CITIES[st]
    return area, None, scan, [c[0] for st in area.split(",") for c in CITIES[st][: args.cities]]


def collect(args):
    area, point, scan, fc_names = resolve_places(args)
    allc = {c[0]: c for c in scan}
    days_model = args.model_days
    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        F = lambda label, fn, *a: ex.submit(safe, label, fn, *a)
        f_alerts = F("Cảnh báo NWS", alerts, area, point)
        f_spc_geo = {d: F(f"SPC GeoJSON ngày {d}", spc_geo, d) for d in (1, 2, 3)}
        f_spc_txt = {d: F(f"SPC text ngày {d} (SWODY{d})", spc_text, d) for d in (1, 2, 3)}
        f_ero = {d: F(f"WPC ERO ngày {d}", ero_geo, d) for d in (1, 2, 3)}
        f_md = F("SPC Mesoscale Discussions", spc_mds)
        f_rep = {w: F(f"SPC Storm Reports {w}", storm_reports, w) for w in ("today", "yesterday")}
        f_nhc = F("NHC bão", nhc)
        f_two = F("NHC Tropical Weather Outlook", nhc_two)
        f_wpc = {p: F(f"WPC {p}", wpc_disc, p) for p in (("PMDSPD", "PMDEPD") if area == "US" else ("PMDSPD",))}
        f_cpc = {k: F(f"CPC {k}", cpc, k) for k in ("610", "814")}
        f_pts = {n: F(f"points {n}", point_info, allc[n][1], allc[n][2]) for n in fc_names if n in allc}
        f_det, f_ens = {}, {}
        if not args.no_models:
            for n, lat, lon in scan:
                f_det[n] = F(f"Open-Meteo {n}", om_det, lat, lon, days_model)
                f_ens[n] = {m: F(f"Ensemble {m} {n}", om_ens, lat, lon, m, days_model) for m in ENS_MODELS}

        pts = {k: v.result() for k, v in f_pts.items()}
        f_fc = {k: F(f"dự báo {k}", forecast, v["forecast"], args.days) for k, v in pts.items() if v and v.get("forecast")}
        wfos = []
        for v in pts.values():
            if v and v.get("wfo") and v["wfo"] not in wfos:
                wfos.append(v["wfo"])
        f_afd = {w: F(f"AFD {w}", afd, w) for w in wfos[: args.afd]}

        spc = {d: f.result() for d, f in f_spc_geo.items()}
        ero = {d: f.result() for d, f in f_ero.items()}
        risk = [{"place": n, "state": CITY_STATE.get(n, ""),
                 "spc": {d: spc_at(spc[d], lat, lon) for d in spc if spc[d] is not None},
                 "ero": {d: ero_at(ero[d], lat, lon) for d in ero if ero[d] is not None}} for n, lat, lon in scan]
        signals = []
        for n in f_det:
            signals += model_signals(n, f_det[n].result(), {m: f.result() for m, f in f_ens[n].items()})

        out = {
            "generated_utc": NOW.isoformat(timespec="seconds"),
            "generated_et": NOW.astimezone(ET_TZ).strftime("%a %b %d %Y %I:%M %p %Z"),
            "scope": area or scan[0][0],
            "alerts": f_alerts.result(),
            "spc_text": {d: f.result() for d, f in f_spc_txt.items()},
            "spc_max": {d: max([SPC_RANK.get((f.get("properties") or {}).get("LABEL"), -1) for f in spc[d]] + [-1]) for d in spc if spc[d] is not None},
            "risk": risk,
            "mds": f_md.result(),
            "reports": {w: f.result() for w, f in f_rep.items()},
            "nhc": f_nhc.result(), "nhc_two": f_two.result(),
            "wpc": {p: f.result() for p, f in f_wpc.items()},
            "cpc": {k: f.result() for k, f in f_cpc.items()},
            "points": pts,
            "forecasts": {k: f.result() for k, f in f_fc.items()},
            "afd": [f.result() for f in f_afd.values() if f.result()],
            "signals": signals,
            "models_used": {"deterministic": DET_MODELS, "ensemble": ENS_MODELS, "days": days_model} if not args.no_models else None,
            "errors": ERRORS,
        }
        out["stories"] = build_stories(out)
        return out


# ---------------- in kết quả ----------------
def render(d, max_alerts):
    L = []
    w = L.append
    w(f"# DỮ LIỆU THỜI TIẾT MỸ — {d['scope']} — lấy lúc {d['generated_et']} ({d['generated_utc']} UTC)\n")
    w(render_stories(d.get("stories") or []) + "\n")

    # 1. Cảnh báo
    al = d["alerts"]
    w("## 1. Cảnh báo NWS đang hiệu lực [OFFICIAL]")
    if al is None:
        w("- LỖI: không lấy được → kiểm tra https://www.weather.gov/ hoặc https://api.weather.gov/alerts/active")
    elif not al:
        w("- KHÔNG có cảnh báo/khuyến cáo nào đang hiệu lực.")
    else:
        cnt, by_state = {}, {}
        for a in al:
            cnt[a["event"]] = cnt.get(a["event"], 0) + 1
            for s in a["states"]:
                by_state.setdefault(a["event"], set()).add(s)
        order = lambda ev: PRIORITY.index(ev.replace("PDS ", "")) if ev.replace("PDS ", "") in PRIORITY else 999
        w(f"- Tổng {len(al)} sản phẩm. Theo loại (số lượng → bang):")
        for ev in sorted(cnt, key=order):
            w(f"  - {ev} ×{cnt[ev]} → {', '.join(sorted(by_state.get(ev, [])))}")
        w("")
        seen, shown = set(), 0
        for a in al:
            key = (a["event"], a["area"][:80], a["ends"])
            if key in seen:
                continue
            seen.add(key)
            if shown >= max_alerts:
                w(f"- … còn nữa (dùng --max-alerts hoặc --json)")
                break
            shown += 1
            extra = [x for x in (a["maxWindGust"] and f"gusts {a['maxWindGust']}", a["maxHailSize"] and f'hail {a["maxHailSize"]}"',
                                 a["tornadoDetection"] and f"tornado {a['tornadoDetection']}") if x]
            w(f"### {a['event']} — {', '.join(a['states'])} — {a['sender']} [{a['severity']}/{a['urgency']}]")
            w(f"- Area: {clean(a['area'], 350)}")
            w(f"- Valid: {fmt_time(a['onset'])} → {fmt_time(a['ends'])}")
            if extra:
                w("- " + "; ".join(extra))
            if a["headline"]:
                w(f"- Headline: {clean(a['headline'], 300)}")
            if a["description"]:
                w(f"- Text: {clean(re.sub(chr(10), ' ', a['description']), 450)}")
            w("")

    # 2. SPC
    w("\n## 2. Dông mạnh / lốc xoáy — SPC [OFFICIAL]")
    for day in (1, 2, 3):
        t = (d["spc_text"] or {}).get(day)
        mx = d["spc_max"].get(day)
        lvl = next((SPC_TXT[k] for k, r in SPC_RANK.items() if r == mx), "none") if mx is not None and mx >= 0 else ("none" if mx is not None else "?")
        w(f"- **Day {day}** — mức cao nhất: {lvl}" + (f" — issued {fmt_time(t['issued'])}" if t else ""))
        if t:
            for h in t["headlines"]:
                w(f"  - {h}")
            w(f"  - Summary: {t['summary']}")
    w("- Day 4–8: xem tay https://www.spc.noaa.gov/products/exper/day4-8/")
    mds = d.get("mds")
    if mds:
        w("\n**Mesoscale Discussions gần nhất:**")
        for m in mds[:8]:
            w(f"- {m['title']} ({m['pubDate']}) — {m['text'][:260]} {m['link']}")
    for which in ("today", "yesterday"):
        r = (d.get("reports") or {}).get(which)
        if r is None:
            continue
        lab = "hôm nay (từ 12Z)" if which == "today" else "hôm qua (12Z–12Z)"
        w(f"\n**Storm Reports {lab}:** tornado {len(r['tornado'])}, wind {len(r['wind'])}, hail {len(r['hail'])} (báo cáo sơ bộ, chưa phải kết quả khảo sát)")
        for k in ("tornado", "wind", "hail"):
            if r[k]:
                st = {}
                for x in r[k]:
                    st[x["state"]] = st.get(x["state"], 0) + 1
                w(f"  - {k}: " + ", ".join(f"{s} {n}" for s, n in sorted(st.items(), key=lambda kv: -kv[1])))
        big_hail = sorted([x for x in r["hail"] if x["mag"].isdigit()], key=lambda x: -int(x["mag"]))[:3]
        big_wind = sorted([x for x in r["wind"] if x["mag"].isdigit()], key=lambda x: -int(x["mag"]))[:3]
        for x in big_hail:
            w(f"  - hail {int(x['mag']) / 100:.2f}\" — {x['loc']}, {x['county']} Co., {x['state']} ({x['time']}Z)")
        for x in big_wind:
            w(f"  - wind {x['mag']} mph — {x['loc']}, {x['county']} Co., {x['state']} ({x['time']}Z)")
        for x in r["tornado"][:5]:
            w(f"  - tornado — {x['loc']}, {x['county']} Co., {x['state']} ({x['time']}Z): {x['comments'][:140]}")

    # 3. Nguy cơ tại các thành phố
    w("\n## 3. Nguy cơ tại các thành phố [SPC Convective Outlook • WPC Excessive Rainfall] [OFFICIAL]")
    w("| City | ST | SPC D1 | SPC D2 | SPC D3 | ERO D1 | ERO D2 | ERO D3 |")
    w("|---|---|---|---|---|---|---|---|")
    rows = 0
    for r in d["risk"]:
        s = [SPC_TXT.get(r["spc"].get(k), "—") if k in r["spc"] else "err" for k in (1, 2, 3)]
        e = [ERO_TXT.get(r["ero"].get(k), "—") if k in r["ero"] else "err" for k in (1, 2, 3)]
        if d["scope"] == "US" and all(x in ("—", "General t-storms", "err") for x in s + e):
            continue  # toàn quốc: chỉ in thành phố có nguy cơ
        rows += 1
        w(f"| {r['place']} | {r['state']} | " + " | ".join(s + e) + " |")
    if not rows:
        w("| (không thành phố nào trong danh sách nằm trong vùng nguy cơ ≥ Marginal) | | | | | | | |")

    # 4. Nhiệt đới
    w("\n## 4. Bão nhiệt đới — NHC [OFFICIAL]")
    if d["nhc"] is None:
        w("- LỖI: kiểm tra tay https://www.nhc.noaa.gov/")
    elif not d["nhc"]:
        w("- Không có bão đang hoạt động.")
    for s in d["nhc"] or []:
        kt = s.get("intensity")
        try:
            wind = f"{round(int(kt) * 1.151 / 5) * 5} mph ({kt} kt)"
        except (TypeError, ValueError):
            wind = str(kt)
        w(f"- {s.get('classification', '')} {s.get('name', '')} ({s.get('id', '')}): {s.get('latitude', '')} {s.get('longitude', '')}; "
          f"max winds {wind}; {s.get('pressure', '')} mb; moving {s.get('movementDir', '')}° at {s.get('movementSpeed', '')} mph; "
          f"updated {fmt_time(s.get('lastUpdate'))}")
    for basin, txt in (d.get("nhc_two") or {}).items():
        w(f"- TWO {basin}: {txt}")

    # 5. WPC/CPC
    w("\n## 5. Tổng quan toàn quốc — WPC / CPC [OFFICIAL]")
    for p, lab in (("PMDSPD", "WPC Short Range Discussion (1–3 ngày)"), ("PMDEPD", "WPC Extended Discussion (3–7 ngày)")):
        x = (d.get("wpc") or {}).get(p)
        if x:
            w(f"### {lab} — issued {fmt_time(x['issued'])}\n```\n{x['text']}\n```")
    for k, lab in (("610", "CPC 6–10 ngày"), ("814", "CPC 8–14 ngày")):
        x = (d.get("cpc") or {}).get(k)
        if x:
            w(f"- **{lab}:** {x}")

    # 6. Dự báo 7 ngày
    w("\n## 6. Dự báo 7 ngày NWS [OFFICIAL]")
    for name, periods in d["forecasts"].items():
        if not periods:
            continue
        info = d["points"].get(name) or {}
        w(f"### {name} (WFO {info.get('wfo', '?')})")
        for p in periods:
            pop = (p.get("probabilityOfPrecipitation") or {}).get("value")
            w(f"- {p.get('name')}: {p.get('temperature')}°{p.get('temperatureUnit', 'F')}, {p.get('shortForecast')}"
              + (f", {pop}% precip" if pop else "") + f", wind {p.get('windDirection', '')} {p.get('windSpeed', '')}")
        w("")
    if d["afd"]:
        w("### Area Forecast Discussion (trích)")
        for a in d["afd"]:
            w(f"**AFD {a['wfo']}** — issued {fmt_time(a['issued'])}\n```\n{a['text']}\n```")

    # 7. Mô hình
    w("\n## 7. Tín hiệu mô hình [MODEL GUIDANCE — chỉ tham khảo, không phải dự báo chính thức]")
    if d.get("models_used") is None:
        w("- (đã tắt bằng --no-models)")
    elif not d["signals"]:
        w(f"- Không mô hình nào ({', '.join(DET_MODELS)}) vượt ngưỡng tại các thành phố trong {d['models_used']['days']} ngày tới.")
    else:
        w("Ngưỡng: " + "; ".join(v[3] for v in THRESH.values()) + ". Đồng thuận = số mô hình vượt ngưỡng / số mô hình có dữ liệu. "
          "Ensemble = % thành viên vượt ngưỡng.")
        w("| Ngày | Hiện tượng | Độ tin cậy | Thành phố (đồng thuận; khoảng giá trị; ensemble GEFS/ECMWF) |")
        w("|---|---|---|---|")
        groups = {}
        for s in d["signals"]:
            n = int(s["agree"].split("/")[0])
            ens = s["ensemble_pct"]
            top = max(ens.values()) if ens else 0
            conf = "CAO" if n >= 3 and top >= 50 else "TRUNG BÌNH" if n >= 2 or top >= 30 else "THẤP"
            ens_txt = "/".join(f"{ens[m]}%" if m in ens else "—" for m in ENS_MODELS)
            st = CITY_STATE.get(s["place"], "")
            groups.setdefault((s["date"], s["day_index"], s["label"], conf), []).append(
                f"{s['place']}{' ' + st if st and not s['place'].endswith(st) else ''} ({s['agree']}; {s['range']}; {ens_txt})")
        order = {"CAO": 0, "TRUNG BÌNH": 1, "THẤP": 2}
        for (date, di, label, conf), cities in sorted(groups.items(), key=lambda kv: (kv[0][0], order[kv[0][3]], kv[0][2])):
            w(f"| {date} (D{di}) | {label} | {conf} | {', '.join(cities)} |")

    if d["errors"]:
        w("\n## Nguồn bị lỗi — PHẢI kiểm tra tay bằng web")
        for e in d["errors"]:
            w(f"- {e}")
    w("\n_Còn phải kiểm tra tay: SPC Day 4–8, WPC Hazards Outlook 3–7, sông lũ (water.noaa.gov), tin nhà đài — xem SKILL.md._")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--area", help="US (mặc định) hoặc mã bang, cách nhau bằng dấu phẩy: TX,OK")
    g.add_argument("--point", help="lat,lon")
    g.add_argument("--city", help='Tên thành phố, ví dụ "Denver, CO"')
    ap.add_argument("--name", help="Tên hiển thị cho --point")
    ap.add_argument("--days", type=int, default=7, help="Số ngày dự báo NWS (tối đa 7)")
    ap.add_argument("--model-days", type=int, default=10, help="Số ngày mô hình (mặc định 10, tối đa 16)")
    ap.add_argument("--cities", type=int, default=3, help="Số thành phố lấy dự báo NWS mỗi bang")
    ap.add_argument("--afd", type=int, default=2, help="Số bản AFD trích")
    ap.add_argument("--max-alerts", type=int, default=30)
    ap.add_argument("--no-models", action="store_true", help="Bỏ phần mô hình")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    d = collect(args)
    print(json.dumps(d, ensure_ascii=False, indent=1, default=str) if args.json else render(d, args.max_alerts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
