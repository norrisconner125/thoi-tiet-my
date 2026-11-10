---
name: ban-tin-thoi-tiet-my
description: Tìm và tổng hợp bản tin thời tiết nước Mỹ bằng tiếng Việt. Cảnh báo và dự báo lấy từ NOAA/NWS (SPC, WPC, NHC, CPC), tin tức đối chiếu với các nhà đài địa phương uy tín của từng bang. Khi không có cảnh báo thì dùng dự báo 7 ngày chính thức, radar và các mô hình (NBM, HRRR, NAM, GFS, ECMWF, ensemble) để báo sớm các sự kiện thời tiết. Dùng khi người dùng xin bản tin, cảnh báo, dự báo, tin bão, tin lốc xoáy, bão tuyết, lũ, nắng nóng... cho một bang, thành phố, khu vực hoặc toàn nước Mỹ, hoặc gọi /ban-tin-thoi-tiet-my.
---

# Bản tin thời tiết Mỹ

Mục tiêu: một bản tin tiếng Việt **chính xác, có nguồn, có giờ phát hành**, dùng được ngay cho người làm dự báo/biên tập.
Thứ tự ưu tiên nguồn: **NWS/NOAA (chính thức) → nhà đài địa phương uy tín (xác thực, bổ sung tình hình thực tế) → mô hình thời tiết (báo sớm, ghi rõ là "khả năng")**.

## 0. Xác định phạm vi

Đọc yêu cầu để biết:
- **Khu vực**: bang (mã 2 chữ, ví dụ `TX`), nhiều bang, thành phố, vùng (Đông Bắc, Bờ Vịnh, Đồng bằng lớn, Tây Bắc Thái Bình Dương...) hoặc toàn quốc (`US`). Vùng → đổi ra danh sách bang (xem `references/vung-va-bang.md`).
- **Khung thời gian**: hôm nay / 48 giờ / 7 ngày / 8–14 ngày. Mặc định: hiện tại + 7 ngày.
- Nếu người dùng không nói khu vực: làm bản tin **toàn quốc**, tập trung vào những nơi có cảnh báo nặng nhất.

Không hỏi lại nếu có thể đoán hợp lý; nói rõ giả định ở đầu bản tin.

## 1. Lấy dữ liệu chính thức (bắt buộc)

### Cách 1 — chạy script (nhanh nhất, nếu mạng cho phép)

```bash
python3 .claude/skills/ban-tin-thoi-tiet-my/scripts/tong_hop_nws.py --area TX,OK
python3 .claude/skills/ban-tin-thoi-tiet-my/scripts/tong_hop_nws.py --area US
python3 .claude/skills/ban-tin-thoi-tiet-my/scripts/tong_hop_nws.py --point 29.76,-95.37 --name Houston
python3 .claude/skills/ban-tin-thoi-tiet-my/scripts/tong_hop_nws.py --city "Denver, CO"
```

Script gọi trực tiếp api.weather.gov, SPC, WPC, NHC và in ra bản tóm tắt (đã đổi °C, km/h, giờ Việt Nam):
cảnh báo đang hiệu lực xếp theo mức nguy hiểm, nguy cơ dông bão SPC ngày 1–3 tại các thành phố chính, nguy cơ mưa lớn gây lũ WPC,
bão NHC, dự báo 7 ngày và đoạn đầu bản thảo luận dự báo (AFD). Thêm `--json` để lấy dữ liệu thô.
Nếu script báo lỗi một nguồn, nguồn đó vẫn phải được kiểm tra bằng Cách 2.

### Cách 2 — đọc trực tiếp nguồn (khi script lỗi/bị chặn mạng)

Dùng WebFetch/WebSearch với các địa chỉ trong `references/nguon-noaa-nws.md`. Tối thiểu phải xem:
1. **Cảnh báo NWS**: `https://api.weather.gov/alerts/active?area=XX` (hoặc `alerts.weather.gov`, `weather.gov`).
2. **SPC**: Convective Outlook ngày 1, 2, 3 (và 4–8), Watch đang hiệu lực, Mesoscale Discussion.
3. **WPC**: Excessive Rainfall Outlook ngày 1–5, Winter Weather (WSSI, xác suất tuyết), Hazards Outlook 3–7 ngày, Short Range Discussion.
4. **NHC** (mùa bão 1/6–30/11, hoặc khi có bão): Tropical Weather Outlook, bão đang hoạt động, nón dự báo.
5. **Văn phòng NWS địa phương (WFO)**: dự báo 7 ngày cho các thành phố chính + Area Forecast Discussion + Hazardous Weather Outlook (HWO).

## 2. Nhánh A — CÓ cảnh báo

1. Xếp cảnh báo theo mức: **Emergency (Tornado/Flash Flood/Extreme Wind Emergency) → Warning → Watch → Advisory → Statement**.
   Trong cùng mức, ưu tiên: lốc xoáy, lũ quét, bão/nước dâng, dông mạnh, bão tuyết/băng, gió mạnh, nắng nóng/lạnh cực, cháy rừng (Red Flag), sương mù, chất lượng không khí.
2. Với mỗi cảnh báo quan trọng ghi: tên tiếng Anh gốc + dịch (xem bảng thuật ngữ `references/thuat-ngu.md`), khu vực (quận/county, thành phố),
   **thời gian hiệu lực (giờ địa phương + giờ Việt Nam)**, nguy hiểm chính (gió giật, mưa đá, lượng mưa, tuyết, nhiệt độ — đổi đơn vị), văn phòng NWS phát hành.
3. **Xác thực bằng nhà đài địa phương** (`references/nha-dai-theo-bang.md`): tìm tin của 1–3 đài uy tín của bang đó về cùng sự kiện
   (thiệt hại, mất điện, đường đóng, sơ tán, số người bị ảnh hưởng). Chỉ đưa vào bản tin thông tin có **ít nhất một đài uy tín hoặc cơ quan chính thức**
   (NWS, cơ quan quản lý khẩn cấp bang, sở giao thông/511, công ty điện) xác nhận. Tin chỉ có trên mạng xã hội → ghi "chưa xác thực" hoặc bỏ.
4. Báo cáo thực tế: NWS Local Storm Reports (LSR), SPC Storm Reports hôm nay/hôm qua — dùng để nói "đã ghi nhận" lốc xoáy/mưa đá/gió.
5. Sau phần cảnh báo, vẫn thêm dự báo ngắn 2–3 ngày tới và sự kiện kế tiếp (nếu có).

## 3. Nhánh B — KHÔNG có cảnh báo

1. **Dự báo 7 ngày chính thức** của NWS (`api.weather.gov/points/...` → forecast) cho 2–4 thành phố chính của bang/khu vực
   (danh sách sẵn trong script; hoặc `references/vung-va-bang.md`).
2. Đọc **AFD** của WFO và **HWO** để biết nhà dự báo NWS đang theo dõi sự kiện gì (mặt trận lạnh, hệ thống áp thấp, sông khí quyển...).
3. **Báo sớm sự kiện** (3–14 ngày) bằng các sản phẩm và mô hình (chi tiết trong `references/radar-va-mo-hinh.md`):
   - Chính thức: SPC Day 4–8, WPC Hazards Outlook 3–7 ngày, WPC ERO ngày 4–5, CPC 6–10 / 8–14 ngày, NHC TWO 7 ngày.
   - Mô hình: ngắn hạn HRRR/NAM 3km/RRFS (0–48 giờ), trung hạn GFS, ECMWF (IFS/AIFS), ICON, CMC; ensemble GEFS/EPS để đánh giá độ tin cậy; NBM là hướng dẫn tổng hợp NWS dùng.
   - Radar/vệ tinh hiện tại (NEXRAD/MRMS, GOES) để mô tả mưa dông đang có.
4. Viết theo xác suất: "các mô hình đồng thuận / còn khác nhau", "khả năng thấp / trung bình / cao". **Không** khẳng định chắc chắn một sự kiện chỉ dựa trên một lượt chạy mô hình.

## 4. Quy tắc bắt buộc

- **Không bịa số liệu.** Mỗi con số (nhiệt độ, gió, mưa, xác suất, thời gian) phải lấy từ nguồn đã đọc trong phiên này. Không tìm thấy → ghi "chưa có dữ liệu".
- **Kiểm tra thời gian**: chỉ dùng sản phẩm còn hiệu lực/mới nhất; ghi giờ phát hành. Bỏ cảnh báo đã hết hạn (`expires`/`ends` đã qua).
- **Đơn vị**: ghi °F kèm °C (°C = (°F − 32) × 5/9), mph kèm km/h (× 1,609), inch kèm mm (× 25,4) / cm cho tuyết, dặm kèm km.
- **Giờ**: giờ địa phương của bang (ET/CT/MT/PT/AKT/HT, lưu ý giờ mùa hè DST: Chủ nhật thứ 2 tháng 3 → Chủ nhật đầu tháng 11) **và** giờ Việt Nam (UTC+7).
- Phân biệt rõ 3 loại thông tin: **[Chính thức NWS/NOAA]**, **[Nhà đài xác nhận]**, **[Mô hình — tham khảo]**.
- Giữ nguyên tên sản phẩm tiếng Anh lần đầu xuất hiện (ví dụ "Tornado Watch – Theo dõi lốc xoáy").
- Không dùng các trang tổng hợp/kiếm view không rõ nguồn làm nguồn chính. AccuWeather/The Weather Channel chỉ là tham khảo phụ.

## 5. Mẫu bản tin (tiếng Việt)

```
# BẢN TIN THỜI TIẾT MỸ – [Khu vực] – [ngày, giờ Việt Nam] ([giờ địa phương])

## Tóm tắt nhanh
- 3–5 gạch đầu dòng: sự kiện nguy hiểm nhất, nơi, khi nào, mức độ.

## 1. Cảnh báo đang hiệu lực  [Chính thức NWS]
| Mức | Cảnh báo | Khu vực | Hiệu lực (địa phương / VN) | Nguy hiểm chính |
(Nếu không có: "Hiện không có cảnh báo của NWS cho [khu vực] tính đến [giờ].")

## 2. Tình hình thực tế  [Nhà đài xác nhận]
- Thiệt hại, mất điện, giao thông… — (Nguồn: tên đài, giờ đăng)

## 3. Nguy cơ dông bão / mưa lớn / bão nhiệt đới  [SPC • WPC • NHC]
- SPC ngày 1/2/3: mức nguy cơ (Marginal 1/5 … High 5/5), khu vực, các hiểm họa (lốc xoáy, mưa đá, gió).
- WPC ERO: mức (Marginal/Slight/Moderate/High), khu vực.
- NHC: tên bão, vị trí, sức gió, hướng đi, cảnh báo ven biển.

## 4. Dự báo 7 ngày  [NWS]
| Ngày | [Thành phố 1] | [Thành phố 2] | ... |  (cao/thấp °F/°C, hiện tượng, % mưa)

## 5. Theo dõi sớm (3–14 ngày)  [Mô hình — tham khảo]
- Sự kiện có thể xảy ra, thời điểm, khu vực, độ tin cậy, mức đồng thuận giữa các mô hình.

## Nguồn
- Danh sách liên kết + giờ phát hành từng sản phẩm.
```

Bản tin toàn quốc: thay bảng 7 ngày bằng 6–10 thành phố lớn (New York, Washington, Atlanta, Miami, Chicago, Dallas, Houston, Denver, Phoenix, Los Angeles, Seattle) và gom cảnh báo theo bang/sự kiện.

Nếu người dùng muốn bản ngắn (đọc lên sóng / đăng mạng xã hội), viết thêm một đoạn 120–180 chữ ở cuối, giọng biên tập viên, không bỏ nguồn.
