#!/usr/bin/env python3
"""Quét đề tài "Big Picture" kiểu Max Velocity / Ryan Hall từ nguồn chính thức NOAA.

Lấy (chỉ thư viện chuẩn, không cần key):
  1. ENSO: trạng thái cảnh báo + Synopsis (CPC ENSO Discussion) và nhiệt độ mặt biển
     Niño 1+2 / 3 / 3.4 / 4 bốn tuần gần nhất (CPC weekly).
  2. CPC US Hazards Outlook tuần 2 (ngày 8–14): Synopsis + danh sách nguy cơ.
  3. CPC Week 3–4: các đoạn thảo luận chính (MJO, pattern, nhiệt độ, mưa).
  4. CPC Monthly (30 ngày) và Seasonal (90 ngày): đoạn đầu thảo luận
     (thường nhắc El Niño, xoáy cực, SSW, AO).
  5. Kỷ lục: Record Event Reports (RER) của NWS trong N giờ qua, gom theo loại.
  6. Lịch mốc: ngày phát hành sắp tới của CPC/Drought Monitor và ngày lễ gần nhất.

Cách dùng:
  python3 scripts/xu_huong_dai_han.py              # đủ 6 phần, kỷ lục 48 giờ
  python3 scripts/xu_huong_dai_han.py --hours 72   # kỷ lục 72 giờ
  python3 scripts/xu_huong_dai_han.py --only enso,hazards,records
"""
import argparse, concurrent.futures as cf, datetime as dt, html, json, re, sys, urllib.request

UA = {"User-Agent": "thoi-tiet-my (weather briefing script)"}
CPC = "https://www.cpc.ncep.noaa.gov"


def get(url, as_json=False, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read().decode("utf-8", "replace")
    return json.loads(data) if as_json else data


def text_of(page):
    s = re.sub(r"<br\s*/?>", "\n", page, flags=re.I)
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S | re.I)
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    s = re.sub(r"[ \t\xa0]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n\n", s)


def unwrap(s):
    """Nối các dòng bị ngắt cứng trong cùng một đoạn."""
    paras = [re.sub(r"\s*\n\s*", " ", p).strip() for p in re.split(r"\n\s*\n", s)]
    return "\n\n".join(p for p in paras if p)


def cut(s, n):
    s = s.strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " …"


# ---------------------------------------------------------------- 1. ENSO
def enso():
    out = []
    t = text_of(get(f"{CPC}/products/analysis_monitoring/enso_advisory/ensodisc.shtml"))
    m = re.search(r"ENSO Alert System Status:\s*(.+?)\n", t + "\n", re.S)
    status = m.group(1).strip() if m and m.group(1).strip() else ""
    if not status:
        m = re.search(r"ENSO Alert System Status:\s*\n\s*(.+?)\n", t)
        status = m.group(1).strip() if m else "?"
    m = re.search(r"Synopsis:\s*(.+?)\n\s*\n", t, re.S)
    syn = unwrap(m.group(1)) if m else "?"
    out.append(f"Trạng thái: {status}")
    out.append(f"Synopsis: {syn}")

    raw = get(f"{CPC}/data/indices/wksst9120.for").splitlines()
    rows = [l for l in raw if re.match(r"\s*\d{2}[A-Z]{3}\d{4}", l)][-4:]
    out.append("")
    out.append("SST tuần (°C | dị thường °C), nguồn CPC wksst9120:")
    out.append(f"{'Tuần':<11}{'Niño1+2':>14}{'Niño3':>14}{'Niño3.4':>14}{'Niño4':>14}")
    last34 = None
    for l in rows:
        p = l.split()
        cells = [f"{p[i]} | {float(p[i+1]):+.1f}" for i in (1, 3, 5, 7)]
        last34 = float(p[6])
        out.append(f"{p[0]:<11}" + "".join(f"{c:>14}" for c in cells))
    if last34 is not None:
        lvl = ("rất mạnh (≥ +2.0, mức 'Super El Niño' báo chí hay dùng)" if last34 >= 2.0 else
               "mạnh (+1.5 → +2.0)" if last34 >= 1.5 else
               "trung bình (+1.0 → +1.5)" if last34 >= 1.0 else
               "yếu (+0.5 → +1.0)" if last34 >= 0.5 else
               "La Niña (≤ −0.5)" if last34 <= -0.5 else "trung tính")
        out.append(f"→ Niño 3.4 tuần gần nhất {last34:+.1f}°C: {lvl}. "
                   "Lưu ý: xếp loại chính thức dùng trung bình 3 tháng (ONI), không phải số tuần.")
    return "\n".join(out)


# ---------------------------------------------------------------- 2. Hazards week 2
def hazards(chars=2600):
    t = text_of(get(f"{CPC}/products/predictions/threats/threats.php"))
    i = t.find("US Hazards Outlook")
    if i < 0:
        return "Không tìm thấy US Hazards Outlook."
    head = t[max(0, i - 120):i]
    m = re.search(r"Valid (.+?\d{4}) to (.+?\d{4})", head + t[i:i + 200])
    valid = f"Hiệu lực: {m.group(1)} → {m.group(2)}" if m else ""
    body = t[i:]
    j = body.find("Detailed Summary")
    core = body[:j] if j > 0 else body[:chars]
    core = re.sub(r"\s+", " ", core)
    core = re.sub(r"^US Hazards Outlook\s*", "", core)
    core = core.replace("Synopsis:", "\nSynopsis:")
    core = re.sub(r"\s*Hazards\s+(?=(Moderate|Slight|High) risk)", "\nHazards:\n - ", core, count=1)
    core = re.sub(r"\.\s+(?=(Moderate|Slight|High) risk)", ".\n - ", core)
    return (valid + "\n" + cut(core, chars)).strip()


# ---------------------------------------------------------------- 3. Week 3-4
def week34(paras=4, chars=900):
    t = text_of(get(f"{CPC}/products/predictions/WK34/texts/week34fcst.txt"))
    ps = [p.strip() for p in t.split("\n\n") if p.strip()]
    head = [p for p in ps[:6] if re.search(r"(EST|EDT) \w{3} \w{3} \d", p) or "Valid" in p]
    body = [p for p in ps if len(p) > 200][:paras]
    out = head[:2] + [cut(unwrap(p), chars) for p in body]
    nxt = [p for p in ps if p.startswith("The next week 3-4")]
    return "\n\n".join(out + nxt[:1])


# ---------------------------------------------------------------- 4. Monthly / Seasonal
def long_range(kind, chars=1800):
    page = "fxus07" if kind == "monthly" else "fxus05"
    t = text_of(get(f"{CPC}/products/predictions/long_range/{page}.html"))
    i = t.find("Prognostic Discussion")
    if i < 0:
        return "Không đọc được thảo luận."
    s = t[i:]
    lines = [l.strip() for l in s.splitlines()]
    head = " | ".join(l for l in lines[:6] if l)[:200]
    body = unwrap("\n".join(lines[3:]))
    keys = ["SSW", "polar vortex", "Arctic Oscillation", "El Nino", "MJO", "record"]
    found = [k for k in keys if k.lower() in body.lower()]
    return f"{head}\nTừ khóa có nhắc: {', '.join(found) or '—'}\n\n{cut(body, chars)}"


# ---------------------------------------------------------------- 5. Records (RER)
REC_KIND = [  # thứ tự quan trọng: mẫu cụ thể trước
    ("đêm ấm kỷ lục (thấp nhất cao)", r"WARMEST LOW|WARM LOW|HIGH MINIMUM|HIGHEST MINIMUM"),
    ("ngày lạnh kỷ lục (cao nhất thấp)", r"COOL MAXIMUM|COOLEST MAXIMUM|COLD HIGH|COOLEST HIGH|LOW MAXIMUM|LOWEST MAXIMUM"),
    ("mưa ngày", r"RAINFALL|PRECIPITATION"), ("tuyết", r"SNOW"),
    ("nóng (cao nhất)", r"HIGH TEMPERATURE|MAXIMUM TEMPERATURE|RECORD HIGH|WARMEST"),
    ("lạnh (thấp nhất)", r"LOW TEMPERATURE|MINIMUM TEMPERATURE|RECORD LOW|COLDEST"),
]


def records(hours=48, max_list=25):
    lst = get("https://api.weather.gov/products/types/RER", as_json=True)["@graph"]
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    recent = [p for p in lst if dt.datetime.fromisoformat(p["issuanceTime"]) >= since]
    if not recent:
        return f"Không có Record Event Report nào trong {hours} giờ qua."

    def one(p):
        try:
            txt = get(f"https://api.weather.gov/products/{p['id']}", as_json=True)["productText"]
        except Exception as e:  # noqa
            return None
        heads = re.findall(r"\.\.\.(.+?)\.\.\.", txt.replace("\n", " "))
        heads = [h.strip() for h in heads if "RECORD" in h.upper()]
        return p["issuanceTime"][:16].replace("T", " ") + "Z", p["issuingOffice"], heads, txt

    with cf.ThreadPoolExecutor(8) as ex:
        got = [r for r in ex.map(one, recent[:60]) if r]
    tally = {}
    lines = []
    for t, off, heads, txt in got:
        for h in heads or ["(không có tiêu đề)"]:
            k = next((name for name, rx in REC_KIND if re.search(rx, h.upper())), "khác")
            tally[k] = tally.get(k, 0) + 1
            lines.append(f"  {t} {off:<5} {h.title()}")
    out = [f"{len(got)} bản tin RER trong {hours} giờ qua. Theo loại: " +
           ", ".join(f"{k} {v}" for k, v in sorted(tally.items(), key=lambda x: -x[1]))]
    out += lines[:max_list]
    if len(lines) > max_list:
        out.append(f"  … và {len(lines) - max_list} kỷ lục khác.")
    out.append("Gợi ý: nhiều kỷ lục cùng loại ở cùng vùng = đề tài 'Records & Rare'. "
               "Mở bản tin gốc để lấy số cũ/số mới và năm của kỷ lục cũ.")
    return "\n".join(out)


# ---------------------------------------------------------------- 6. Calendar
def nth_weekday(y, m, wd, n):
    d = dt.date(y, m, 1)
    d += dt.timedelta(days=(wd - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def holidays(y):
    return {
        "New Year's Day": dt.date(y, 1, 1), "Groundhog Day": dt.date(y, 2, 2),
        "Memorial Day": nth_weekday(y, 6, 0, 1) - dt.timedelta(days=7),
        "Independence Day": dt.date(y, 7, 4), "Labor Day": nth_weekday(y, 9, 0, 1),
        "Halloween": dt.date(y, 10, 31), "Thanksgiving": nth_weekday(y, 11, 3, 4),
        "Christmas": dt.date(y, 12, 25),
    }


def calendar(today=None):
    today = today or dt.date.today()
    ev = []
    for y in (today.year, today.year + 1):
        for name, d in holidays(y).items():
            ev.append((d, f"Lễ: {name}"))
        for m in range(1, 13):
            ev.append((nth_weekday(y, m, 3, 2), "CPC ENSO Discussion (thứ Năm tuần 2)"))
            ev.append((nth_weekday(y, m, 3, 3), "CPC dự báo tháng + mùa (thứ Năm tuần 3)"))
            nxt = dt.date(y + (m == 12), m % 12 + 1, 1)
            ev.append((nxt - dt.timedelta(days=1), "CPC cập nhật dự báo tháng tới (ngày cuối tháng)"))
        ev.append((dt.date(y, 6, 1), "Mở mùa bão Đại Tây Dương"))
        ev.append((dt.date(y, 11, 30), "Kết thúc mùa bão Đại Tây Dương"))
    for k in range(0, 15):
        d = today + dt.timedelta(days=k)
        if d.weekday() == 3:
            ev.append((d, "US Drought Monitor (thứ Năm)"))
        if d.weekday() == 4:
            ev.append((d, "CPC Week 3–4 (thứ Sáu)"))
    soon = sorted({e for e in ev if today <= e[0] <= today + dt.timedelta(days=21)})
    out = [f"{d:%a %d/%m}: {name}" + (f"  (còn {(d - today).days} ngày)" if name.startswith("Lễ") else "")
           for d, name in soon]
    out.append("Ghi nhớ: đề tài gắn mốc lễ nên ra 5–10 ngày trước lễ (kiểu 'Before Thanksgiving').")
    return "\n".join(out)


SECTIONS = {
    "enso": ("1. ENSO / EL NIÑO", enso),
    "hazards": ("2. CPC HAZARDS OUTLOOK TUẦN 2 (ngày 8–14)", hazards),
    "week34": ("3. CPC WEEK 3–4", week34),
    "monthly": ("4a. CPC DỰ BÁO THÁNG", lambda: long_range("monthly")),
    "seasonal": ("4b. CPC DỰ BÁO MÙA", lambda: long_range("seasonal")),
    "records": ("5. KỶ LỤC NWS (RER)", None),
    "calendar": ("6. LỊCH MỐC 3 TUẦN TỚI", calendar),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hours", type=int, default=48, help="Cửa sổ thời gian lấy kỷ lục RER (giờ)")
    ap.add_argument("--only", help="Chỉ chạy các phần, ví dụ enso,hazards,records")
    a = ap.parse_args()
    keys = [k.strip() for k in a.only.split(",")] if a.only else list(SECTIONS)
    now = dt.datetime.now(dt.timezone.utc)
    print(f"QUÉT XU HƯỚNG BIG PICTURE — {now:%Y-%m-%d %H:%M}Z")
    print("Nguồn: NOAA CPC, NWS. Mọi số trong video phải lấy lại từ đây hoặc bản gốc, kèm giờ phát hành.\n")
    errors = []
    jobs = {}
    with cf.ThreadPoolExecutor(6) as ex:
        for k in keys:
            if k not in SECTIONS:
                print(f"(bỏ qua phần không biết: {k})")
                continue
            fn = (lambda: records(a.hours)) if k == "records" else SECTIONS[k][1]
            jobs[k] = ex.submit(fn)
        for k, f in jobs.items():
            title = SECTIONS[k][0]
            print("=" * 78 + f"\n{title}\n" + "=" * 78)
            try:
                print(f.result())
            except Exception as e:  # noqa
                errors.append(f"{title}: {e}")
                print(f"LỖI: {e}")
            print()
    if errors:
        print("NGUỒN LỖI (kiểm tra tay trên web, xem references/tim-tin-kieu-max-ryan.md):")
        for e in errors:
            print(" - " + e)


if __name__ == "__main__":
    sys.exit(main())
