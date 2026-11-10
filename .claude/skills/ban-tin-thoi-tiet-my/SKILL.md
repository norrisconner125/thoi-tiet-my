---
name: ban-tin-thoi-tiet-my
description: Tìm, xác thực và tổng hợp tin thời tiết toàn nước Mỹ thành các gói video YouTube tiếng Anh cho khán giả Mỹ: phân loại và chọn tin hot nhất trong ngày theo khu vực (gộp các bang liền kề cùng loại sự kiện), tách riêng bang có sự kiện đủ lớn; mỗi đề tài một gói (kịch bản chia đoạn, tiêu đề, mô tả, tag, gợi ý hình ảnh). Cảnh báo/dự báo lấy từ NOAA–NWS (SPC, WPC, NHC, CPC), tin thiệt hại đối chiếu với nhà đài địa phương uy tín, báo sớm 3–14 ngày bằng số liệu mô hình GFS, ECMWF, ICON, GEM và ensemble. Dùng khi người dùng xin bản tin, kịch bản, video, cảnh báo, dự báo, tin bão, lốc xoáy, bão tuyết, lũ, nắng nóng, đợt lạnh cho nước Mỹ, một vùng, bang hoặc thành phố, hoặc gọi /ban-tin-thoi-tiet-my.
---

# Bản tin thời tiết Mỹ → gói video YouTube

**Người dùng**: biên tập viên người Việt, làm kênh YouTube thời tiết **cho người Mỹ xem**, phạm vi **toàn nước Mỹ**.
- Trò chuyện, giải thích, ghi chú biên tập: **tiếng Việt**.
- Sản phẩm đăng tải (kịch bản đọc, tiêu đề, mô tả, tag, chữ trên hình): **tiếng Anh Mỹ**, đơn vị Mỹ (°F, mph, inches, miles), giờ Mỹ (ET/CT/MT/PT…).
- Mặc định phạm vi toàn quốc, trừ khi người dùng nêu bang/vùng/thành phố.

Uy tín kênh = độ chính xác. Thứ tự nguồn: **NWS/NOAA (chính thức) → nhà đài địa phương uy tín (xác thực thực tế) → mô hình (báo sớm, luôn nói là "possible/could")**.

## Bước 1 — Thu thập dữ liệu (bắt buộc)

Chạy script (thử trước tiên; nếu không có mạng hoặc lỗi thì làm Bước 1b cho phần lỗi):

```bash
python3 scripts/tong_hop_nws.py                 # toàn quốc (mặc định)
python3 scripts/tong_hop_nws.py --area TX,OK    # bang
python3 scripts/tong_hop_nws.py --city "Denver, CO"
```
(Đường dẫn tính từ thư mục skill; trong repo là `.claude/skills/ban-tin-thoi-tiet-my/scripts/tong_hop_nws.py`.)

Script trả về: cảnh báo NWS đang hiệu lực (gom theo loại → bang), SPC Day 1–3 (mức cao nhất + đoạn SUMMARY), Mesoscale Discussions,
Storm Reports hôm nay/hôm qua, nguy cơ SPC/WPC ERO tại ~40 thành phố, bão NHC + Tropical Weather Outlook, WPC Short Range/Extended Discussion,
CPC 6–10/8–14, dự báo 7 ngày NWS 12 thành phố, AFD, và **tín hiệu mô hình** 10 ngày (mưa lớn, tuyết, gió giật, nóng, rét)
có số mô hình đồng thuận + % ensemble + độ tin cậy. Cuối bản in là danh sách nguồn lỗi — mỗi nguồn lỗi phải kiểm tra tay.

### Bước 1b — Kiểm tra tay trên web
Luôn xem thêm (script không lấy): **SPC Day 4–8**, **WPC Hazards Outlook 3–7 ngày**, **WPC Key Messages** (khi có sự kiện lớn), sông lũ (water.noaa.gov).
Địa chỉ: `references/nguon-noaa-nws.md`. Đọc mô hình: `references/radar-va-mo-hinh.md`.

## Bước 2 — Phân loại & chọn tin hot theo khu vực / bang (bắt buộc)

Chi tiết cách chấm và điều chỉnh: `references/phan-loai-tin.md`. Tóm tắt:
1. Script in sẵn **"0. BẢNG XẾP HẠNG ĐỀ TÀI"**: chấm điểm từng bang (cảnh báo NWS, SPC, WPC ERO, Storm Reports, tín hiệu mô hình),
   gom **các bang liền kề cùng loại sự kiện** thành một đề tài khu vực, và **tách riêng bang nào đạt ≥45 điểm** thành đề tài riêng.
2. Claude **điều chỉnh** điểm bằng tin tức đã xác thực (Bước 3): thương vong, thiệt hại lớn, kỷ lục, thành phố lớn bị ảnh hưởng,
   mức độ báo chí quốc gia đưa tin. Một bang có thể được nâng lên video riêng (hoặc gộp lại) nếu tin tức cho thấy khác với điểm tự động — ghi rõ lý do.
3. Loại sự kiện gồm: dông mạnh/lốc xoáy, bão nhiệt đới, mưa lớn/lũ, bão tuyết/băng giá, rét, nắng nóng, cháy rừng, gió mạnh, ngập ven biển.
   Hai hiện tượng khác loại ở hai bang liền kề → **hai đề tài khác nhau** (trừ khi cùng một hệ thống, ví dụ một cơn bão gây cả tuyết lẫn dông — khi đó gộp và nêu cả hai).
4. Chốt **Bảng đề tài trong ngày** (tiếng Việt) cho người dùng: thứ tự, tên đề tài, loại (bang riêng/khu vực), bang, hiện tượng, thời điểm, mức (RẤT HOT/HOT/ĐÁNG CHÚ Ý), lý do 1 dòng.
5. Đề tài cùng một hệ thống thời tiết (ví dụ video Texas riêng + video "South outside Texas"): mỗi video **nhắc chéo** video kia trong 1 câu, không lặp nội dung chi tiết.
6. Không có đề tài nào đạt ngưỡng → làm **1 video tổng hợp toàn quốc** (dự báo 7 ngày các thành phố lớn + sự kiện sắp tới).

## Bước 3 — Xác thực tin thực tế (thiệt hại, mất điện, thương vong, sơ tán)

Theo `references/nha-dai-theo-bang.md`. Quy tắc:
1. Chỉ dùng tin **đăng trong 24 giờ** và **đúng sự kiện** (đúng địa danh, đúng thời điểm với cảnh báo/Storm Reports).
2. Mỗi thông tin cần **≥1 nguồn uy tín**: nhà đài địa phương thuộc mạng lớn, AP/Reuters, cơ quan quản lý khẩn cấp bang/hạt, NWS. Số thương vong, sơ tán: **chỉ từ cơ quan chính quyền** (hoặc đài trích dẫn cơ quan đó) — ghi rõ "according to…".
3. **Cấp lốc xoáy (EF)**, vận tốc gió ước tính, đường đi lốc: **chỉ từ khảo sát thiệt hại của NWS** (Public Information Statement / Damage Assessment Toolkit). Trước khi có khảo sát: nói "a tornado was reported" / "NWS survey teams will determine the rating".
4. Storm Reports của SPC là **báo cáo sơ bộ** — nói "preliminary reports", không cộng thành con số chính thức.
5. Mất điện: PowerOutage.us hoặc công ty điện, ghi thời điểm.
6. Video/ảnh mạng xã hội: không dùng làm nguồn sự thật; nếu nhắc tới phải nói rõ "unverified" — tốt nhất bỏ.
7. Hai nguồn mâu thuẫn → dùng số của cơ quan chính quyền/NWS, hoặc nói khoảng ("at least…").

## Bước 4 — Quy tắc chính xác (không được vi phạm)

- **Không bịa số.** Mọi con số phải có trong dữ liệu đã lấy ở phiên này. Không có → không nói.
- **Thời điểm**: ghi giờ phát hành sản phẩm; bỏ cảnh báo đã hết hạn; nói rõ "as of [time] ET".
- **Ngôn ngữ xác suất** cho mô hình và ngày ≥3: "could", "is expected to", "there's a chance". Không dùng con số tuyết/mưa cụ thể cho một thành phố khi >72 giờ — dùng khoảng và "still uncertain".
- Độ tin cậy mô hình: CAO → "models agree"; TRUNG BÌNH → "some models show"; THẤP → không đưa vào video (chỉ ghi chú biên tập).
- Không giật gân: không "apocalyptic", "monster", "historic" (trừ khi NWS dùng), không tiêu đề hứa điều video không có.
- Nhắc người xem theo dõi văn phòng NWS địa phương và làm theo hướng dẫn của chính quyền khi có cảnh báo.

## Bước 5 — Gói sản phẩm (đầu ra)

Thứ tự trả lời:
1. **Bảng đề tài trong ngày** (tiếng Việt) — như Bước 2.4.
2. **Một gói video riêng cho mỗi đề tài RẤT HOT và HOT** (tối đa 5, theo thứ tự điểm), theo mẫu `references/mau-youtube.md`.
   Đề tài ĐÁNG CHÚ Ý: chỉ liệt kê kèm 2–3 ý chính; người dùng muốn thì làm gói đầy đủ sau.
   Nếu số đề tài HOT nhiều hơn 5 hoặc thông tin quá dài: làm đầy đủ 2 đề tài đầu, các đề tài còn lại hỏi người dùng có muốn làm tiếp không.
3. Tùy chọn: 1 video **National Roundup** ngắn tổng hợp mọi đề tài (khi người dùng xin, hoặc khi các đề tài đều chỉ ở mức ĐÁNG CHÚ Ý).

Mỗi gói video gồm:
1. **Ghi chú biên tập (tiếng Việt)** — đề tài, bang, độ tin cậy, điểm cần cẩn trọng, nguồn bị lỗi.
2. **Title** — 3 phương án (≤70 ký tự), nêu đúng bang/khu vực của đề tài. **Thumbnail text** — 2–4 từ.
3. **Script** — tiếng Anh, chia **đoạn đánh số 1…N** (mỗi đoạn = một file voice `N.mp3`, 1–3 câu, ~8–20 giây), mỗi đoạn kèm cột **Visual** (bản đồ/lớp dữ liệu/khu vực cần hiển thị) để dựng video.
4. **Description** — tóm tắt, chapter timestamps (ước lượng), nguồn có link, disclaimer.
5. **Tags** và **Hashtags** (có tên bang/thành phố của đề tài).
6. **Bảng nguồn & giờ phát hành**.
7. Nếu người dùng cần: file **SRT** (ước lượng 2.5 từ/giây) hoặc lưu từng gói ra file `.md` riêng (tên file theo đề tài, ví dụ `2026-11-10_texas-severe-storms.md`).

Độ dài: video bang riêng 3–6 phút; video khu vực 4–7 phút; Shorts (khi được xin) 45–60 giây, 5–8 đoạn.

## Thuật ngữ
`references/thuat-ngu.md` (Anh ↔ Việt, thang SPC/ERO/EF/Saffir-Simpson, múi giờ) — dùng khi giải thích cho người dùng; kịch bản giữ thuật ngữ gốc tiếng Anh.
