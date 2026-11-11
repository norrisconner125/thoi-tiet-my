---
name: lop-ban-do-noaa
description: 'Xuất CLIP MP4 + ẢNH PNG 1920×1080 bản đồ thời tiết Mỹ từ 50 lớp dữ liệu NOAA chính thức để dựng video trên CapCut: vệ tinh GOES (có chạy hình), radar NEXRAD (chạy giờ quá khứ), radar vận tốc từng trạm, radar dự báo HRRR 1–18 giờ, SPC nguy cơ giông lốc/lốc xoáy ngày 1–8, báo cáo thiệt hại LSR, ERO mưa gây lũ quét, lượng mưa đã rơi / dự báo QPF, bản đồ front H/L của WPC, nhiệt độ NDFD, WSSI bão tuyết, xác suất tuyết/băng, bão nhiệt đới (gió, nước dâng), CPC 6–14 ngày, hạn hán, khói cháy rừng, chất lượng không khí, hàng không. Kiểu hình giống ban-tin-ve-tinh (nền vệ tinh, ranh giới bang/hạt, chip lớp, tiêu đề, chú giải). Dùng skill này mỗi khi người dùng cần bản đồ / đồ hoạ thời tiết cho video, cảnh bản đồ cho CapCut, "bản đồ SPC", "bản đồ mưa", "future radar", "radar loop", "bản đồ tuyết", "bản đồ front", "lớp NOAA", "xuất clip bản đồ", hoặc khi đang dựng bản tin bằng ban-tin-ve-tinh mà cần lớp nó không có (SPC, WPC, CPC, LSR, HRRR, tuyết, khói…). Không dùng cho bản đồ Windy / Zoom Earth.'
---

# Lớp bản đồ NOAA → clip cho CapCut

Đầu ra: mỗi cảnh một `<id>.mp4` (1920×1080, 30 fps, H.264), `<id>.png` (khung cuối có chữ), `<id>_sach.png` (không chữ, để tự gõ chữ trong CapCut) và `bao_cao.json`. Không ghi dự án CapCut: clip được kéo vào CapCut, hoặc chèn qua skill `ban-tin-ve-tinh`.

- Trả lời tiếng Việt, câu ngắn. Chữ **trên** video mặc định tiếng Anh (khán giả Mỹ), trừ khi người dùng muốn khác.
- Chạy liền các bước. Chỉ dừng khi thiếu thông tin thật sự (không rõ vùng, không rõ nói về ngày nào).
- Không sửa file gốc của người dùng. Clip ghi vào thư mục ra (mặc định `<case>/lop_noaa/`).

`S` = thư mục `scripts/` cạnh file này. Trên Windows/PowerShell, nạp PATH trước:
`$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`
Chạy Python với `-X utf8`. Đừng nhét code nhiều dòng vào `python -c` (dễ vỡ dấu nháy): viết ra file rồi chạy.

**Cần có:** Python 3.10+ với Pillow (`pip install pillow`), ffmpeg trên PATH, Internet. Không cần trình duyệt, không cần API key. Font Barlow Condensed / Inter và ranh giới bang/hạt đã nằm sẵn trong `assets/`.

## Dữ liệu này là "bây giờ" — hiểu trước khi chọn lớp

Đa số lớp chỉ có **bản phát hành mới nhất** (SPC, WPC, CPC, NDFD, QPF, LSR, khói…). Không lấy lại được bản của hôm qua. Vì vậy:

| Loại thời gian | Lớp | Dùng thế nào |
|---|---|---|
| Lưu trữ | `radar` (khảm NEXRAD) | Mọi giờ trong quá khứ: `"vong": {"tu": "…Z", "den": "…Z", "buoc": 10}` hoặc ảnh tĩnh `"luc": "…Z"` |
| Gần đây | `sat_vis`, `sat_ir`, `sat_wv`, `sat_sw`, `sat_snow` | Khoảng 8 giờ gần nhất: `"vong": {"gio": 3, "buoc": 10}` |
| Giờ dự báo | `hrrr` | `"hrrr:*"` chạy +1…+18 giờ từ lượt chạy mới nhất; chip ghi giờ địa phương hiệu lực, `bao_cao.json` ghi `hrrr_chay_utc` |
| Hiện tại | tất cả lớp còn lại | Ảnh của bản mới nhất, có zoom chậm và hiện dần |

- Kịch bản nói về sự kiện **đã qua** (vd lũ tuần trước): chỉ dùng `radar` lưu trữ. Các lớp "hiện tại" sẽ cho bản đồ **sai ngày**, đừng dùng. Nói rõ điều này với người dùng.
- Kịch bản cho **hôm nay / sắp tới**: dùng thoải mái. Ghi `tai_luc_utc` trong báo cáo, vì sản phẩm NOAA được cập nhật trong ngày (SPC ra Day 1 lúc 06Z, 13Z, 1630Z, 20Z, 01Z).

## Chọn lớp theo câu chuyện

| Chủ đề | Lớp nên dùng (dưới → trên) |
|---|---|
| Giông lốc, lốc xoáy | `spc:0` (5 cấp) hoặc `spc:1` (xác suất lốc) · `lsr:0` · `radar` có `vong` · `rad_site` (vận tốc) khi zoom vào một ô bão |
| Mưa lớn, lũ quét | `ero:0` · `qpf:Tổng 3` · `qpe:24` (mưa đã rơi) · `ffg:0` · `nwm` (sông dâng) |
| Bão tuyết, băng giá | `rad_ptype` · `wssi:0` · `wpc_snow:0` · `chart:3` (front + H/L) · `ndfd_apt` (wind chill) |
| Bão nhiệt đới | `sat_ir` có `vong` · `tc_wind` · `tc_ww` · `surge` · `qpf:Tổng 5` · `sst` |
| Nắng nóng | `ndfd_max:0` · `ndfd_apt` (heat index) · `cpch:0` |
| Cháy rừng, khói | `fire:0` · `smoke:0` · `aq:0` |
| Tổng quan toàn quốc | `sat_ir` · `chart:0` (front, H/L, vùng mưa) |
| Xu hướng 1–2 tuần | `cpc610:0` / `cpc610:1` · `cpc814` · `cpch` |

Chọn biến thể bằng `mã:X`:
- `X` là số nhỏ hơn số biến thể → theo thứ tự (`spc:1` = ngày 1, xác suất lốc).
- Ngược lại → khớp một đoạn của nhãn tiếng Việt hoặc tiếng Anh, không phân biệt hoa thường (`qpf:Tổng 3`, `qpf:3-Day`, `lsr:72`, `qpe:24`).
- Bỏ trống → biến thể 0. Riêng `hrrr:*` là chạy mọi giờ dự báo.

Một cảnh tốt có **1–2 lớp dữ liệu**. Thêm lớp làm rối và che nhau. Danh mục đủ 50 lớp, mã biến thể và ghi chú: `references/danh_muc_lop.md`. Tra nhanh: `python -X utf8 "S/xuat.py" --danh-sach <từ khoá>`.

## Quy trình

### 1. Chia cảnh
Đọc kịch bản (SRT, văn bản, hoặc lời người dùng). Mỗi cảnh = một chủ đề + một vùng + một lớp chính. Xác định:
- **Vùng**: mã bang (`"vung": "TX"`), `"US"` (lục địa), hoặc `"bbox": [lat0, lon0, lat1, lon1]` cho khu vực tuỳ ý (vd Gulf Coast `[27, -98, 33, -84]`). Khung tự giãn cho đủ 16:9. Rộng dưới ~16° kinh độ thì có ranh giới hạt; dưới ~6° có tên hạt.
- **Số giây**: khớp lời đọc của đoạn đó (`giay`, mặc định 8). Có voice thì lấy độ dài câu thật.
- **Tiêu đề**: 2 dòng ngắn, in hoa. Dòng 2 tô màu theo ý nghĩa: `cam` ấm/nhấn, `tim` lạnh/tuyết, `xanh` nước/mưa, `do` nguy hiểm/kỷ lục, `vang` cảnh giác. Không có số liệu thì đừng bịa; số trên tiêu đề lấy từ kịch bản.

### 2. Viết `canh.json`
Đặt ở `<case>/_tt/lop_noaa_canh.json` (hoặc thư mục người dùng chỉ định):
```json
{ "ra": "<case>/lop_noaa", "tz": "CT",
  "canh": [
    {"id": "N01", "vung": "US", "lop": ["sat_ir", "chart:0"], "tieu": ["NATIONAL FORECAST", "TODAY"], "nhan": "cam", "giay": 8},
    {"id": "N02", "vung": "OK", "lop": ["spc:0", "lsr:24"], "tieu": ["SEVERE STORM RISK", "TODAY"], "nhan": "do", "giay": 10},
    {"id": "N03", "bbox": [29, -100, 34, -93], "lop": ["radar"], "vong": {"tu": "2026-11-08T18:00Z", "den": "2026-11-09T00:00Z", "buoc": 15},
     "tieu": ["RADAR", "SATURDAY AFTERNOON"], "nhan": "xanh", "giay": 9},
    {"id": "N04", "vung": "US", "lop": ["hrrr:*"], "tieu": ["FUTURE RADAR", "NEXT 18 HOURS"], "nhan": "xanh", "giay": 9}
  ] }
```
Tuỳ chọn mỗi cảnh: `ten_bang` (false để tắt tên bang mờ, nên tắt khi khung chỉ 1–3 bang và tên bang nằm dưới tiêu đề hoặc chú giải), `zoom` (độ đẩy cuối, mặc định 1.06; 1.0 = đứng yên), `khung_giay` (giây mỗi khung khi chạy hình, mặc định 0.3), `tram` (trạm radar 3 chữ, vd `"TLX"`; bỏ trống thì lấy trạm gần tâm khung), `do_dam` (`{"spc": 0.7}`), `chu_giai` (false để tắt), `chip` (false để tắt chip), `nguon` (thay dòng nguồn tự sinh).
- `tz` là múi giờ hiện trên chip giờ: `ET`, `CT`, `MT`, `AZ`, `PT`, `AKT`, `HT` (tự đổi giờ mùa hè).
- Giờ trong `vong` / `luc` luôn là **UTC** (`Z`). CST = UTC−6, CDT = UTC−5, EST = UTC−5, EDT = UTC−4.

### 3. Xem thử
```
python -X utf8 "S/xuat.py" "<canh.json>" --thu
```
Chỉ ra PNG (nhanh, ~5 giây/cảnh). **Read từng PNG** và đọc dòng `⚠` in ra:
- `lớp … gần như TRỐNG`: hôm nay NOAA không phát hành sản phẩm đó cho vùng này (vd không có nguy cơ giông). Đừng đưa bản đồ trống vào video: đổi biến thể (ngày khác), đổi lớp, nới vùng, hoặc bỏ cảnh và báo người dùng. Bản đồ trống mà lời đọc nói "nguy cơ cao" sẽ làm khán giả mất tin.
- Nhìn chữ: tiêu đề có che vùng dữ liệu chính không, chú giải có đè lên chỗ quan trọng không. Che thì dời `bbox` cho vùng chính lệch lên/sang phải.
- Cảnh chạy hình: ảnh xem thử chỉ là **một** khung (radar/vệ tinh: khung cuối; HRRR: khung nhiều dữ liệu nhất trong +1, +9, +18 giờ), nên đừng bỏ cảnh chỉ vì khung đó ít mưa.
- Lần đầu người dùng thấy kiểu bản đồ: gửi một ảnh để họ duyệt. Không có ai trả lời (chạy tự động) thì cứ xuất tiếp và đính kèm PNG trong báo cáo.

### 4. Xuất clip
```
python -X utf8 "S/xuat.py" "<canh.json>"            # tất cả
python -X utf8 "S/xuat.py" "<canh.json>" N02 N04    # chỉ vài cảnh
```
Cảnh tĩnh mất ~10–20 giây; cảnh chạy hình 18 khung mất ~1 phút (tải từng khung). `bao_cao.json` cộng dồn qua các lần chạy.

### 5. Đưa vào CapCut
Xem `references/capcut.md`. Tóm tắt:
- **Dựng tay**: kéo `N01.mp4, N02.mp4…` vào timeline theo thứ tự. Muốn tự gõ chữ trong CapCut thì dùng `_sach.png` (đặt thời lượng = lời đọc) thay cho MP4.
- **Cùng `ban-tin-ve-tinh`**: để thư mục ra là `<case>/lop_noaa/`, chạy lại `kiem_ke.py` để clip được đánh số `V..`, rồi trong `lap_edl.py` chèn vào câu tương ứng (`chen={câu: [{"id": "Vxx"}]}`) và liệt kê các id đó trong `do_hoa=[...]` để không bị gắn thẻ địa danh.

## Báo cáo cuối
Ngắn gọn:
- Thư mục ra, số clip, tổng thời lượng.
- Bảng cảnh: id · vùng · lớp (biến thể) · số giây · % phủ dữ liệu · ghi chú.
- Lớp trống đã đổi/bỏ và lý do. Khung giờ radar/vệ tinh (giờ địa phương).
- Thời điểm tải dữ liệu (UTC) và nhắc: các lớp "hiện tại" là bản NOAA lúc đó; dựng video muộn thì nên xuất lại cho mới.
- Nguồn dữ liệu đều là cơ quan liên bang Mỹ (public domain); dòng nguồn đã có ở đáy mỗi clip, đừng cắt đi.
