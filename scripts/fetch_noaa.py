"""Tải dữ liệu NOAA cho app (chạy trong GitHub Actions).

- data/CurrentStorms.json : danh sách bão đang hoạt động của NHC
- data/metars-us.json     : quan trắc METAR mới nhất của các trạm Mỹ (Aviation Weather Center, NOAA/NWS)

Trình duyệt có thể bị chặn khi gọi thẳng các nguồn này, nên app dùng bản sao cùng tên miền.
Mỗi nguồn chạy độc lập: một nguồn lỗi không làm hỏng nguồn kia.
"""
import csv, datetime, gzip, io, json, os, re, sys, urllib.request

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
