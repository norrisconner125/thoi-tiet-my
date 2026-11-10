# Radar, vệ tinh và mô hình thời tiết

Dùng để mô tả tình hình hiện tại và **báo sớm** sự kiện khi chưa có cảnh báo. Mọi nhận định từ mô hình ghi nhãn **[Mô hình — tham khảo]**.

## Radar / vệ tinh (hiện tại)
| Nguồn | Địa chỉ | Ghi chú |
|---|---|---|
| NWS Radar | `https://radar.weather.gov/` | NEXRAD từng trạm, khảm toàn quốc |
| MRMS (NOAA) | `https://mrms.ncep.noaa.gov/` | Mưa đá, xoáy quay (rotation track), lượng mưa ước tính |
| GOES (NESDIS) | `https://www.star.nesdis.noaa.gov/GOES/` | Vệ tinh GOES-East/West, sét GLM |
| SPC Mesoanalysis | `https://www.spc.noaa.gov/exper/mesoanalysis/` | CAPE, đứt gió, chỉ số lốc xoáy STP |
| Iowa Mesonet | `https://mesonet.agron.iastate.edu/` | Lưu radar, cảnh báo, LSR |

## Mô hình — chọn theo khung thời gian
| Khung | Mô hình | Dùng để |
|---|---|---|
| 0–18 giờ | HRRR (3 km, chạy mỗi giờ), RAP | Thời điểm/đường đi dông, dải tuyết, khói |
| 0–60 giờ | NAM 3 km, RRFS, HREF (ensemble CAM) | Kiểu dông (đơn bào/đường dông), lượng mưa cục bộ |
| 1–10 ngày | GFS, ECMWF IFS/AIFS, ICON, CMC (GDPS) | Hệ thống áp thấp, mặt trận, bão tuyết, đợt lạnh/nóng |
| 1–16 ngày | GEFS, ECMWF EPS (ensemble) | Độ tin cậy, xác suất |
| Hướng dẫn NWS | NBM (National Blend of Models) | Gần với dự báo chính thức nhất |
| Bão nhiệt đới | HAFS, HWRF/HMON (cũ), mô hình xoáy ECMWF/GFS, TCVN/HCCA (đồng thuận NHC) | Đường đi, cường độ — **luôn ưu tiên NHC** |

## Trang xem mô hình
| Trang | Địa chỉ |
|---|---|
| NOAA NOMADS (dữ liệu gốc) | `https://nomads.ncep.noaa.gov/` |
| WPC Model Diagnostics | `https://www.wpc.ncep.noaa.gov/mdd/` |
| ECMWF Charts (mở) | `https://charts.ecmwf.int/` |
| NBM Viewer | `https://blend.mdl.nws.noaa.gov/` |
| College of DuPage | `https://weather.cod.edu/forecast/` |
| Pivotal Weather | `https://www.pivotalweather.com/model.php` |
| Tropical Tidbits | `https://www.tropicaltidbits.com/analysis/models/` |

## Cách viết nhận định sớm
1. So sánh ít nhất **2 mô hình toàn cầu + 1 ensemble** (ví dụ GFS, ECMWF, GEFS/EPS).
2. Đối chiếu với sản phẩm chính thức cùng khung: SPC Day 4–8, WPC Hazards 3–7, CPC 6–10/8–14, NHC TWO.
3. Độ tin cậy:
   - **Cao**: mô hình và ensemble đồng thuận, SPC/WPC đã vẽ vùng nguy cơ.
   - **Trung bình**: hệ thống chắc chắn có nhưng vị trí/thời gian lệch 12–24 giờ hoặc 150–300 km.
   - **Thấp**: chỉ một mô hình hoặc một lượt chạy cho thấy; ensemble phân tán.
4. Cấm viết số tuyết/mưa cụ thể cho một thành phố từ mô hình >72 giờ; dùng khoảng ("10–25 cm có thể") và nói rõ còn thay đổi.
5. Ghi lượt chạy đã xem (ví dụ "GFS 12Z 10/11").
