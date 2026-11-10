#!/usr/bin/env python3
"""Tổng hợp dữ liệu chính thức NOAA/NWS cho bản tin thời tiết Mỹ (tiếng Việt).

Ví dụ:
  python3 tong_hop_nws.py --area TX            # một bang
  python3 tong_hop_nws.py --area TX,OK,KS      # nhiều bang
  python3 tong_hop_nws.py --area US            # toàn quốc
  python3 tong_hop_nws.py --point 29.76,-95.37 --name Houston
  python3 tong_hop_nws.py --city "Denver, CO"
  python3 tong_hop_nws.py --area FL --json     # dữ liệu thô dạng JSON

Nguồn: api.weather.gov (cảnh báo, dự báo 7 ngày, AFD), SPC (Convective Outlook ngày 1–3),
WPC (Excessive Rainfall Outlook ngày 1–3), NHC (bão đang hoạt động).
Chỉ dùng thư viện chuẩn Python 3.9+. Mỗi nguồn chạy độc lập: một nguồn lỗi vẫn in phần còn lại.
"""
import argparse, concurrent.futures as cf, datetime as dt, json, re, sys, urllib.parse, urllib.request

try:
    from zoneinfo import ZoneInfo
    VN = ZoneInfo("Asia/Ho_Chi_Minh")
except Exception:  # pragma: no cover
    VN = dt.timezone(dt.timedelta(hours=7))

UA = {"User-Agent": "thoi-tiet-my-skill (ban tin thoi tiet)", "Accept": "application/geo+json, application/json"}
NOW = dt.datetime.now(dt.timezone.utc)
ERRORS = []

# 2–3 thành phố chính mỗi bang (lat, lon) — dùng cho dự báo 7 ngày và kiểm tra vùng nguy cơ SPC/WPC.
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
NATIONAL = ["New York", "Washington", "Atlanta", "Miami", "Chicago", "Dallas", "Houston", "Denver", "Phoenix", "Los Angeles", "Seattle", "Minneapolis"]

# Thứ tự ưu tiên hiện tượng (nhỏ = nguy hiểm hơn). Không có trong danh sách → xếp theo severity.
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
SPC_VI = {"TSTM": "dông thường", "MRGL": "1/5 Marginal", "SLGT": "2/5 Slight", "ENH": "3/5 Enhanced", "MDT": "4/5 Moderate", "HIGH": "5/5 High"}
ERO_RANK = {"MRGL": 1, "SLGT": 2, "MDT": 3, "HIGH": 4}
ERO_VI = {1: "1/4 Marginal", 2: "2/4 Slight", 3: "3/4 Moderate", 4: "4/4 High"}


# ---------------- tiện ích ----------------
def get(url, as_json=True, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return json.loads(data) if as_json else data.decode("utf-8", "replace")


def safe(label, fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception as e:  # ghi lại để người dùng biết phải kiểm tra tay
        ERRORS.append(f"{label}: {type(e).__name__}: {e}")
        return None


def parse_time(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_time(s):
    """'2026-11-10T18:00:00-06:00' → '18:00 10/11 (giờ đ.p. UTC-6) = 07:00 11/11 giờ VN'."""
    t = parse_time(s)
    if not t:
        return "—"
    off = t.utcoffset()
    h = int(off.total_seconds() // 3600) if off is not None else 0
    v = t.astimezone(VN)
    return f"{t:%H:%M %d/%m} (UTC{h:+d}) = {v:%H:%M %d/%m} giờ VN"


def f2c(f):
    return round((f - 32) * 5 / 9)


def mph_text(s):
    """'10 to 15 mph' → '10 to 15 mph (16–24 km/h)'."""
    nums = [int(n) for n in re.findall(r"\d+", s or "")]
    if not nums:
        return s or ""
    kmh = "–".join(str(round(n * 1.609)) for n in nums)
    return f"{s} ({kmh} km/h)"


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
    for poly in polys:
        if poly and in_ring(lon, lat, poly[0]) and not any(in_ring(lon, lat, h) for h in poly[1:]):
            return True
    return False


# ---------------- nguồn dữ liệu ----------------
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
        out.append({
            "event": p.get("event", ""), "severity": p.get("severity", "Unknown"), "urgency": p.get("urgency"),
            "certainty": p.get("certainty"), "area": p.get("areaDesc", ""), "sender": p.get("senderName", ""),
            "onset": p.get("onset") or p.get("effective"), "ends": p.get("ends") or p.get("expires"),
            "headline": (params.get("NWSheadline") or [p.get("headline") or ""])[0],
            "maxWindGust": (params.get("maxWindGust") or [None])[0], "maxHailSize": (params.get("maxHailSize") or [None])[0],
            "tornadoDetection": (params.get("tornadoDetection") or [None])[0],
            "description": (p.get("description") or "").strip(), "instruction": (p.get("instruction") or "").strip(),
            "id": p.get("id"),
        })

    def rank(a):
        ev = a["event"]
        desc = a["description"].upper()
        if ev == "Tornado Warning" and "TORNADO EMERGENCY" in desc:
            ev = "Tornado Emergency"
        if ev == "Flash Flood Warning" and "FLASH FLOOD EMERGENCY" in desc:
            ev = "Flash Flood Emergency"
        a["event_display"] = ev if ev != a["event"] else a["event"]
        pr = PRIORITY.index(ev) if ev in PRIORITY else len(PRIORITY)
        return (pr, SEV.get(a["severity"], 4))

    out.sort(key=rank)
    return out


def spc_day(day):
    d = get(f"https://www.spc.noaa.gov/products/outlook/day{day}otlk_cat.nolyr.geojson")
    return d.get("features", [])


def ero_day(day):
    d = get(f"https://www.wpc.ncep.noaa.gov/exper/eromap/geojson/Day{day}_Latest.geojson")
    return d.get("features", [])


def spc_at(features, lat, lon):
    best = None
    for f in features or []:
        lab = (f.get("properties") or {}).get("LABEL")
        if lab in SPC_RANK and in_geom(lon, lat, f.get("geometry")):
            if best is None or SPC_RANK[lab] > SPC_RANK[best]:
                best = lab
    return best


def ero_at(features, lat, lon):
    best = 0
    for f in features or []:
        p = f.get("properties") or {}
        txt = " ".join(str(v) for v in p.values()).upper()
        lvl = max([r for k, r in ERO_RANK.items() if re.search(rf"\b{k}", txt)] + [0])
        if not lvl:
            m = re.search(r"\b(MARGINAL|SLIGHT|MODERATE|HIGH)\b", txt)
            lvl = {"MARGINAL": 1, "SLIGHT": 2, "MODERATE": 3, "HIGH": 4}.get(m.group(1), 0) if m else 0
        if lvl > best and in_geom(lon, lat, f.get("geometry")):
            best = lvl
    return best


def nhc():
    d = get("https://www.nhc.noaa.gov/CurrentStorms.json")
    return d.get("activeStorms", [])


def point_info(lat, lon):
    p = get(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}")["properties"]
    rel = (p.get("relativeLocation") or {}).get("properties") or {}
    return {"wfo": p.get("gridId"), "forecast": p.get("forecast"), "tz": p.get("timeZone"),
            "place": f"{rel.get('city', '')}, {rel.get('state', '')}".strip(", ")}


def forecast(url, days):
    periods = get(url)["properties"]["periods"]
    return periods[: days * 2]


def afd(wfo, chars=1800):
    lst = get(f"https://api.weather.gov/products/types/AFD/locations/{wfo}")
    g = lst.get("@graph") or []
    if not g:
        return None
    prod = get(f"https://api.weather.gov/products/{g[0]['id']}")
    text = prod.get("productText", "")
    m = re.search(r"\.(KEY MESSAGES|SYNOPSIS|WHAT HAS CHANGED)[^\n]*\n(.*?)(?=\n&&|\n\.[A-Z][A-Z /]+\.\.\.)", text, re.S)
    body = (m.group(0) if m else text)
    body = re.sub(r"[ \t]+", " ", body).strip()
    return {"wfo": wfo, "issued": prod.get("issuanceTime"), "text": body[:chars] + ("…" if len(body) > chars else "")}


def geocode(name):
    q = name.split(",")[0].strip()
    st = name.split(",")[1].strip().upper() if "," in name else None
    d = get("https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
        {"name": q, "count": 10, "countryCode": "US", "language": "en"}))
    res = d.get("results") or []
    if st:
        res = [r for r in res if st in (r.get("admin1_code") or r.get("admin1", "")).upper()
               or STATE_NAMES.get(st, "~").upper() == (r.get("admin1") or "").upper()] or res
    if not res:
        raise ValueError(f"không tìm thấy '{name}'")
    r = res[0]
    return r["name"], r["latitude"], r["longitude"]


STATE_NAMES = {"AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado", "CT": "Connecticut",
               "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
               "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
               "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
               "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
               "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
               "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
               "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
               "PR": "Puerto Rico", "VI": "U.S. Virgin Islands", "GU": "Guam"}


# ---------------- tổng hợp ----------------
def collect(args):
    if args.point or args.city:
        if args.city:
            name, lat, lon = geocode(args.city)
        else:
            lat, lon = (float(x) for x in args.point.split(","))
            name = args.name or f"{lat:.2f},{lon:.2f}"
        places, area, point = [(name, lat, lon)], None, (lat, lon)
    else:
        area = args.area.upper().replace(" ", "")
        point = None
        if area == "US":
            allc = {c[0]: c for v in CITIES.values() for c in v}
            places = [allc[n] for n in NATIONAL if n in allc]
        else:
            places = []
            for st in area.split(","):
                if st not in CITIES:
                    raise SystemExit(f"Mã bang không hợp lệ: {st}")
                places += CITIES[st][: args.cities]

    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        f_alerts = ex.submit(safe, "Cảnh báo NWS", alerts, area, point)
        f_spc = {d: ex.submit(safe, f"SPC ngày {d}", spc_day, d) for d in (1, 2, 3)}
        f_ero = {d: ex.submit(safe, f"WPC ERO ngày {d}", ero_day, d) for d in (1, 2, 3)}
        f_nhc = ex.submit(safe, "NHC", nhc)
        f_pts = {p[0]: ex.submit(safe, f"points {p[0]}", point_info, p[1], p[2]) for p in places}
        pts = {k: v.result() for k, v in f_pts.items()}
        f_fc = {k: ex.submit(safe, f"dự báo {k}", forecast, v["forecast"], args.days) for k, v in pts.items() if v and v.get("forecast")}
        wfos = []
        for v in pts.values():
            if v and v["wfo"] and v["wfo"] not in wfos:
                wfos.append(v["wfo"])
        f_afd = {w: ex.submit(safe, f"AFD {w}", afd, w) for w in wfos[: args.afd]}

        spc = {d: f.result() for d, f in f_spc.items()}
        ero = {d: f.result() for d, f in f_ero.items()}
        risk = []
        for name, lat, lon in places:
            risk.append({"place": name,
                         "spc": {d: spc_at(spc[d], lat, lon) for d in spc if spc[d] is not None},
                         "ero": {d: ero_at(ero[d], lat, lon) for d in ero if ero[d] is not None}})
        return {
            "generated_utc": NOW.isoformat(timespec="seconds"),
            "generated_vn": NOW.astimezone(VN).strftime("%H:%M %d/%m/%Y"),
            "scope": area or places[0][0],
            "alerts": f_alerts.result(),
            "risk": risk,
            "spc_max": {d: max([SPC_RANK.get((f.get("properties") or {}).get("LABEL"), -1) for f in spc[d]] + [-1])
                        for d in spc if spc[d] is not None},
            "nhc": f_nhc.result(),
            "points": pts,
            "forecasts": {k: f.result() for k, f in f_fc.items()},
            "afd": [f.result() for f in f_afd.values() if f.result()],
            "errors": ERRORS,
        }


def render(d, max_alerts):
    L = []
    w = L.append
    w(f"# DỮ LIỆU NWS/NOAA — {d['scope']} — lấy lúc {d['generated_vn']} giờ VN ({d['generated_utc']} UTC)\n")

    al = d["alerts"]
    w("## 1. Cảnh báo đang hiệu lực [api.weather.gov]")
    if al is None:
        w("- LỖI: không lấy được cảnh báo → kiểm tra tay https://www.weather.gov/ hoặc https://api.weather.gov/alerts/active")
    elif not al:
        w("- KHÔNG có cảnh báo/khuyến cáo nào đang hiệu lực. → Dùng Nhánh B (dự báo 7 ngày + mô hình).")
    else:
        cnt = {}
        for a in al:
            cnt[a["event_display"]] = cnt.get(a["event_display"], 0) + 1
        w("- Tổng: " + "; ".join(f"{k} ×{v}" for k, v in sorted(cnt.items(), key=lambda kv: PRIORITY.index(kv[0]) if kv[0] in PRIORITY else 999)))
        w("")
        seen = set()
        shown = 0
        for a in al:
            key = (a["event_display"], a["area"][:80], a["ends"])
            if key in seen:
                continue
            seen.add(key)
            if shown >= max_alerts:
                w(f"- … còn {len(al) - shown} cảnh báo khác (dùng --max-alerts hoặc --json)")
                break
            shown += 1
            extra = []
            if a["maxWindGust"]:
                extra.append(f"gió giật {mph_text(a['maxWindGust'])}")
            if a["maxHailSize"]:
                try:
                    extra.append(f"mưa đá {a['maxHailSize']} inch ({float(a['maxHailSize']) * 2.54:.1f} cm)")
                except ValueError:
                    extra.append(f"mưa đá {a['maxHailSize']}")
            if a["tornadoDetection"]:
                extra.append(f"lốc xoáy: {a['tornadoDetection']}")
            w(f"### {a['event_display']} [{a['severity']}/{a['urgency']}] — {a['sender']}")
            w(f"- Khu vực: {a['area'][:400]}")
            w(f"- Hiệu lực: {fmt_time(a['onset'])} → {fmt_time(a['ends'])}")
            if extra:
                w("- " + "; ".join(extra))
            if a["headline"]:
                w(f"- Tiêu đề: {a['headline'][:300]}")
            desc = re.sub(r"\s+", " ", a["description"])[:500]
            if desc:
                w(f"- Mô tả: {desc}{'…' if len(a['description']) > 500 else ''}")
            w("")

    w("\n## 2. Nguy cơ tại các thành phố [SPC Convective Outlook • WPC Excessive Rainfall]")
    if d["spc_max"]:
        w("- Mức cao nhất toàn quốc SPC: " + ", ".join(
            f"ngày {k}: {SPC_VI.get([l for l, r in SPC_RANK.items() if r == v][0], '—') if v >= 0 else 'không có dông'}"
            for k, v in sorted(d["spc_max"].items())))
    w("| Thành phố | SPC ngày 1 | SPC ngày 2 | SPC ngày 3 | ERO ngày 1 | ERO ngày 2 | ERO ngày 3 |")
    w("|---|---|---|---|---|---|---|")
    for r in d["risk"]:
        s = [SPC_VI.get(r["spc"].get(k), "—") if k in r["spc"] else "lỗi" for k in (1, 2, 3)]
        e = [ERO_VI.get(r["ero"].get(k), "—") if k in r["ero"] else "lỗi" for k in (1, 2, 3)]
        w(f"| {r['place']} | " + " | ".join(s + e) + " |")

    w("\n## 3. Bão nhiệt đới [NHC]")
    if d["nhc"] is None:
        w("- LỖI: kiểm tra tay https://www.nhc.noaa.gov/")
    elif not d["nhc"]:
        w("- Không có bão đang hoạt động (vẫn nên xem Tropical Weather Outlook 7 ngày: https://www.nhc.noaa.gov/gtwo.php)")
    for s in d["nhc"] or []:
        kt = s.get("intensity")
        try:
            wind = f"{kt} kt ≈ {round(int(kt) * 1.151)} mph ≈ {round(int(kt) * 1.852)} km/h"
        except (TypeError, ValueError):
            wind = str(kt)
        w(f"- {s.get('classification', '')} {s.get('name', '')} ({s.get('id', '')}): vị trí {s.get('latitude', '')}, {s.get('longitude', '')}; "
          f"gió {wind}; áp suất {s.get('pressure', '')} mb; hướng {s.get('movementDir', '')}° {s.get('movementSpeed', '')} mph; "
          f"cập nhật {fmt_time(s.get('lastUpdate'))}")

    w("\n## 4. Dự báo chính thức NWS")
    for name, periods in d["forecasts"].items():
        if not periods:
            continue
        info = d["points"].get(name) or {}
        w(f"### {name} (WFO {info.get('wfo', '?')}, {info.get('tz', '')})")
        for p in periods:
            t = p.get("temperature")
            unit = p.get("temperatureUnit", "F")
            temp = f"{t}°F/{f2c(t)}°C" if isinstance(t, (int, float)) and unit == "F" else f"{t}°{unit}"
            pop = ((p.get("probabilityOfPrecipitation") or {}).get("value"))
            w(f"- {p.get('name')}: {temp}, {p.get('shortForecast')}"
              + (f", mưa {pop}%" if pop else "") + f", gió {mph_text(p.get('windDirection', '') + ' ' + p.get('windSpeed', ''))}")
        w("")

    if d["afd"]:
        w("## 5. Area Forecast Discussion (trích)")
        for a in d["afd"]:
            w(f"### AFD {a['wfo']} — phát hành {fmt_time(a['issued'])}")
            w("```\n" + a["text"] + "\n```")

    if d["errors"]:
        w("\n## Nguồn bị lỗi (PHẢI kiểm tra tay bằng WebFetch/WebSearch)")
        for e in d["errors"]:
            w(f"- {e}")
    w("\n_Cần bổ sung: SPC Day 4–8, WPC Hazards 3–7, CPC 6–10/8–14, mô hình, và tin nhà đài — xem SKILL.md._")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--area", help="Mã bang, cách nhau bằng dấu phẩy (TX,OK) hoặc US")
    g.add_argument("--point", help="lat,lon")
    g.add_argument("--city", help='Tên thành phố, ví dụ "Denver, CO"')
    ap.add_argument("--name", help="Tên hiển thị cho --point")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--cities", type=int, default=3, help="Số thành phố mỗi bang (mặc định 3)")
    ap.add_argument("--afd", type=int, default=2, help="Số bản AFD trích (mặc định 2)")
    ap.add_argument("--max-alerts", type=int, default=25)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    d = collect(args)
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=1, default=str))
    else:
        print(render(d, args.max_alerts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
