#!/usr/bin/env python3
"""Kiểm tra file SRT kịch bản thời tiết trước khi đưa vào phần mềm TTS.

Kiểm tra:
  - Đánh số liên tục, định dạng thời gian đúng, không chồng lấn
  - Mỗi đoạn 20–25 từ, đúng MỘT câu hoàn chỉnh (kết thúc bằng . ! ?)
  - Ký tự/viết tắt dễ làm TTS đọc sai (°, %, /, &, #, mph, NWS, I-95, 6-12, …)
  - Tổng thời lượng trong khoảng mong muốn (mặc định 12–15 phút)

Dùng:
  python3 kiem_tra_srt.py script.srt
  python3 kiem_tra_srt.py script.srt --min 12 --max 15 --words 20-25
  python3 kiem_tra_srt.py script.srt --retime --wpm 150 -o script_fixed.srt   # tính lại thời gian theo số từ
Thoát với mã 1 nếu có LỖI (cảnh báo không làm thất bại).
"""
import argparse, re, sys

TS = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})$")
BAD_CHARS = {"°": "viết 'degrees'", "%": "viết 'percent'", "/": "viết bằng chữ ('per', 'or', 'and')", "&": "viết 'and'",
             "#": "bỏ", "*": "bỏ (không dùng ký hiệu nhấn mạnh)", "@": "bỏ", "~": "viết 'about'", "^": "bỏ", "_": "bỏ",
             "=": "bỏ", "+": "viết 'plus' hoặc 'or more'", "<": "viết 'less than'", ">": "viết 'more than'", "[": "bỏ ngoặc",
             "]": "bỏ ngoặc", "{": "bỏ", "}": "bỏ", "|": "bỏ", "\\": "bỏ", "…": "dùng dấu chấm hoặc phẩy", "–": "viết 'to' hoặc dùng dấu phẩy",
             "—": "dùng dấu phẩy", "(": "bỏ ngoặc, viết thành mệnh đề", ")": "bỏ ngoặc", "\"": "bỏ ngoặc kép", "“": "bỏ ngoặc kép",
             "”": "bỏ ngoặc kép", ";": "tách thành câu/ dùng dấu phẩy"}
BAD_PATTERNS = [
    (r"\b\d+\s*-\s*\d+\b", "khoảng số có gạch nối → '6 to 12'"),
    (r"\bI-\d+\b", "viết 'Interstate' + số, ví dụ 'Interstate 35'"),
    (r"\bmph\b", "viết 'miles per hour'"),
    (r"\b\d+(\.\d+)?\s*(in|ft|mi|kts?|mb)\b\.?", "viết đơn vị đầy đủ: inches, feet, miles, knots, millibars"),
    (r"\b\d+\s*F\b|\b\d+F\b", "viết 'degrees'"),
    (r"\b(NWS|SPC|WPC|NHC|CPC|NOAA|AFD|ERO|EF\d|CAPE|HRRR|GFS|ECMWF|NAM|ICON)\b",
     "viết tắt: lần đầu viết đầy đủ (the National Weather Service, the Storm Prediction Center…); EF2 → 'EF two'"),
    (r"\b[A-Z]{2}\b(?<!\bAM)(?<!\bPM)(?<!\bUS)(?<!\bOK)(?<!\bTV)(?<!\bDC)", "mã viết hoa 2 chữ (mã bang?) → viết tên bang đầy đủ"),
    (r"\ba\.m\.|\bp\.m\.", "dấu chấm trong a.m./p.m. có thể làm TTS ngắt câu → 'AM'/'PM' hoặc 'this morning'"),
    (r"https?://|www\.", "không đọc đường link"),
    (r"[\U0001F300-\U0001FAFF☀-➿]", "bỏ emoji"),
]
ABBR = re.compile(r"\b(Mr|Mrs|Dr|St|Mt|Ft|Jr|Sr|vs|etc|U\.S)\.$")


def to_ms(h, m, s, ms):
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)


def fmt(ms):
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse(text):
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip())
    cues = []
    for b in blocks:
        lines = [l for l in b.split("\n") if l.strip() != ""]
        cues.append(lines)
    return cues


def words(t):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.,-]*", t))


def sentence_count(t):
    t2 = re.sub(r"\b\d+\.\d+\b", "0", t)
    parts = [p for p in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", t2.strip()) if p]
    return len([p for p in parts if not ABBR.search(p)]) or 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("srt")
    ap.add_argument("--min", type=float, default=12.0, help="phút tối thiểu")
    ap.add_argument("--max", type=float, default=15.0, help="phút tối đa")
    ap.add_argument("--words", default="20-25", help="khoảng số từ mỗi đoạn")
    ap.add_argument("--retime", action="store_true", help="tính lại thời gian theo số từ")
    ap.add_argument("--wpm", type=float, default=150.0, help="tốc độ đọc khi --retime (từ/phút)")
    ap.add_argument("--gap", type=int, default=200, help="khoảng nghỉ giữa các đoạn khi --retime (ms)")
    ap.add_argument("-o", "--out", help="file ghi kết quả --retime")
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.words.split("-"))

    cues = parse(open(a.srt, encoding="utf-8-sig").read())
    errors, warns, items = [], [], []
    prev_end = -1
    for i, lines in enumerate(cues, 1):
        tag = f"Đoạn {i}"
        if len(lines) < 3:
            errors.append(f"{tag}: thiếu số thứ tự/thời gian/nội dung")
            continue
        if lines[0].strip() != str(i):
            errors.append(f"{tag}: số thứ tự là '{lines[0].strip()}', phải là {i}")
        m = TS.match(lines[1].strip())
        text = " ".join(l.strip() for l in lines[2:])
        items.append(text)
        if not m:
            errors.append(f"{tag}: sai định dạng thời gian '{lines[1].strip()}'")
        else:
            st, en = to_ms(*m.groups()[:4]), to_ms(*m.groups()[4:])
            if en <= st:
                errors.append(f"{tag}: thời gian kết thúc ≤ bắt đầu")
            if st < prev_end:
                errors.append(f"{tag}: chồng lấn với đoạn trước")
            prev_end = en
            secs = (en - st) / 1000
            wps = words(text) / secs if secs > 0 else 0
            if wps > 3.3:
                warns.append(f"{tag}: đọc quá nhanh ({wps:.1f} từ/giây) — kéo dài thời gian hoặc dùng --retime")
        n = words(text)
        if not lo <= n <= hi:
            errors.append(f"{tag}: {n} từ (yêu cầu {lo}–{hi}): {text[:90]}")
        if not re.search(r"[.!?]$", text):
            errors.append(f"{tag}: không kết thúc bằng . ! ? (chưa phải câu hoàn chỉnh)")
        if sentence_count(text) > 1:
            errors.append(f"{tag}: có nhiều hơn một câu: {text[:90]}")
        for ch, fix in BAD_CHARS.items():
            if ch in text:
                errors.append(f"{tag}: ký tự '{ch}' dễ làm TTS đọc sai → {fix}")
        for pat, fix in BAD_PATTERNS:
            mm = re.search(pat, text)
            if mm:
                warns.append(f"{tag}: '{mm.group(0)}' → {fix}")

    total = prev_end / 60000 if prev_end > 0 else 0
    if a.retime:
        out, t = [], 0
        for i, text in enumerate(items, 1):
            dur = int(words(text) / a.wpm * 60000) + 300
            out.append(f"{i}\n{fmt(t)} --> {fmt(t + dur)}\n{text}\n")
            t += dur + a.gap
        total = t / 60000
        path = a.out or a.srt.replace(".srt", "_retimed.srt")
        open(path, "w", encoding="utf-8").write("\n".join(out))
        print(f"Đã tính lại thời gian ({a.wpm:g} từ/phút) → {path}")
    if not a.min <= total <= a.max:
        errors.append(f"Tổng thời lượng {total:.1f} phút, yêu cầu {a.min:g}–{a.max:g} phút (thêm/bớt khoảng {abs((a.min + a.max) / 2 - total) * a.wpm / 22.5:.0f} đoạn)")

    tw = sum(words(x) for x in items)
    print(f"{len(items)} đoạn, {tw} từ, ~{total:.1f} phút.")
    for e in errors:
        print("LỖI   ", e)
    for w_ in warns:
        print("CẢNH BÁO", w_)
    print("KẾT QUẢ:", "ĐẠT" if not errors else f"CHƯA ĐẠT ({len(errors)} lỗi, {len(warns)} cảnh báo)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
