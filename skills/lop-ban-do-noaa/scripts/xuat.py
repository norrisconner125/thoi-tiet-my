"""Xuất clip MP4 + ảnh PNG 1920×1080 cho từng cảnh bản đồ, để kéo vào CapCut hoặc chèn bằng ban-tin-ve-tinh.

  python -X utf8 xuat.py --danh-sach [nhóm|từ khoá]       # xem lớp, mã biến thể
  python -X utf8 xuat.py canh.json --thu [L01 L02]        # chỉ ảnh PNG để duyệt nhanh
  python -X utf8 xuat.py canh.json [L01 …]                # MP4 + PNG + bao_cao.json

canh.json:
{ "ra": "<thư mục ra>", "tz": "CT",
  "canh": [ { "id": "L01", "vung": "OK" | "bbox": [lat0, lon0, lat1, lon1],
              "lop": ["spc:0", "lsr:72 giờ"],                 # dưới → trên; ":" + số thứ tự hoặc đoạn nhãn biến thể
              "tieu": ["SEVERE STORM RISK", "TODAY"], "nhan": "do",   # dòng 2 tô màu: cam|tim|xanh|do|vang
              "giay": 8, "zoom": 1.06,
              "vong": {"tu": "2026-11-10T18:00Z", "den": "2026-11-10T23:00Z", "buoc": 10}  # radar lưu trữ
                    | {"gio": 3, "buoc": 10},                  # radar / vệ tinh: N giờ gần nhất
              "tram": "TLX", "nguon": "…", "chu_giai": true, "chip": true } ] }
HRRR ("hrrr:*") tự chạy +1…+18 giờ.
"""
import argparse, json, os, subprocess, sys, time
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ban_do as B  # noqa: E402

W, H, FPS = B.W, B.H, 30
NEN_GOC = "Imagery: USGS The National Map, NASA · Boundaries: U.S. Census"


# ---------------- Chữ có bóng ----------------
def chu(lop, xy, t, f, fill, anchor="la", bong=8):
    sh = Image.new("RGBA", lop.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text(xy, t, font=f, fill=(0, 0, 0, 215), anchor=anchor)
    lop.alpha_composite(sh.filter(ImageFilter.GaussianBlur(bong)))
    ImageDraw.Draw(lop).text(xy, t, font=f, fill=fill, anchor=anchor)


def chip(t, phu="", mau=(61, 139, 253)):
    f, fe = B.F_DAM7(25), B.F_VUA(25)
    w = 14 + 12 + 9 + round(f.getlength(t)) + (round(fe.getlength("  " + phu)) if phu else 0) + 14
    im = Image.new("RGBA", (w, 42), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 41), 8, fill=(10, 14, 22, 200), outline=(255, 255, 255, 42))
    d.ellipse((14, 15, 26, 27), fill=mau + (255,))
    d.text((35, 22), t, font=f, fill="white", anchor="lm")
    if phu: d.text((35 + f.getlength(t), 22), "  " + phu, font=fe, fill=(170, 178, 192), anchor="lm")
    return im


MAU_CHIP = {"sat": (180, 190, 205), "radar": (2, 253, 2), "obs": (127, 208, 255), "fcst": (255, 176, 74), "severe": (255, 75, 75),
            "winter": (201, 184, 255), "tropic": (255, 120, 200), "long": (255, 216, 74), "env": (120, 220, 170), "avn": (170, 178, 192)}


def lop_chu(c, ds_lop, chu_giai_ds, nguon, gio_chip=None):
    """Lớp chữ cố định (không zoom theo bản đồ): chip, tiêu đề, chú giải, dòng nguồn."""
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if c.get("chip", True):
        x = 44
        for o, vi in ds_lop:
            ch = chip(o["chip"].upper(), o["v"][vi]["en"].upper(), MAU_CHIP.get(o["g"], (61, 139, 253)))
            if x + ch.width > W - 40: break
            ui.alpha_composite(ch, (x, 30)); x += ch.width + 10
        if gio_chip:
            ch = chip(gio_chip[0], gio_chip[1], (255, 213, 79)); ui.alpha_composite(ch, (min(x, W - 40 - ch.width), 30))
    tieu = c.get("tieu") or []
    if isinstance(tieu, str): tieu = [tieu]
    y = H - 74
    if len(tieu) > 1:
        chu(ui, (60, y), tieu[1].upper(), B.F_DAM(70), B.MAU.get(c.get("nhan", "cam"), B.MAU["cam"]), "ls"); y -= 74
    if tieu:
        chu(ui, (60, y), tieu[0].upper(), B.F_DAM(92), "white", "ls")
    yb = H - 62
    for cg in reversed(chu_giai_ds):
        if yb - cg.height < 100: break
        ui.alpha_composite(cg, (W - 40 - cg.width, yb - cg.height)); yb -= cg.height + 10
    chu(ui, (30, H - 22), nguon, B.F_NHO(15), (235, 238, 245, 165), "ls", bong=2)
    return ui


# ---------------- Ghép lớp ----------------
def mo(im, op):
    a = im.getchannel("A").point(lambda v: int(v * op))
    im = im.copy(); im.putalpha(a); return im


def thoi_diem(v, mac_dinh_buoc=10):
    buoc = int(v.get("buoc", mac_dinh_buoc))
    if "tu" in v:
        p = lambda s: datetime.strptime(s.replace("Z", ""), "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
        t0, t1 = p(v["tu"]), p(v["den"])
    else:
        t1 = datetime.now(timezone.utc) - timedelta(minutes=12)
        t0 = t1 - timedelta(hours=float(v.get("gio", 2)))
    t0 = t0.replace(minute=t0.minute - t0.minute % 5, second=0, microsecond=0)
    out, t = [], t0
    while t <= t1:
        out.append(t); t += timedelta(minutes=buoc)
    if len(out) > 60: raise SystemExit("vòng lặp quá 60 khung — tăng 'buoc' hoặc rút ngắn khoảng giờ")
    return out


def dung_canh(c, tz, chi_anh=False, log=print):
    kh = B.Khung(B.vung_bbox(c.get("bbox") or c.get("vung", "US")), k=1.0 if chi_anh else 1.08)
    ds = []
    for s in c["lop"]:
        lid, _, ch = str(s).partition(":")
        if lid not in B.BYID: raise SystemExit(f"[{c['id']}] không có lớp '{lid}' — xem: xuat.py --danh-sach")
        o = B.BYID[lid]
        ds.append((o, 0 if ch == "*" else B.chon_bien_the(o, ch or None), ch == "*"))
    # Lớp chạy hình: HRRR '*' (các giờ dự báo) hoặc radar/vệ tinh có 'vong'
    dong = None
    for k, (o, vi, sao) in enumerate(ds):
        if sao and o["thoi_gian"] == "bien_the": dong = (k, "bien_the")
        elif c.get("vong") and o["thoi_gian"] in ("luu_tru", "gan_day"): dong = (k, "gio")
        if dong: break
    tram = None
    if any(o.get("tram") for o, _, _ in ds):
        tram = c.get("tram") or B.tram_gan(*kh.tam)[0]
        log(f"  trạm radar: K{tram}")

    t0 = time.time()
    nen = B.nen_ve_tinh(kh)
    ranh = B.ve_ranh_gioi(kh, c.get("ten_bang", True))
    duoi, tren, phu, canh_bao = Image.new("RGBA", nen.size, (0, 0, 0, 0)), Image.new("RGBA", nen.size, (0, 0, 0, 0)), {}, []
    khung = []  # [(nhãn chip giờ, ảnh lớp động đã mờ)]
    hrrr_chay = [None]
    for k, (o, vi, _) in enumerate(ds):
        op = float(c.get("do_dam", {}).get(o["id"], o["op"])) if isinstance(c.get("do_dam"), dict) else o["op"]
        if dong and k == dong[0]:
            if dong[1] == "bien_the":
                init = B.hrrr_chay() if o["id"] == "hrrr" else None
                if init: hrrr_chay[0] = init
                # xem thử: lấy 3 khung (đầu, giữa, cuối) và giữ khung nhiều dữ liệu nhất, để % phủ không đánh lừa
                js = sorted({0, len(o["v"]) // 2, len(o["v"]) - 1}) if chi_anh else range(len(o["v"]))
                for j in js:
                    v = o["v"][j]
                    im = B.anh_lop(kh, o, j, tram=tram)
                    nhan = v["en"]
                    if init:
                        nhan = B.gio_dia_phuong(init + timedelta(minutes=int(v["val"])), tz)[0] + " · " + v["en"]
                    khung.append(((o["chip"].upper(), nhan), mo(im, op)))
                if chi_anh:
                    khung = [max(khung, key=lambda k: B.do_phu(k[1]))]
            else:
                ts = thoi_diem(c["vong"], 10 if o["id"] == "radar" else 5)
                for t in (ts[-1:] if chi_anh else ts):
                    im = B.anh_lop(kh, o, vi, luc=t)
                    khung.append(((o["chip"].upper(), B.gio_dia_phuong(t, tz)[0]), mo(im, op)))
            phu[o["id"]] = max(B.do_phu(im) for _, im in khung)
            continue
        luc = None
        if o["thoi_gian"] in ("luu_tru", "gan_day") and c.get("luc"):
            luc = datetime.strptime(c["luc"].replace("Z", ""), "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
        im = B.anh_lop(kh, o, vi, luc=luc, tram=tram)
        phu[o["id"]] = B.do_phu(im)
        (duoi if (o.get("duoi") or not dong or k < dong[0]) else tren).alpha_composite(mo(im, op))
    for lid, p in phu.items():
        if p < 0.3:
            canh_bao.append(f"lớp {lid} gần như TRỐNG trong khung này ({p}%) — hôm nay có thể không có sản phẩm này, hoặc khung nhìn lệch")
    # chú giải + nguồn
    cgs = []
    if c.get("chu_giai", True):
        for o, vi, _ in ds:
            try:
                im = B.ve_chu_giai(B.chu_giai(o, vi, kh), o["chip"] + (f" ({o['don_vi']})" if o.get("don_vi") else ""))
            except Exception as e:  # noqa: BLE001
                im = None; canh_bao.append(f"chú giải {o['id']}: {e}")
            if im: cgs.append(im)
        cgs = cgs[-2:]   # tối đa 2 ô, ưu tiên lớp trên cùng
    nguon = c.get("nguon") or ("Data: " + " · ".join(dict.fromkeys(o["src"] for o, _, _ in ds)) + " · " + NEN_GOC)
    if tram: nguon = nguon.replace("Iowa Environmental Mesonet", f"Iowa Environmental Mesonet (K{tram})", 1)
    ds_chip = [(o, vi) for o, vi, _ in ds if not (dong and o is ds[dong[0]][0])] if khung else [(o, vi) for o, vi, _ in ds]
    log(f"  tải xong {time.time() - t0:.0f}s · phủ dữ liệu: " + ", ".join(f"{k} {v}%" for k, v in phu.items()))
    return {"kh": kh, "nen": nen, "ranh": ranh, "duoi": duoi, "tren": tren, "khung": khung, "cgs": cgs, "nguon": nguon,
            "ds_chip": ds_chip, "phu": phu, "canh_bao": canh_bao, "tram": tram, "hrrr_chay": hrrr_chay[0]}


def anh_tinh(d, j=None):
    im = d["nen"].copy(); im.alpha_composite(d["duoi"])
    if j is not None: im.alpha_composite(d["khung"][j][1])
    im.alpha_composite(d["tren"]); im.alpha_composite(d["ranh"])
    return im.convert("RGB")


def xuat_canh(c, ra, tz, chi_anh=False, log=print):
    log(f"[{c['id']}] {', '.join(map(str, c['lop']))}")
    d = dung_canh(c, tz, chi_anh, log)
    ui_cache = {}
    def ui(j):
        g = d["khung"][j][0] if j is not None else None
        if g not in ui_cache: ui_cache[g] = B_ui(c, d, g)
        return ui_cache[g]
    cuoi = len(d["khung"]) - 1 if d["khung"] else None
    full = anh_tinh(d, cuoi)
    def khung_ra(rgb, z, uiim):
        rw, rh = rgb.size; bw, bh = rw / z, rh / z
        f = rgb.resize((W, H), Image.BILINEAR, box=((rw - bw) / 2, (rh - bh) / 2, (rw + bw) / 2, (rh + bh) / 2)).convert("RGBA")
        f.alpha_composite(uiim); return f.convert("RGB")
    zend = float(c.get("zoom", 1.06))
    png = os.path.join(ra, f"{c['id']}.png")
    khung_ra(full, 1.0 if chi_anh else zend, ui(cuoi)).save(png)
    khung_ra(full, 1.0 if chi_anh else zend, Image.new("RGBA", (W, H), (0, 0, 0, 0))).save(os.path.join(ra, f"{c['id']}_sach.png"))
    kq = {"id": c["id"], "png": png, "lop": c["lop"], "phu_du_lieu": d["phu"], "canh_bao": d["canh_bao"], "nguon": d["nguon"],
          "tai_luc_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ")}
    if d["tram"]: kq["tram"] = "K" + d["tram"]
    if d["hrrr_chay"]: kq["hrrr_chay_utc"] = d["hrrr_chay"].strftime("%Y-%m-%d %H:%MZ")
    if chi_anh and d["khung"]: kq["ghi_chu"] = "xem thử chỉ một khung (" + d["khung"][0][0][1] + "); % phủ là của khung nhiều dữ liệu nhất trong các khung đã tải"
    if d["khung"]: kq["khung_hinh"] = [g[1] for g, _ in d["khung"]]
    if chi_anh:
        return kq
    # ---- MP4: zoom đẩy chậm; lớp tĩnh hiện dần; lớp động chạy vòng, dừng lâu ở khung cuối ----
    giay = float(c.get("giay", 8)); n = round(giay * FPS)
    mp4 = os.path.join(ra, f"{c['id']}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    try:
        if d["khung"]:
            imgs = [anh_tinh(d, j) for j in range(len(d["khung"]))]
            mk = max(2, round(float(c.get("khung_giay", .3)) * FPS)); giu = round(1.2 * FPS)
            vong = [j for j in range(len(imgs)) for _ in range(mk)] + [len(imgs) - 1] * giu
            for i in range(n):
                j = vong[i % len(vong)]
                ff.stdin.write(khung_ra(imgs[j], 1 + (zend - 1) * i / max(1, n - 1), ui(j)).tobytes())
        else:
            truoc = d["nen"].copy(); truoc.alpha_composite(d["ranh"]); truoc = truoc.convert("RGB")
            for i in range(n):
                t = i / FPS; a = min(1.0, max(0.0, (t - .3) / .8))
                rgb = full if a >= 1 else Image.blend(truoc, full, a)
                ff.stdin.write(khung_ra(rgb, 1 + (zend - 1) * i / max(1, n - 1), ui(None)).tobytes())
    finally:
        ff.stdin.close(); ff.wait()
    if ff.returncode: raise SystemExit("ffmpeg lỗi khi ghi " + mp4)
    kq.update({"mp4": mp4, "giay": giay})
    return kq


def B_ui(c, d, gio):
    return lop_chu(c, d["ds_chip"], d["cgs"], d["nguon"], gio)


def danh_sach(tu=""):
    tu = (tu or "").lower()
    for g, ten in B.LOP["nhom"]:
        ls = [o for o in B.LOP["lop"] if o["g"] == g and (not tu or tu in (g + o["id"] + o["name"] + o["en"]).lower())]
        if not ls: continue
        print(f"\n== {ten} ({g})")
        for o in ls:
            tg = {"luu_tru": "chạy giờ quá khứ", "gan_day": "chạy ~8 giờ gần nhất", "bien_the": "chạy theo giờ dự báo ('*')"}.get(o["thoi_gian"], "hiện tại")
            print(f"  {o['id']:<11} {o['name']}  [{o['chip']}] · {tg}")
            if len(o["v"]) > 1:
                print("              " + " | ".join(f"{i}={v['vi']}" for i, v in enumerate(o["v"])))
    print("\nBộ dựng sẵn:")
    for p in B.LOP["bo_dung_san"]:
        print(f"  {p['ten']}: {', '.join(p['lop'])}" + (" + radar" if p.get("radar") else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("canh", nargs="?")
    ap.add_argument("chon", nargs="*")
    ap.add_argument("--thu", action="store_true", help="chỉ ảnh PNG, không MP4")
    ap.add_argument("--danh-sach", nargs="?", const="", default=None)
    a = ap.parse_args()
    if a.danh_sach is not None or not a.canh:
        return danh_sach(a.danh_sach)
    spec = json.load(open(a.canh, encoding="utf-8"))
    ra = spec.get("ra") or os.path.join(os.path.dirname(os.path.abspath(a.canh)), "lop_noaa")
    os.makedirs(ra, exist_ok=True)
    tz = spec.get("tz", "CT")
    ds = [c for c in spec["canh"] if not a.chon or c["id"] in a.chon]
    bc_p = os.path.join(ra, "bao_cao.json")
    bc = {x["id"]: x for x in (json.load(open(bc_p, encoding="utf-8")) if os.path.exists(bc_p) else [])}
    loi = []
    for c in ds:
        try:
            bc[c["id"]] = xuat_canh(c, ra, tz, a.thu)
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            loi.append(f"{c['id']}: {e}"); print("  LỖI:", e)
    json.dump(list(bc.values()), open(bc_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n→ {ra}")
    for c in ds:
        x = bc.get(c["id"])
        if not x: continue
        print(f"  {c['id']}: {os.path.basename(x.get('mp4') or x['png'])}" + "".join(f"\n     ⚠ {w}" for w in x["canh_bao"]))
    if loi:
        print("LỖI:", *loi, sep="\n  "); sys.exit(1)


if __name__ == "__main__":
    main()
