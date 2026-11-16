# Tìm tin kiểu Max Velocity & Ryan Hall

Hai kênh thời tiết lớn nhất YouTube Mỹ tìm đề tài theo hai cách khác nhau. Skill dùng cả hai, nhưng **mọi số liệu vẫn chỉ lấy từ nguồn chính thức** (NOAA/NWS, mô hình có ghi lượt chạy), không lấy từ video của họ.

| | Ryan Hall, Y'all | Max Velocity |
|---|---|---|
| Cách tìm tin | Nhìn **bức tranh lớn**: El Niño, xoáy cực, đổi pattern, kỷ lục trăm năm, mốc ngày lễ | Bám **một cơn bão** và cập nhật mỗi khi mô hình đổi |
| Nguồn họ ghi trong mô tả video | NOAA NCEI, PRISM, NMME/CPC, ECMWF (xoáy cực), NOAA OISST, MRMS, Iowa Environmental Mesonet, ERA5 | Pivotal Weather (bản đồ mô hình), dữ liệu mô hình GFS/ECMWF |
| Video ăn khách nhất | Dự báo tuyết/mùa đông theo vùng, "Hasn't Happened In 100 Years", "Pattern Flips Before Thanksgiving" | "Nobody Has EVER Seen A Winter Like This", "Storm Just Took A Turn", "Just Got WORSE" |

## 1. Năm dạng đề tài và cách phát hiện

Mỗi đề tài trong Bảng đề tài (Bước 2 của SKILL.md) ghi thêm **dạng video**.

### A. Big Picture (kiểu Ryan): El Niño, xoáy cực, đổi pattern, dự báo tháng/mùa, mốc ngày lễ
**Dấu hiệu kích hoạt** (cần ít nhất 1, có nguồn):
- CPC ENSO Discussion mới ra (thứ Năm tuần 2 mỗi tháng), hoặc Niño 3.4 tuần đổi ≥ 0,3°C.
- CPC dự báo tháng/mùa mới ra (thứ Năm tuần 3) hoặc bản cập nhật cuối tháng.
- Thảo luận CPC (tháng, Week 3–4, Hazards) nhắc **SSW / polar vortex disruption / negative AO**.
- CPC Hazards Outlook tuần 2 có nguy cơ **Moderate** trở lên, hoặc nguy cơ trùng dịp lễ đi lại.
- CPC 6–10 và 8–14 ngày đổi màu mạnh so với lần trước (ví dụ nóng → lạnh cho cùng vùng).

**Nguồn:** `scripts/xu_huong_dai_han.py` (phần 1–4, 6). Kiểm tra thêm:
| Nội dung | Địa chỉ |
|---|---|
| Blog ENSO (giải thích dễ hiểu, trích được) | `https://www.climate.gov/news-features/blogs/enso` |
| Blog xoáy cực của NOAA | `https://www.climate.gov/news-features/blogs/polar-vortex` |
| Chỉ số AO / NAO / PNA (quan trắc + dự báo GEFS) | `https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_ao_index/ao.shtml` (đổi `nao.shtml`, `pna.shtml` trong thư mục `pna/`) |
| MJO | `https://www.cpc.ncep.noaa.gov/products/precip/CWlink/MJO/mjo.shtml` |
| Tầng bình lưu (nhiệt độ 10 hPa, gió vòng cực) | `https://www.cpc.ncep.noaa.gov/products/stratosphere/` |
| Dự báo mùa nhiều mô hình (NMME) | `https://www.cpc.ncep.noaa.gov/products/NMME/` |
| Dự báo mùa châu Âu (C3S) | `https://climate.copernicus.eu/charts/c3s_seasonal/` |
| Nhiệt độ mặt biển dị thường | `https://coralreefwatch.noaa.gov/product/5km/index_5km_ssta.php` |
| Giá trị trung bình khí hậu (normals) | `https://prism.oregonstate.edu/normals/` • NOWData `https://www.weather.gov/wrh/climate` |

**Cách nói (bắt buộc):** dự báo tháng/mùa là **xác suất nghiêng về** ("favors above-normal"), không phải chắc chắn. "Super El Niño" không phải thuật ngữ chính thức: nói "a very strong El Niño, often called a super El Niño". SSW chỉ nói "could" cho đến khi CPC hoặc dữ liệu tầng bình lưu xác nhận đã xảy ra. Tác động của SSW lên Mỹ thường trễ 1–4 tuần và không chắc chắn.

### B. Storm Tracker (kiểu Max): một hệ thống, nhiều video nối nhau
**Vòng đời:** `Forecast (7–14 ngày) → Threat Development (3–7 ngày) → Warning (0–2 ngày) → Event Tracking → Aftermath`. Ghi giai đoạn hiện tại của đề tài trong Bảng đề tài.

**Phát hiện "storm just took a turn"**: chỉ dùng cụm này khi có **thay đổi đo được** giữa hai lượt chạy hoặc hai bản sản phẩm chính thức:
| Loại thay đổi | Ngưỡng đáng làm video cập nhật |
|---|---|
| Đường đi tâm áp thấp / dải tuyết | lệch ≥ 100 miles giữa 2 lượt chạy liên tiếp của cùng mô hình, **và** ensemble cùng dịch chuyển |
| Lượng tuyết/mưa tại thành phố chính | đổi ≥ 50% hoặc ≥ 4 inches tuyết / ≥ 1 inch mưa |
| Thời điểm | sớm/muộn ≥ 12 giờ |
| Sản phẩm chính thức | SPC nâng/hạ mức nguy cơ, WPC ERO nâng mức, WSSI tăng cấp, NHC đổi nón dự báo đáng kể, NWS chuyển Watch → Warning |

**Cách so sánh lượt chạy:**
- Open-Meteo Previous Runs API: `https://previous-runs-api.open-meteo.com/v1/forecast?latitude=..&longitude=..&hourly=temperature_2m,precipitation,snowfall&hourly=temperature_2m_previous_day1,precipitation_previous_day1,snowfall_previous_day1&models=gfs_seamless` (hậu tố `_previous_dayN` = dự báo của lượt chạy N ngày trước cho cùng thời điểm).
- So sánh ảnh hai lượt chạy liên tiếp trên Pivotal Weather / Tropical Tidbits / College of DuPage (ghi rõ "GFS 12Z vs 06Z").
- Đọc WPC Short Range / Extended Discussion: tìm các từ "trend", "shifted", "faster", "slower", "farther north/south".
- Ghi vào ghi chú biên tập: lượt chạy cũ, lượt chạy mới, thay đổi bao nhiêu.

### C. Records & Rare (cả hai kênh, mạnh nhất ở Shorts)
**Dấu hiệu kích hoạt:**
- Nhiều Record Event Report (RER) **cùng loại, cùng vùng** trong 24–48 giờ (script phần 5).
- NWS / CPC / thảo luận WPC dùng các từ "record", "rare", "unprecedented", "first time since".
- Chỉ số vượt kỷ lục quan trắc (ví dụ Niño 3.4 tuần cao nhất từ trước đến nay).

**Nguồn xác minh "lần đầu kể từ năm …":**
| Nội dung | Địa chỉ |
|---|---|
| Kỷ lục từng trạm, chuỗi dài | xmACIS `https://xmacis.rcc-acis.org/` • NOWData `https://www.weather.gov/wrh/climate` |
| Kỷ lục ngày toàn quốc | `https://www.ncei.noaa.gov/access/monitoring/daily-records/` |
| Xếp hạng tháng/mùa theo bang | NCEI Climate at a Glance `https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/` |
| Lưu trữ cảnh báo, radar, LSR | Iowa Environmental Mesonet `https://mesonet.agron.iastate.edu/` |

**Quy tắc:** "This hasn't happened in 100 years" chỉ dùng khi dữ liệu trạm cho thấy đúng như vậy, và nói rõ **ở đâu** ("in Chicago's records, which go back to 1871"). Không suy từ một trạm ra cả bang.

### D. State Spotlight (Shorts theo bang)
Lấy một bang có tín hiệu **ngược với cả nước** hoặc ngược với điều người dân bang đó chờ đợi (ví dụ "Ohio's Winter Flips Warm"). Nguồn: CPC (tháng/mùa) tại bang đó + NWS 7 ngày + AFD văn phòng NWS trong bang. Một Short = một kết luận + một nguồn.

### E. Aftermath
Sau sự kiện 1–3 ngày: tổng tuyết/mưa (NWS PNS, NOHRSC), kết quả khảo sát lốc xoáy (PNS, Damage Assessment Toolkit), kỷ lục (RER), so sánh dự báo với thực tế. Thiệt hại và thương vong theo Bước 3 của SKILL.md.

## 2. Theo dõi đối thủ để chọn đề tài (không sao chép)

Mục đích: biết đề tài nào đang hút người xem, rồi tìm **khoảng trống**. Không dùng số liệu, bản đồ, câu chữ hay kết luận của họ làm nguồn.
- Trang kênh: `https://www.youtube.com/@RyanHallYall/videos`, `https://www.youtube.com/@MaxVelocityWX/videos`, và tab Shorts, Posts (Community).
- RSS (không cần đăng nhập): `https://www.youtube.com/feeds/videos.xml?channel_id=<ID>`. Lấy ID bằng cách mở trang kênh, tìm chuỗi `"channelId":"UC…"`.
- Nếu người dùng dán số liệu vidIQ (VPH, x): video có VPH cao hoặc ≥ 1,5x trong 24–48 giờ = đề tài đang nóng.
- Cách dùng:
  1. Đề tài đối thủ đang nóng **và** có sản phẩm chính thức hỗ trợ → làm, nhưng chọn **góc khác**: vùng họ chưa nói, khung thời gian khác (ví dụ họ nói cả mùa, mình nói 2 tuần tới), hoặc dạng khác (họ làm Short, mình làm video dài).
  2. Đề tài họ mới chỉ có Short (ví dụ sông khí quyển, bão băng) mà CPC/WPC đang có nguy cơ → ưu tiên làm video dài.
  3. Đề tài họ nói mà nguồn chính thức **không** ủng hộ → không làm, hoặc làm video "what the data actually shows" với nguồn rõ ràng.
- Trong môi trường không vào được YouTube: yêu cầu người dùng dán danh sách video mới nhất (tiêu đề, view, thời gian, VPH).

## 3. Lịch mốc cố định (script phần 6 in tự động 3 tuần tới)
| Sản phẩm | Lịch |
|---|---|
| CPC ENSO Discussion | thứ Năm tuần 2 mỗi tháng |
| CPC dự báo tháng + mùa | thứ Năm tuần 3; cập nhật dự báo tháng tới vào ngày cuối tháng |
| CPC Week 3–4 | thứ Sáu hằng tuần |
| CPC 6–10 / 8–14 ngày, Hazards tuần 2 | hằng ngày, khoảng 3 giờ chiều ET |
| US Drought Monitor | thứ Năm hằng tuần |
| NOAA Winter Outlook | giữa tháng 10 |
| NOAA Hurricane Outlook | cuối tháng 5 |
| Mùa bão Đại Tây Dương | 1/6 – 30/11 |

Đề tài gắn mốc lễ (Thanksgiving, Christmas, New Year, July 4th, Memorial Day, Labor Day, Halloween) nên ra **5–10 ngày trước lễ**.

## 4. Từ ngữ kiểu tiêu đề của hai kênh: khi nào được dùng
| Cụm từ | Chỉ dùng khi |
|---|---|
| "Just took a turn" / "Just got worse" | Có thay đổi đạt ngưỡng ở mục 1B, ghi rõ lượt chạy |
| "Make HISTORY" / "Hasn't happened in 100 years" | Có dữ liệu kỷ lục ở mục 1C, nêu trạm và năm bắt đầu lưu |
| "Super El Niño" | Niño 3.4 ≥ +2,0°C và CPC nói "very strong"; trong lời đọc vẫn giải thích là cách gọi không chính thức |
| "Polar vortex" | CPC hoặc dữ liệu tầng bình lưu nhắc gián đoạn xoáy cực / SSW, hoặc NWS dùng từ này |
| "Pattern flips" | CPC 6–10/8–14 hoặc Week 3–4 đổi dấu nhiệt độ cho cùng vùng |
| "Everyone is wrong" / "Nobody has ever seen" | **Không dùng**: không kiểm chứng được và trái quy tắc không giật gân |
