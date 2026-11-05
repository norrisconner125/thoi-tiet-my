"""Tải dữ liệu NOAA cho app (chạy trong GitHub Actions).

- data/CurrentStorms.json : danh sách bão đang hoạt động của NHC
- data/metars-us.json     : quan trắc METAR mới nhất của các trạm Mỹ (Aviation Weather Center, NOAA/NWS)
- data/storm-cones.json   : nón dự báo và đường đi dự báo của từng cơn bão (từ file KMZ của NHC), dạng GeoJSON

Trình duyệt có thể bị chặn khi gọi thẳng các nguồn này, nên app dùng bản sao cùng tên miền.
Mỗi nguồn chạy độc lập: một nguồn lỗi không làm hỏng nguồn kia.
"""
import csv, datetime, gzip, html, io, json, os, re, sys, urllib.request, zipfile
import xml.etree.ElementTree as ET

OUT = sys.argv[1] if len(sys.argv) > 1 else "data"
UA = {"User-Agent": "thoi-tiet-my (github actions)"}
NOW = datetime.datetime.now(datetime.timezone.utc)
os.makedirs(OUT, exist_ok=True)


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def nhc():
    d = json.loads(get("https://www.nhc.noaa.gov/CurrentStorms.json"))
    assert "activeStorms" in d
    d["fetchedAt"] = NOW.isoformat(timespec="seconds")
    json.dump(d, open(f"{OUT}/CurrentStorms.json", "w"), ensure_ascii=False)
    print("NHC:", len(d["activeStorms"]), "bão")
    cones(d["activeStorms"])


# ---------- Nón dự báo bão (KMZ của NHC → GeoJSON) ----------
def kmz_urls(obj, found):
    """Tìm mọi đường dẫn .kmz trong mục của một cơn bão (không phụ thuộc tên trường)."""
    if isinstance(obj, dict):
        for v in obj.values():
            kmz_urls(v, found)
    elif isinstance(obj, list):
        for v in obj:
            kmz_urls(v, found)
    elif isinstance(obj, str) and obj.lower().endswith(".kmz"):
        found.append(obj)
    return found


def kml_root(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".kml"))
        return ET.fromstring(z.read(name))


def local(tag):
    return tag.rsplit("}", 1)[-1]


def coords(text):
    pts = []
    for tok in (text or "").split():
        p = tok.split(",")
        if len(p) >= 2:
            pts.append([round(float(p[0]), 4), round(float(p[1]), 4)])
    return pts


def text_of(el):
    """Chữ thuần của phần mô tả (bỏ thẻ HTML), gọn trên một dòng."""
    if el is None or el.text is None:
        return ""
    t = re.sub(r"<[^>]+>", " ", html.unescape(el.text))
    return re.sub(r"\s+", " ", t).strip()


def placemarks(root):
    for pm in root.iter():
        if local(pm.tag) != "Placemark":
            continue
        name = desc = ""
        geoms = []
        for ch in pm.iter():
            t = local(ch.tag)
            if t == "name" and not name:
                name = (ch.text or "").strip()
            elif t == "description":
                desc = text_of(ch)
            elif t == "Polygon":
                outer = next((c for c in ch.iter() if local(c.tag) == "outerBoundaryIs"), None)
                ring = next((c for c in (outer if outer is not None else ch).iter() if local(c.tag) == "coordinates"), None)
                if ring is not None and len(coords(ring.text)) >= 4:
                    geoms.append({"type": "Polygon", "coordinates": [coords(ring.text)]})
            elif t == "LineString":
                c = next((x for x in ch.iter() if local(x.tag) == "coordinates"), None)
                if c is not None and len(coords(c.text)) >= 2:
                    geoms.append({"type": "LineString", "coordinates": coords(c.text)})
            elif t == "Point":
                c = next((x for x in ch.iter() if local(x.tag) == "coordinates"), None)
                if c is not None and coords(c.text):
                    geoms.append({"type": "Point", "coordinates": coords(c.text)[0]})
        for g in geoms:
            yield name, desc, g


def wind_kt(desc):
    m = re.search(r"(?:Maximum|Max)\s+(?:Sustained\s+)?Wind[^0-9]{0,20}(\d{2,3})\s*(?:knots|kt)", desc, re.I)
    return int(m.group(1)) if m else None


def cones(storms):
    feats = []
    for s in storms:
        sid, name = s.get("id", ""), s.get("name", "")
        for url in kmz_urls(s, []):
            kind = "cone" if "CONE" in url.upper() else "track" if "TRACK" in url.upper() else None
            if not kind:
                continue
            try:
                root = kml_root(get(url))
            except Exception as e:  # noqa: BLE001
                print(f"  bỏ qua {url}: {e}", file=sys.stderr)
                continue
            for pname, desc, g in placemarks(root):
                if kind == "cone" and g["type"] != "Polygon":
                    continue
                props = {"storm": sid, "name": name, "kind": kind if g["type"] != "Point" else "point"}
                if g["type"] == "Point":
                    props.update({"label": pname[:60], "desc": desc[:400], "wind": wind_kt(desc)})
                if kind == "track" and g["type"] == "Polygon":
                    continue
                feats.append({"type": "Feature", "geometry": g, "properties": props})
    json.dump({"fetchedAt": NOW.isoformat(timespec="seconds"), "type": "FeatureCollection", "features": feats},
              open(f"{OUT}/storm-cones.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print("Nón bão:", sum(1 for f in feats if f["properties"]["kind"] == "cone"), "nón,",
          sum(1 for f in feats if f["properties"]["kind"] == "point"), "điểm dự báo")


def num(v):
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


def metars():
    text = gzip.decompress(get("https://aviationweather.gov/data/cache/metars.cache.csv.gz")).decode("utf-8", "replace")
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("raw_text"))
    us = re.compile(r"^(K|PA|PH|PG|TJ|TI)")
    obs = {}
    for r in csv.DictReader(lines[start:]):
        sid = r.get("station_id", "")
        lat, lon = num(r.get("latitude")), num(r.get("longitude"))
        if not us.match(sid) or lat is None or lon is None:
            continue
        try:
            t = datetime.datetime.fromisoformat(r["observation_time"].replace("Z", "+00:00"))
        except Exception:
            continue
        if (NOW - t).total_seconds() > 3 * 3600:
            continue
        o = {
            "id": sid, "lat": round(lat, 3), "lon": round(lon, 3),
            "t": num(r.get("temp_c")), "td": num(r.get("dewpoint_c")),
            "wdir": num(r.get("wind_dir_degrees")), "wspd": num(r.get("wind_speed_kt")), "wgst": num(r.get("wind_gust_kt")),
            "vis": num((r.get("visibility_statute_mi") or "").replace("+", "")),
            "altim": num(r.get("altim_in_hg")), "wx": r.get("wx_string") or "",
            "cat": r.get("flight_category") or "", "raw": r.get("raw_text") or "",
            "time": int(t.timestamp() * 1000),
        }
        if o["altim"]:
            o["altim"] = round(o["altim"], 2)
        prev = obs.get(sid)
        if not prev or o["time"] > prev["time"]:
            obs[sid] = o
    json.dump({"fetchedAt": NOW.isoformat(timespec="seconds"), "obs": list(obs.values())},
              open(f"{OUT}/metars-us.json", "w"), separators=(",", ":"))
    print("METAR:", len(obs), "trạm")


ok = True
for job in (nhc, metars):
    try:
        job()
    except Exception as e:  # noqa: BLE001
        ok = False
        print(f"LỖI {job.__name__}: {e}", file=sys.stderr)
sys.exit(0)  # vẫn triển khai app kể cả khi một nguồn lỗi
