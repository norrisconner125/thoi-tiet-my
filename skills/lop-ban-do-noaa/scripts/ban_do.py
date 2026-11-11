"""Bộ vẽ khung bản đồ 1920×1080 kiểu bản tin: nền ảnh vệ tinh + lớp dữ liệu NOAA + ranh giới bang/hạt + chữ.

Chỉ cần Python 3.10+, Pillow và Internet. Mọi lớp lấy ảnh đúng khung (Web Mercator, EPSG:3857) từ dịch vụ chính thức:
  WMS (nowCOAST, NCEP MRMS, IEM) — GetMap theo bbox; ArcGIS (NWS mapservices) — export theo bbox;
  XYZ (IEM: radar từng trạm, HRRR) và ảnh nền (USGS / NASA GIBS) — ghép ô 256 px rồi cắt.
"""
import io, json, math, os, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

GOC = os.path.dirname(os.path.abspath(__file__))
TAI = os.path.join(os.path.dirname(GOC), "assets")
W, H = 1920, 1080
R = 6378137.0
UA = {"User-Agent": "Mozilla/5.0 (weather-map-renderer)"}

LOP = json.load(open(os.path.join(GOC, "lop.json"), encoding="utf-8"))
BYID = {o["id"]: o for o in LOP["lop"]}
VUNG = json.load(open(os.path.join(GOC, "vung.json"), encoding="utf-8"))

MAU = {"trang": (255, 255, 255), "cam": (255, 176, 74), "tim": (201, 184, 255), "vang": (255, 216, 74),
       "do": (255, 75, 75), "xanh": (127, 208, 255), "xam": (170, 178, 192)}


def font(ten, co):
    return ImageFont.truetype(os.path.join(TAI, "fonts", ten), co)


F_DAM = lambda co: font("BarlowCondensed_800ExtraBold.ttf", co)
F_DAM7 = lambda co: font("BarlowCondensed_700Bold.ttf", co)
F_VUA = lambda co: font("BarlowCondensed_600SemiBold.ttf", co)
F_NHO = lambda co: font("Inter_500Medium.ttf", co)


# ---------------- Tải có thử lại (máy chủ NWS đôi khi trả 504) ----------------
def tai(url, lan=4, cho=60):
    loi = None
    for k in range(lan):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=cho) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            loi = e
            time.sleep(1.5 * (k + 1))
    raise RuntimeError(f"không tải được {url[:120]}… ({loi})")


def tai_anh(url, **kw):
    b = tai(url, **kw)
    try:
        return Image.open(io.BytesIO(b)).convert("RGBA")
    except Exception as e:
        raise RuntimeError(f"máy chủ không trả ảnh: {b[:160]!r}") from e


# ---------------- Khung nhìn Web Mercator ----------------
def merc(lon, lat):
    lat = max(-85.0, min(85.0, lat))
    return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


class Khung:
    """bbox = (lat0, lon0, lat1, lon1). Mở rộng cho đúng tỉ lệ 16:9; k = độ lớn ảnh vẽ so với 1920×1080 (để đẩy zoom chậm)."""

    def __init__(self, bbox, k=1.08):
        la0, lo0, la1, lo1 = bbox
        x0, y0 = merc(lo0, la0); x1, y1 = merc(lo1, la1)
        cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, abs(x1 - x0), abs(y1 - y0)
        if w / h > W / H: h = w * H / W
        else: w = h * W / H
        w *= k; h *= k
        self.x0, self.x1, self.y0, self.y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
        self.rw, self.rh, self.k = round(W * k), round(H * k), k
        self.tam = (math.degrees(cx / R), math.degrees(2 * math.atan(math.exp(cy / R)) - math.pi / 2))

    @property
    def bbox3857(self):
        return f"{self.x0:.2f},{self.y0:.2f},{self.x1:.2f},{self.y1:.2f}"

    def px(self, lon, lat, s=1.0):
        x, y = merc(lon, lat)
        return ((x - self.x0) / (self.x1 - self.x0) * self.rw * s, (self.y1 - y) / (self.y1 - self.y0) * self.rh * s)

    def rong_do(self):
        return math.degrees((self.x1 - self.x0) / R)


def vung_bbox(v):
    """'TX' | 'US' | [lat0, lon0, lat1, lon1] → bbox, có lề 4%."""
    if isinstance(v, str):
        if v.upper() not in VUNG: raise SystemExit(f"không biết vùng '{v}'. Dùng mã bang (TX, OK…), 'US', hoặc bbox [lat0, lon0, lat1, lon1].")
        _, la0, lo0, la1, lo1 = VUNG[v.upper()]
    else:
        la0, lo0, la1, lo1 = v
    dla, dlo = (la1 - la0) * .04, (lo1 - lo0) * .04
    return (la0 - dla, lo0 - dlo, la1 + dla, lo1 + dlo)


# ---------------- Ghép ô XYZ ----------------
def ghep_o(kh, mau_url, zmax, nen=None):
    mpp = (kh.x1 - kh.x0) / kh.rw
    z = max(1, min(zmax, math.ceil(math.log2(2 * math.pi * R / (256 * mpp)))))
    n, cz = 2 ** z, 2 * math.pi * R / 2 ** z
    tx0, tx1 = math.floor((kh.x0 + math.pi * R) / cz), math.floor((kh.x1 + math.pi * R) / cz)
    ty0, ty1 = math.floor((math.pi * R - kh.y1) / cz), math.floor((math.pi * R - kh.y0) / cz)
    ty0, ty1 = max(0, ty0), min(n - 1, ty1)
    anh = Image.new("RGBA", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), (0, 0, 0, 0))
    o = [(x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]

    def lay(xy):
        x, y = xy
        try:
            return xy, tai_anh(mau_url(z, x % n, y), lan=3, cho=40)
        except Exception:
            return xy, (nen(z, x % n, y) if nen else None)

    with ThreadPoolExecutor(8) as ex:
        for (x, y), im in ex.map(lay, o):
            if im is not None:
                anh.paste(im.resize((256, 256)), ((x - tx0) * 256, (y - ty0) * 256))
    # cắt đúng khung
    gx0, gy0 = tx0 * cz - math.pi * R, math.pi * R - ty0 * cz
    s = 256 / cz
    box = ((kh.x0 - gx0) * s, (gy0 - kh.y1) * s, (kh.x1 - gx0) * s, (gy0 - kh.y0) * s)
    return anh.resize((kh.rw, kh.rh), Image.LANCZOS, box=box)


# ---------------- Nền ảnh vệ tinh ----------------
USGS = "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
GIBS = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg"


def nen_ve_tinh(kh):
    def gibs(z, x, y):
        # ô ngoài vùng USGS: lấy Blue Marble ở mức ≤ 8 rồi phóng
        zz = min(z, 8); d = 2 ** (z - zz)
        try:
            im = tai_anh(GIBS.format(z=zz, x=x // d, y=y // d), lan=2)
            s = 256 // d
            return im.crop(((x % d) * s, (y % d) * s, (x % d + 1) * s, (y % d + 1) * s))
        except Exception:
            return None
    im = ghep_o(kh, lambda z, x, y: USGS.format(z=z, x=x, y=y), 16, nen=gibs).convert("RGB")
    im = ImageEnhance.Color(im).enhance(.82)
    im = ImageEnhance.Brightness(im).enhance(.78)       # tối bớt để lớp dữ liệu và chữ nổi
    return im.convert("RGBA")


# ---------------- Ranh giới (us-atlas, U.S. Census) ----------------
_TOPO = {}


def topo(ten):
    if ten not in _TOPO:
        t = json.load(open(os.path.join(TAI, "us", ten), encoding="utf-8"))
        sx, sy = t["transform"]["scale"]; tx, ty = t["transform"]["translate"]
        arcs = []
        for a in t["arcs"]:
            x = y = 0; pts = []
            for dx, dy in a:
                x += dx; y += dy; pts.append((x * sx + tx, y * sy + ty))
            arcs.append(pts)
        _TOPO[ten] = (t, arcs)
    return _TOPO[ten]


def _vong(arcs, ids):
    pts = []
    for i in ids:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(a if not pts else a[1:])
    return pts


def doi_tuong(ten, obj):
    """→ [(id, tên, [vòng…])] — mỗi vòng là list (lon, lat)."""
    t, arcs = topo(ten)
    out = []
    for g in t["objects"][obj]["geometries"]:
        polys = [g["arcs"]] if g["type"] == "Polygon" else g.get("arcs", [])
        rings = [_vong(arcs, r) for p in polys for r in p]
        out.append((g.get("id"), (g.get("properties") or {}).get("name", ""), rings))
    return out


def ve_ranh_gioi(kh, nhan_bang=True):
    """Lớp RGBA: ranh giới hạt (khi nhìn gần), bang, tên bang mờ, tên hạt (khi rất gần). Vẽ 2× rồi thu nhỏ cho mượt."""
    s = 2
    im = Image.new("RGBA", (kh.rw * s, kh.rh * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rong = kh.rong_do()
    bang = doi_tuong("states-10m.json", "states")
    if rong < 16:
        hat = doi_tuong("counties-10m.json", "counties")
        for _, _, rings in hat:
            for r in rings:
                d.line([kh.px(lo, la, s) for lo, la in r], fill=(255, 255, 255, 105), width=max(2, round(1.4 * s)))
    for _, _, rings in bang:
        for r in rings:
            p = [kh.px(lo, la, s) for lo, la in r]
            d.line(p, fill=(0, 0, 0, 90), width=round(5.5 * s))
            d.line(p, fill=(255, 255, 255, 235), width=round(3.0 * s))
    im = im.resize((kh.rw, kh.rh), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    if nhan_bang:
        co = 46 if rong > 30 else 64 if rong > 12 else 84
        f = F_DAM(co); da_ghi = []
        for _, ten, rings in sorted(bang, key=lambda b: -max((len(r) for r in b[2]), default=0)):
            if not ten or not rings: continue
            r = max(rings, key=len)
            lo = sum(p[0] for p in r) / len(r); la = sum(p[1] for p in r) / len(r)
            x, y = kh.px(lo, la)
            ps = [kh.px(a, b) for a, b in r]
            bw = max(p[0] for p in ps) - min(p[0] for p in ps); bh = max(p[1] for p in ps) - min(p[1] for p in ps)
            tw = f.getlength(ten.upper())
            if tw > bw * .85 or co > bh * .8: continue      # bang nhỏ: bỏ tên cho khỏi chồng
            hop = (x - tw / 2 - 8, y - co / 2, x + tw / 2 + 8, y + co / 2)
            if any(hop[0] < b[2] and b[0] < hop[2] and hop[1] < b[3] and b[1] < hop[3] for b in da_ghi): continue
            if 40 < x < kh.rw - 40 and 40 < y < kh.rh - 40:
                da_ghi.append(hop)
                d.text((x, y), ten.upper(), font=f, fill=(255, 255, 255, 70), anchor="mm")
    if rong < 6:
        hat = doi_tuong("counties-10m.json", "counties")
        f = F_DAM7(26)
        dung = []
        for _, ten, rings in hat:
            if not ten or not rings: continue
            r = max(rings, key=len)
            lo = sum(p[0] for p in r) / len(r); la = sum(p[1] for p in r) / len(r)
            x, y = kh.px(lo, la)
            if not (60 < x < kh.rw - 60 and 60 < y < kh.rh - 60): continue
            if any(abs(x - a) < 90 and abs(y - b) < 30 for a, b in dung): continue
            dung.append((x, y))
            d.text((x, y), ten.upper(), font=f, fill=(255, 255, 255, 150), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, 140))
    return im


# ---------------- Lớp dữ liệu ----------------
def chon_bien_the(o, chon):
    """chon: số thứ tự, hoặc một đoạn nhãn (vi/en), hoặc None (mặc định 0)."""
    if chon is None or chon == "": return 0
    if (isinstance(chon, int) or str(chon).isdigit()) and 0 <= int(chon) < len(o["v"]):
        return int(chon)
    c = str(chon).lower()
    for i, v in enumerate(o["v"]):
        if c in v["vi"].lower() or c in v["en"].lower(): return i
    raise SystemExit(f"lớp {o['id']} không có biến thể '{chon}'. Có: " + "; ".join(f"{i}={v['vi']}" for i, v in enumerate(o["v"])))


def anh_lop(kh, o, vi, luc=None, tram=None):
    """Ảnh RGBA đúng khung cho lớp o, biến thể vi. luc: datetime UTC cho lớp có thời gian (radar, vệ tinh)."""
    val = o["v"][vi]["val"]
    q = lambda d: urllib.parse.urlencode(d, safe=":,{}")
    if o["kieu"] == "wms":
        p = {"service": "WMS", "version": "1.3.0", "request": "GetMap", "styles": "", "format": "image/png", "transparent": "true",
             "crs": "EPSG:3857", "bbox": kh.bbox3857, "width": kh.rw, "height": kh.rh, "layers": val}
        if luc: p["time"] = luc.strftime("%Y-%m-%dT%H:%M:00Z")
        base = o["url"].split("?")[0]
        im = tai_anh(base + "?" + q(p), cho=90)
        if o.get("toan_cau"):
            # ảnh GOES chỉ phủ ~ tới 52°N: lót ảnh ghép toàn cầu (thô hơn) bên dưới cho kín khung
            try:
                g = tai_anh(base + "?" + q({**p, "layers": o["toan_cau"]}), cho=90, lan=2)
                g.alpha_composite(im); im = g
            except Exception:
                pass
        return im
    if o["kieu"] == "iem_wmst":
        p = {"service": "WMS", "version": "1.1.1", "request": "GetMap", "styles": "", "format": "image/png", "transparent": "true",
             "srs": "EPSG:3857", "bbox": kh.bbox3857, "width": kh.rw, "height": kh.rh, "layers": val,
             "time": (luc or datetime.now(timezone.utc) - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:00Z")}
        return tai_anh("https://mesonet.agron.iastate.edu/cgi-bin/wms/nexrad/n0q-t.cgi?" + q(p), cho=90)
    if o["kieu"] == "ags":
        ids = ",".join(str(int(x) + 3) for x in val.split(",")) if o.get("raster") else val
        p = {"bbox": kh.bbox3857, "bboxSR": 3857, "imageSR": 3857, "size": f"{kh.rw},{kh.rh}", "dpi": 96, "format": "png32",
             "transparent": "true", "layers": "show:" + ids, "f": "image"}
        return tai_anh(o["svc"] + "/export?" + q(p), cho=120)
    if o["kieu"] == "agi":
        svc = val if val.startswith("http") else o["svc"]
        p = {"bbox": kh.bbox3857, "bboxSR": 3857, "imageSR": 3857, "size": f"{kh.rw},{kh.rh}", "format": "png", "transparent": "true", "f": "image"}
        return tai_anh(svc + "/exportImage?" + q(p), cho=120)
    if o["kieu"] == "xyz":
        tpl = o["tpl"].replace("{v}", val).replace("{site}", tram or "TLX")
        return ghep_o(kh, lambda z, x, y: tpl.replace("{z}", str(z)).replace("{x}", str(x)).replace("{y}", str(y)), 12)
    raise SystemExit("kiểu lớp lạ: " + o["kieu"])


def do_phu(im):
    """% điểm ảnh có dữ liệu (để báo lớp trống — đừng đưa bản đồ trống vào video)."""
    a = im.getchannel("A").resize((192, 108))
    return round(100 * sum(1 for v in a.tobytes() if v > 20) / (192 * 108), 1)


_TRAM = None


def tram_gan(lon, lat):
    global _TRAM
    if _TRAM is None:
        j = json.loads(tai("https://mesonet.agron.iastate.edu/geojson/network/NEXRAD.geojson"))
        _TRAM = [(f["id"], f["properties"].get("sname", ""), *f["geometry"]["coordinates"]) for f in j["features"] if len(f["id"]) == 3]
    return min(_TRAM, key=lambda t: ((t[2] - lon) * math.cos(math.radians(lat))) ** 2 + (t[3] - lat) ** 2)


# ---------------- Chú giải ----------------
_LEG = {}


def _ags_leg(svc):
    if svc not in _LEG:
        lg = json.loads(tai(svc + "/legend?f=json").decode("utf-8", "replace"), strict=False)
        info = json.loads(tai(svc + "?f=json").decode("utf-8", "replace"), strict=False) if svc.endswith("MapServer") else {"layers": []}
        _LEG[svc] = (lg.get("layers", []), {l["id"]: l.get("subLayerIds") or [] for l in info.get("layers", [])})
    return _LEG[svc]


DBZ = [(4, 233, 231), (1, 159, 244), (3, 0, 244), (2, 253, 2), (1, 197, 1), (0, 142, 0), (253, 248, 2), (229, 188, 0),
       (253, 149, 0), (253, 0, 0), (212, 0, 0), (188, 0, 0), (248, 0, 253), (152, 84, 198)]


def _so(t):
    """'-80.139999' → '-80'; giữ nguyên nhãn chữ."""
    t = t.strip()
    try:
        v = float(t); return str(round(v)) if abs(v) >= 10 else f"{v:g}"
    except ValueError:
        return t


def _co_trong_khung(svc, layer_ids, kh):
    """Nhãn chú giải của các đối tượng thật sự nằm trong khung (renderer unique value)."""
    nhan = set()
    for lid in layer_ids:
        info = json.loads(tai(f"{svc}/{lid}?f=json").decode("utf-8", "replace"), strict=False)
        r = (info.get("drawingInfo") or {}).get("renderer") or {}
        if r.get("type") != "uniqueValue" or not r.get("field1"): return None
        q = urllib.parse.urlencode({"geometry": kh.bbox3857, "geometryType": "esriGeometryEnvelope", "inSR": 3857,
                                    "spatialRel": "esriSpatialRelIntersects", "outFields": r["field1"], "returnDistinctValues": "true",
                                    "returnGeometry": "false", "f": "json"})
        j = json.loads(tai(f"{svc}/{lid}/query?{q}").decode("utf-8", "replace"), strict=False)
        gt = {str(f["attributes"].get(r["field1"])) for f in j.get("features", [])}
        nhan |= {u.get("label") for u in r.get("uniqueValueInfos", []) if str(u.get("value")) in gt}
    return nhan


def chu_giai(o, vi, kh=None):
    """→ ('thang', [(rgb)…], (trái, phải)) | ('muc', [(ảnh, nhãn)…]) | ('anh', ảnh) | None"""
    import base64
    if o.get("khong_chu_giai"): return None
    if o.get("thang") == "dbz": return ("thang", DBZ, ("LIGHT", "HEAVY / HAIL"))
    if o.get("thang") == "van_toc":
        return ("thang", [(0, 224, 255), (0, 150, 60), (10, 110, 10), (127, 127, 127), (122, 10, 10), (200, 20, 20), (255, 42, 42)], ("TOWARD RADAR", "AWAY"))
    val = o["v"][vi]["val"]
    if o["kieu"] == "wms":
        try:
            return ("anh", tai_anh(o["url"].split("?")[0] + "?service=WMS&version=1.3.0&request=GetLegendGraphic&format=image/png&layer=" + urllib.parse.quote(val), lan=2))
        except Exception:
            return None
    if o["kieu"] in ("ags", "agi"):
        svc = val if o["kieu"] == "agi" and val.startswith("http") else o["svc"]
        try:
            layers, kids = _ags_leg(svc)
        except Exception:
            return None
        if o["kieu"] == "agi":
            items = [x for l in layers for x in l.get("legend", [])]
            raster = True
        else:
            ids = [int(x) + 3 for x in val.split(",")] if o.get("raster") else [int(x) for x in val.split(",")]
            want = set()
            def walk(i):
                want.add(i); [walk(k) for k in kids.get(i, [])]
            [walk(i) for i in ids]
            ls = [l for l in layers if l["layerId"] in want]
            items, seen = [], set()
            for l in ls:
                for x in l.get("legend", []):
                    if x.get("label") and x["label"] not in seen:
                        seen.add(x["label"]); items.append(x)
            raster = any("raster" in (l.get("layerType") or "").lower() or "image" in (l.get("layerType") or "").lower() for l in ls)
        items = [x for x in items if x.get("imageData") and (x.get("label") or "").strip()]
        if o["kieu"] == "ags" and not raster and len(items) > 8 and kh is not None:
            try:
                co = _co_trong_khung(svc, [l["layerId"] for l in ls if not kids.get(l["layerId"])], kh)
                if co is not None: items = [x for x in items if x["label"] in co]
            except Exception:
                pass
        for x in items: x["label"] = x["label"].replace(" Valid", "").replace(" VALID", "")
        if not items: return None
        ims = [(Image.open(io.BytesIO(base64.b64decode(x["imageData"]))).convert("RGBA"), x["label"]) for x in items]
        if raster and len(ims) > 14:
            mau = [im.resize((1, 1), Image.BOX).getpixel((0, 0))[:3] for im, _ in ims]
            return ("thang", mau, (_so(ims[0][1].split(" - ")[0]), _so(ims[-1][1].split(" - ")[-1])))
        return ("muc", ims[:16])
    return None


def ve_chu_giai(cg, tieu):
    """Ô chú giải nền tối bo góc, chữ hẹp in hoa → ảnh RGBA."""
    if not cg: return None
    pad, fw = 16, F_DAM7(26)
    fi = F_VUA(24)
    if cg[0] == "thang":
        _, mau, (a, b) = cg
        w = 420; h = pad + 34 + 26 + 8 + 28 + pad
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, h - 1), 9, fill=(10, 14, 22, 205), outline=(255, 255, 255, 40))
        d.text((pad, pad), tieu.upper(), font=fw, fill="white")
        x0, y0, bw = pad, pad + 40, w - 2 * pad
        for k, c in enumerate(mau):
            d.rectangle((x0 + bw * k / len(mau), y0, x0 + bw * (k + 1) / len(mau), y0 + 22), fill=tuple(c) + (255,))
        d.text((x0, y0 + 28), str(a).upper(), font=fi, fill=(220, 226, 236))
        d.text((x0 + bw, y0 + 28), str(b).upper(), font=fi, fill=(220, 226, 236), anchor="ra")
        return im
    if cg[0] == "anh":
        a = cg[1]
        if a.width < 8 or a.height < 8: return None
        sc = min(1.0, 380 / a.width, 420 / a.height)
        a = a.resize((max(1, round(a.width * sc)), max(1, round(a.height * sc))))
        w, h = max(a.width, 300) + 2 * pad, a.height + 46 + 2 * pad
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, h - 1), 9, fill=(10, 14, 22, 205), outline=(255, 255, 255, 40))
        d.text((pad, pad), tieu.upper(), font=fw, fill="white")
        bg = Image.new("RGBA", a.size, (245, 247, 250, 255)); bg.alpha_composite(a)
        im.paste(bg, (pad, pad + 40))
        return im
    items = cg[1]
    cot = 2 if len(items) > 7 else 1
    hang = math.ceil(len(items) / cot)
    cw = 250 if cot == 2 else 330
    w, h = pad * 2 + cw * cot, pad + 40 + hang * 32 + pad - 4
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 9, fill=(10, 14, 22, 205), outline=(255, 255, 255, 40))
    d.text((pad, pad), tieu.upper(), font=fw, fill="white")
    for k, (sw, lab) in enumerate(items):
        x, y = pad + (k // hang) * cw, pad + 40 + (k % hang) * 32
        im.alpha_composite(sw.resize((22, 22)), (x, y + 2))
        t = lab.upper()
        while fi.getlength(t) > cw - 40 and len(t) > 4: t = t[:-2]
        d.text((x + 32, y + 1), t, font=fi, fill=(235, 238, 245))
    return im


# ---------------- Giờ địa phương Mỹ (không cần tzdata) ----------------
TZ = {"ET": (-5, "EST", "EDT"), "CT": (-6, "CST", "CDT"), "MT": (-7, "MST", "MDT"), "AZ": (-7, "MST", "MST"), "PT": (-8, "PST", "PDT"),
      "AKT": (-9, "AKST", "AKDT"), "HT": (-10, "HST", "HST")}


def _dst(utc, off):
    y = utc.year
    def chu_nhat(m, n):
        d = datetime(y, m, 1)
        return d + timedelta(days=(6 - d.weekday()) % 7 + 7 * (n - 1))
    bd = chu_nhat(3, 2) + timedelta(hours=2 - off); kt = chu_nhat(11, 1) + timedelta(hours=1 - off)
    return bd <= utc.replace(tzinfo=None) < kt


def gio_dia_phuong(utc, tz="CT"):
    off, a, b = TZ.get(tz, TZ["CT"])
    he = a != b and _dst(utc, off)
    t = utc + timedelta(hours=off + (1 if he else 0))
    return t.strftime("%-I:%M %p" if os.name != "nt" else "%#I:%M %p") + " " + (b if he else a), t
