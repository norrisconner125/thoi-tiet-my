# Nguồn chính thức NOAA / NWS

Mọi API của NWS cần header `User-Agent` (ví dụ `thoi-tiet-my`). Không cần API key.

## Cảnh báo (NWS)
| Nội dung | Địa chỉ |
|---|---|
| Cảnh báo theo bang | `https://api.weather.gov/alerts/active?area=TX` (nhiều bang: `area=TX,OK`) |
| Cảnh báo tại một điểm | `https://api.weather.gov/alerts/active?point=29.76,-95.37` |
| Cảnh báo toàn quốc | `https://api.weather.gov/alerts/active` (lọc `?severity=Extreme,Severe`) |
| Đếm cảnh báo theo bang | `https://api.weather.gov/alerts/active/count` |
| Bản đồ cảnh báo | `https://www.weather.gov/` • `https://alerts.weather.gov/` |
| Báo cáo thực tế (LSR) | `https://api.weather.gov/products/types/LSR/locations/{WFO}` • `https://mesonet.agron.iastate.edu/lsr/` |

Trường quan trọng của mỗi cảnh báo: `event`, `severity`, `urgency`, `certainty`, `areaDesc`, `onset`, `ends`, `expires`, `senderName`, `headline`, `description`, `instruction`, `parameters.maxWindGust`, `parameters.maxHailSize`, `parameters.tornadoDetection`.

## Dự báo điểm, 7 ngày, thảo luận (NWS)
| Nội dung | Địa chỉ |
|---|---|
| Thông tin điểm (tìm WFO, ô lưới) | `https://api.weather.gov/points/{lat},{lon}` |
| Dự báo 7 ngày | trường `properties.forecast` của kết quả trên |
| Dự báo theo giờ | `properties.forecastHourly` |
| Area Forecast Discussion | `https://api.weather.gov/products/types/AFD/locations/{WFO}` → lấy `@graph[0].id` → `https://api.weather.gov/products/{id}` |
| Hazardous Weather Outlook | như trên với `HWO` |
| Trang dự báo dạng web | `https://forecast.weather.gov/MapClick.php?lat=..&lon=..` |
| AFD dạng web | `https://forecast.weather.gov/product.php?site=NWS&issuedby={WFO}&product=AFD` |

## SPC – Storm Prediction Center (dông mạnh, lốc xoáy, cháy rừng)
| Nội dung | Địa chỉ |
|---|---|
| Convective Outlook ngày 1/2/3 | `https://www.spc.noaa.gov/products/outlook/day1otlk.html` (đổi `day2`, `day3`) |
| Ngày 4–8 | `https://www.spc.noaa.gov/products/exper/day4-8/` |
| GeoJSON mức nguy cơ | `https://www.spc.noaa.gov/products/outlook/day1otlk_cat.nolyr.geojson` (đổi `day2`, `day3`; xác suất: `_torn`, `_hail`, `_wind`) |
| Watch đang hiệu lực | `https://www.spc.noaa.gov/products/watch/` |
| Mesoscale Discussion | `https://www.spc.noaa.gov/products/md/` |
| Báo cáo dông bão hôm nay/hôm qua | `https://www.spc.noaa.gov/climo/reports/today.html` • `yesterday.html` |
| Thời tiết cháy rừng | `https://www.spc.noaa.gov/products/fire_wx/` |

Thang SPC: TSTM (dông thường) • 1 MRGL Marginal • 2 SLGT Slight • 3 ENH Enhanced • 4 MDT Moderate • 5 HIGH High.

## WPC – Weather Prediction Center (mưa lớn, tuyết, nắng nóng, tổng quan)
| Nội dung | Địa chỉ |
|---|---|
| Excessive Rainfall Outlook ngày 1–5 | `https://www.wpc.ncep.noaa.gov/qpf/excessive_rainfall_outlook_ero.php` |
| GeoJSON ERO (thử nghiệm) | `https://www.wpc.ncep.noaa.gov/exper/eromap/geojson/Day1_Latest.geojson` (`Day2`, `Day3`) |
| Lượng mưa dự báo (QPF) 7 ngày | `https://www.wpc.ncep.noaa.gov/qpf/qpf2.shtml` |
| Thời tiết mùa đông / xác suất tuyết | `https://www.wpc.ncep.noaa.gov/wwd/winter_wx.shtml` |
| Winter Storm Severity Index | `https://www.wpc.ncep.noaa.gov/wwd/wssi/wssi.php` |
| HeatRisk (nắng nóng) | `https://www.wpc.ncep.noaa.gov/heatrisk/` |
| Hazards Outlook 3–7 ngày | `https://www.wpc.ncep.noaa.gov/threats/threats.php` |
| Bản đồ dự báo toàn quốc | `https://www.wpc.ncep.noaa.gov/national_forecast/natfcst.php` |
| Thảo luận ngắn hạn / dài hạn | `https://www.wpc.ncep.noaa.gov/discussions/hpcdiscussions.php?disc=pmdspd` • `?disc=pmdepd` |

Thang ERO: 1 Marginal (≥5%) • 2 Slight (≥15%) • 3 Moderate (≥40%) • 4 High (≥70%) khả năng mưa vượt ngưỡng lũ quét trong 40 km quanh một điểm.

## NHC / CPHC – bão nhiệt đới
| Nội dung | Địa chỉ |
|---|---|
| Trang chính | `https://www.nhc.noaa.gov/` |
| Bão đang hoạt động (JSON) | `https://www.nhc.noaa.gov/CurrentStorms.json` |
| Tropical Weather Outlook 7 ngày | `https://www.nhc.noaa.gov/gtwo.php` |
| Trung Thái Bình Dương (Hawaii) | `https://www.nhc.noaa.gov/?cpac` |

Mùa bão Đại Tây Dương: 1/6–30/11. Đông Thái Bình Dương: 15/5–30/11.

## CPC – Climate Prediction Center (1–4 tuần)
| Nội dung | Địa chỉ |
|---|---|
| Triển vọng 6–10 ngày | `https://www.cpc.ncep.noaa.gov/products/predictions/610day/` |
| Triển vọng 8–14 ngày | `https://www.cpc.ncep.noaa.gov/products/predictions/814day/` |
| Hiểm họa tuần 2 | `https://www.cpc.ncep.noaa.gov/products/predictions/threats/threats.php` |
| Hạn hán | `https://droughtmonitor.unl.edu/` |

## Khác
| Nội dung | Địa chỉ |
|---|---|
| Sông, lũ (NWPS) | `https://water.noaa.gov/` |
| Tuyết phủ (NOHRSC) | `https://www.nohrsc.noaa.gov/` |
| Sóng thần | `https://www.tsunami.gov/` |
| Chất lượng không khí / khói | `https://www.airnow.gov/` • khói HRRR-Smoke: `https://rapidrefresh.noaa.gov/hrrr/HRRRsmoke/` |
| Biển (OPC) | `https://ocean.weather.gov/` |
| Alaska / Hawaii / Puerto Rico | `https://www.weather.gov/afc` • `https://www.weather.gov/hfo` • `https://www.weather.gov/sju` |
