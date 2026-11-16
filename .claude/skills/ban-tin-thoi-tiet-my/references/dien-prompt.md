# Điền PROMPT_USA và viết SRT

## 1. Điền phần VIDEO INFORMATION (mỗi đề tài một bản)

| Trường | Cách điền |
|---|---|
| Date of broadcast | Ngày phát sóng theo giờ Miền Đông Mỹ, dạng `Tuesday, November 10, 2026`. Mọi dữ liệu phải thuộc ngày này (hoặc phát hành trong 24 giờ trước). |
| Primary forecast region | Tên đề tài theo vùng người Mỹ quen gọi + bang: `Southern Plains (Texas)`, `Upper Midwest (Minnesota, Wisconsin, Michigan, North Dakota)`. |
| Video length target | `12-15 minutes` (mặc định của người dùng) trừ khi người dùng nói khác. |
| Main weather event | Hiện tượng chính, đúng thuật ngữ NWS: `tornado outbreak` chỉ dùng khi SPC/NWS hoặc báo cáo thực tế cho thấy nhiều lốc xoáy; nếu chưa có thì `severe thunderstorms with a tornado threat`. `blizzard`, `ice storm`, `atmospheric river`, `heat wave`… cũng phải khớp cảnh báo/sản phẩm chính thức. |
| CURRENT WEATHER DATA | Xem mục 2. |
| FORECAST DATA | Xem mục 3. |

Giữ nguyên mọi phần còn lại của prompt (SCRIPT REQUIREMENTS, STYLE GUIDELINES, yêu cầu SRT, phần KIỂM TRA bằng tiếng Việt). Bỏ dòng dặn "từ tất cả những phân tích và cập nhật trên…".

## 2. CURRENT WEATHER DATA — định dạng
Gạch đầu dòng ngắn, tiếng Anh, mỗi dòng kết thúc bằng `(Source: …, issued/observed <giờ> <múi giờ>)`. Thứ tự:

```
As of 10:00 AM CST, Tuesday, November 10, 2026.
ACTIVE NWS WARNINGS AND WATCHES:
- Tornado Watch #612 for north and central Texas until 9 PM CST; tornadoes, hail up to 2 inches and gusts to 70 mph possible (Source: NWS / Storm Prediction Center, issued 9:40 AM CST)
- Flash Flood Watch for the Dallas-Fort Worth Metroplex through Wednesday morning, 2 to 4 inches of rain, locally 6 (Source: NWS Fort Worth, issued 4:15 AM CST)
SPC OUTLOOK: Enhanced Risk (level 3 of 5) for north Texas today (Source: SPC Day 1 Outlook, 6:00 AM CST)
OBSERVATIONS:
- Dallas/Fort Worth Intl: 72 F, dew point 68 F, south wind 25 mph gusting 50 mph (Source: NWS observation KDFW, 9:53 AM CST)
CONFIRMED REPORTS / IMPACTS (verified):
- Preliminary report of a tornado near Plano, Collin County at 12:30 PM CST (Source: SPC preliminary storm reports); NWS survey pending
- About 120,000 customers without power in Texas (Source: PowerOutage.us, 11:00 AM CST)
- Interstate 35E closed near Denton due to flooding (Source: TxDOT / WFAA, 10:20 AM CST)
NOTABLE FACT (verified): e.g. record rainfall, rare November tornado watch — chỉ khi có nguồn (NWS climate report, NWS social post, đài)
```
- Interstate/highway: chỉ ghi khi có nguồn nói về tác động trên tuyến đó (DOT 511, đài, NWS). Không tự suy ra đường bị ảnh hưởng.
- Wind chill / heat index: lấy từ quan trắc NWS (mục 6a của script) hoặc từ dự báo/cảnh báo NWS.
- Không có tin thiệt hại đã xác thực → ghi `No verified damage reports as of <giờ>.`

## 3. FORECAST DATA — định dạng
```
NEXT 1-3 DAYS (official):
- Dallas, Texas: Today high 78 F, 90 percent chance of storms; Tonight low 48 F; Wednesday high 58 F, north wind 15-25 mph (Source: NWS Fort Worth 7-day forecast, issued 9:12 AM CST)
- SPC Day 2: Slight Risk (level 2 of 5) for Louisiana and Mississippi (Source: SPC Day 2 Outlook, 12:30 AM CST)
- WPC Excessive Rainfall: Moderate Risk (level 3 of 4) for northeast Texas today (Source: WPC, 8:00 AM CST)
- Key points from NWS forecast discussion: <tóm tắt 2-3 ý từ AFD> (Source: NWS Fort Worth AFD, 9:30 AM CST)
INCOMING SYSTEMS / DAYS 3-7 (official):
- <WPC Extended Discussion / Hazards Outlook / SPC Day 4-8 / CPC 6-10>
MODEL GUIDANCE (not official; describe as possibilities):
- Sunday: GFS 0.4 in / ECMWF 1.8 in / ICON 1.5 in / GEM 0.6 in of rain for Houston; 2 of 4 models above 1.5 in; GEFS 20 percent, ECMWF ensemble 55 percent (Source: Open-Meteo model data, <lượt chạy/giờ lấy>) -> GFS and Euro disagree; scenario A (Euro): heavy rain; scenario B (GFS): mostly dry
UNCERTAINTY:
- <điều gì còn chưa chắc: thời gian, vị trí, lượng tuyết; sản phẩm nào sẽ cập nhật lúc mấy giờ>
```
- Số liệu mô hình lấy từ cột "GFS/ECMWF/ICON/GEM" của mục 7 trong kết quả script. Khi GFS và ECMWF lệch nhau rõ rệt → ghi 2 kịch bản như mẫu (prompt yêu cầu "multiple scenarios if models disagree").
- Không đưa tín hiệu mô hình độ tin cậy THẤP vào prompt.

## 4. Bảng rà soát fact-check (bắt buộc sau khi điền và sau khi viết SRT)
| # | Khẳng định / con số | Nguồn | Giờ phát hành | Đúng ngày phát sóng? |
|---|---|---|---|---|
Mỗi con số trong prompt và trong SRT phải có một dòng. Không tìm được nguồn → xóa khỏi prompt/kịch bản.

## 5. Viết SRT
Prompt của người dùng vừa muốn "enthusiastic, show genuine excitement, build tension", vừa cấm "phóng đại, dramatize, suy đoán". Cách dung hòa:
- Hào hứng ở **giọng văn** (nhịp câu, "you guys", "folks in the Carolinas", chuyển đoạn "Now…", "So…"), **không** ở dữ kiện.
- Không dùng: "catastrophic", "apocalyptic", "monster", "historic", "the worst ever", "unprecedented" — trừ khi đúng nguyên văn NWS dùng, kèm "according to the National Weather Service".
- Mọi dự đoán dùng ngôn ngữ của nguồn: "is expected to", "could", "there's a chance"; mô hình: "one model shows… another keeps it…".
- Trích nguồn bằng lời trong câu: "according to the National Weather Service in Fort Worth", "the Storm Prediction Center has an Enhanced Risk, that's a level three out of five".

Định dạng & an toàn TTS:
- Mỗi đoạn: **một câu hoàn chỉnh, 20–25 từ**, kết thúc bằng dấu chấm/chấm than/chấm hỏi. Không xuống dòng giữa câu.
- Prompt yêu cầu "pause indicators" và "mark emphasis", nhưng ký hiệu trong SRT sẽ bị TTS đọc ra → **tạo nhịp nghỉ bằng dấu phẩy và câu ngắn trong giới hạn 20–25 từ**, nhấn mạnh bằng cách đặt từ khóa ở cuối câu; không dùng *, CAPS, (pause), ….
- Viết bằng chữ: "degrees", "percent", "miles per hour", "inches", "6 to 12 inches", "Interstate 95", "EF two", "level three out of five".
- Tên bang đầy đủ (Texas, không TX); viết tắt cơ quan lần đầu viết đầy đủ ("the National Weather Service"), sau đó "the Weather Service".
- Giờ: "by 2 PM", "this evening", "Tuesday night"; luôn nói múi giờ khi nói giờ cụ thể ("9 PM Central").
- Không dấu ngoặc, ngoặc kép, gạch ngang dài, chấm phẩy, đường link, emoji.
- Thời lượng: 150 từ/phút → 12–15 phút ≈ 1.800–2.250 từ ≈ 85–110 đoạn. Phân bổ gợi ý: Opening 2–3 đoạn (30–45 giây), Current Conditions ~35%, Extended Forecast ~25%, Major Event Forecast ~30%, Closing 2–3 đoạn (20–30 giây) có câu "Like and subscribe and turn notifications on" và kết bằng "I'll see you in the next one. Stay safe out there!" (hai câu → tách hoặc nối thành một câu 20–25 từ hợp lệ, ví dụ: "Thanks for watching, so like and subscribe and turn notifications on, and I'll see you in the next one, stay safe out there!").
- Viết xong chạy `scripts/kiem_tra_srt.py … --retime` và sửa đến khi ĐẠT.
