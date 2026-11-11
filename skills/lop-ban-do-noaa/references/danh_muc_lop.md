# Danh mục lớp bản đồ NOAA

Mỗi lớp: mã · tên · chip trên video · thời gian · biến thể. Chọn biến thể bằng `mã:số` (thứ tự) hoặc `mã:đoạn nhãn` (vd `qpf:Tổng 3`, `lsr:72`).
Xem nhanh trong terminal: `python -X utf8 xuat.py --danh-sach [từ khoá]`.

## Mục lục
- Vệ tinh GOES (`sat`)
- Radar & sét (`radar`)
- Quan trắc thực tế (`obs`)
- Dự báo (`fcst`)
- Giông lốc · lũ · cháy rừng (`severe`)
- Mùa đông: tuyết, băng (`winter`)
- Bão nhiệt đới (`tropic`)
- Triển vọng dài hạn (CPC) (`long`)
- Thủy văn & môi trường (`env`)
- Hàng không (`avn`)

## Vệ tinh GOES (`sat`)

**`sat_vis`** — Ảnh mây thật (Visible) · chip `SATELLITE` · chạy ~8 giờ gần nhất (`vong` gio)
  Chỉ có ban ngày (sáng sớm miền Tây còn tối).
  Nguồn: NOAA nowCOAST / GOES

**`sat_ir`** — Hồng ngoại – đỉnh mây lạnh (IR) · chip `INFRARED SATELLITE` · chạy ~8 giờ gần nhất (`vong` gio)
  Mây càng sáng/lạnh càng cao, giông càng mạnh. Dùng được cả đêm.
  Nguồn: NOAA nowCOAST / GOES

**`sat_wv`** — Hơi nước tầng cao (Water Vapor) · chip `WATER VAPOR` · chạy ~8 giờ gần nhất (`vong` gio)
  Thấy dòng tia, rãnh áp thấp, khí khô.
  Nguồn: NOAA nowCOAST / GOES

**`sat_sw`** — Sóng ngắn – sương mù, điểm cháy (Shortwave) · chip `SHORTWAVE IR` · chạy ~8 giờ gần nhất (`vong` gio)
  Nguồn: NOAA nowCOAST / GOES

**`sat_snow`** — Phân biệt tuyết và mây (Snow/Ice) · chip `SNOW / ICE SATELLITE` · chạy ~8 giờ gần nhất (`vong` gio)
  Nguồn: NOAA nowCOAST / GOES

## Radar & sét (`radar`)

**`radar`** — Radar khảm NEXRAD (chạy theo giờ, có lưu trữ) · chip `RADAR` · chạy giờ quá khứ (`vong` tu/den, hoặc `luc`)
  Lớp radar chính. Chạy được bất kỳ khung giờ nào trong quá khứ (lưu trữ từ 1995), bước 5 phút.
  Nguồn: NWS NEXRAD via Iowa Environmental Mesonet

**`rad_cref`** — Phản hồi tổng hợp (Composite Reflectivity) · chip `COMPOSITE RADAR` · chỉ bản mới nhất
  Cường độ mạnh nhất trên cả cột khí – thấy lõi mưa đá.
  Nguồn: NOAA/NCEP MRMS

**`rad_ptype`** — Loại mưa: mưa / tuyết / băng (Precip Type) · chip `PRECIP TYPE` · chỉ bản mới nhất
  Nguồn: NOAA/NCEP MRMS

**`rad_tops`** — Độ cao đỉnh mây vang (Echo Tops) · chip `ECHO TOPS` · chỉ bản mới nhất
  Đỉnh càng cao, giông càng mạnh.
  Nguồn: NOAA/NCEP MRMS

**`rad_site`** — Radar từng trạm: vận tốc gió (Velocity) · chip `DOPPLER RADAR` · chỉ bản mới nhất
  Xanh: gió hướng về radar, đỏ: gió đi ra xa. Xanh – đỏ sát nhau = vòng xoáy (dấu hiệu lốc xoáy).
  Biến thể: `0` Vận tốc (Velocity) (Velocity) · `1` Vận tốc tương đối với ô bão (SRV) (Storm-Relative Velocity) · `2` Phản hồi độ phân giải cao (N0B) (Reflectivity)
  Nguồn: NWS NEXRAD via Iowa Environmental Mesonet

**`lightning`** — Mật độ sét (Lightning) · chip `LIGHTNING` · chỉ bản mới nhất
  Nguồn: NOAA nowCOAST

## Quan trắc thực tế (`obs`)

**`obs_sfc`** — Bảng số trạm: nhiệt độ, điểm sương, áp suất · chip `SURFACE OBS` · chỉ bản mới nhất
  Đỏ: nhiệt độ (°F) · xanh lá: điểm sương (°F) · xanh dương: áp suất (mb). Phóng to để thấy thêm trạm.
  Nguồn: NWS / NOAA

**`obs_wind`** — Gió quan trắc tại sân bay (mũi tên gió) · chip `WIND` · chỉ bản mới nhất
  Nguồn: NWS / AWC

**`obs_cloud`** — Độ che phủ mây · chip `CLOUD COVER` · chỉ bản mới nhất
  Nguồn: NWS / NOAA

**`lsr`** — Báo cáo thiệt hại: lốc, mưa đá, gió, lũ (LSR) · chip `STORM REPORTS` · chỉ bản mới nhất
  Biến thể: `0` 24 giờ qua (Past 24 Hours) · `1` 48 giờ qua (Past 48 Hours) · `2` 72 giờ qua (Past 72 Hours)
  Nguồn: NWS Local Storm Reports

**`qpe`** — Lượng mưa đã rơi (Observed Precip) · chip `OBSERVED RAIN` · chỉ bản mới nhất
  Biến thể: `0` 1 giờ qua (Past Hour) · `1` 3 giờ qua (Past 3 Hours) · `2` 6 giờ qua (Past 6 Hours) · `3` 24 giờ qua (Past 24 Hours) · `4` 72 giờ qua (Past 72 Hours) · `5` 7 ngày qua (Past 7 Days) · `6` 30 ngày qua (Past 30 Days) · `7` Từ đầu tháng (Month to Date) · `8` % so với bình thường – 30 ngày (% of Normal · 30 Days)
  Nguồn: NWS River Forecast Centers

**`snow_depth`** — Độ dày tuyết trên mặt đất · chip `SNOW COVER` · chỉ bản mới nhất
  Biến thể: `0` Độ dày tuyết (Snow Depth) · `1` Lượng nước trong tuyết (SWE) (Snow Water Equivalent)
  Nguồn: NOAA NOHRSC

**`snow_cover`** — Vùng phủ tuyết & băng (1 km) · chip `SNOW & ICE` · chỉ bản mới nhất
  Nguồn: U.S. National Ice Center

## Dự báo (`fcst`)

**`hrrr`** — Radar dự báo HRRR (Future Radar) · chip `FUTURE RADAR · HRRR` · chạy theo giờ dự báo (`id:*`)
  Mô phỏng radar từ lượt chạy HRRR mới nhất, tới 18 giờ. Bấm ▶ để chạy.
  Biến thể: `0` +1 giờ (+1 HR) · `1` +2 giờ (+2 HR) · `2` +3 giờ (+3 HR) · `3` +4 giờ (+4 HR) · `4` +5 giờ (+5 HR) · `5` +6 giờ (+6 HR) · `6` +7 giờ (+7 HR) · `7` +8 giờ (+8 HR) · `8` +9 giờ (+9 HR) · `9` +10 giờ (+10 HR) · `10` +11 giờ (+11 HR) · `11` +12 giờ (+12 HR) · `12` +13 giờ (+13 HR) · `13` +14 giờ (+14 HR) · `14` +15 giờ (+15 HR) · `15` +16 giờ (+16 HR) · `16` +17 giờ (+17 HR) · `17` +18 giờ (+18 HR)
  Nguồn: NOAA HRRR via Iowa Environmental Mesonet

**`chart`** — Bản đồ dự báo toàn quốc: front, H/L, vùng mưa · chip `NATIONAL FORECAST` · chỉ bản mới nhất
  Biến thể: `0` Hôm nay – đầy đủ (Today) · `1` Ngày mai – đầy đủ (Tomorrow) · `2` Ngày kia – đầy đủ (Day 3) · `3` Hôm nay – chỉ front & H/L (Today · Fronts) · `4` Ngày mai – chỉ front & H/L (Tomorrow · Fronts)
  Nguồn: NOAA WPC

**`ndfd_t`** — Nhiệt độ dự báo theo giờ · chip `TEMPERATURE` · chỉ bản mới nhất
  Biến thể: `0` Sau +3 giờ (+3 HR) · `1` Sau +6 giờ (+6 HR) · `2` Sau +9 giờ (+9 HR) · `3` Sau +12 giờ (+12 HR) · `4` Sau +15 giờ (+15 HR) · `5` Sau +18 giờ (+18 HR) · `6` Sau +21 giờ (+21 HR) · `7` Sau +24 giờ (+24 HR)
  Nguồn: NWS NDFD

**`ndfd_max`** — Nhiệt độ cao nhất / thấp nhất · chip `FORECAST TEMPS` · chỉ bản mới nhất
  Biến thể: `0` Cao nhất hôm nay (Highs Today) · `1` Cao nhất ngày mai (Highs Tomorrow) · `2` Cao nhất ngày kia (Highs Day 3) · `3` Thấp nhất đêm nay (Lows Tonight) · `4` Thấp nhất đêm mai (Lows Tomorrow Night)
  Nguồn: NWS NDFD

**`ndfd_apt`** — Nhiệt độ cảm nhận (Heat Index / Wind Chill) · chip `FEELS LIKE` · chỉ bản mới nhất
  Biến thể: `0` Sau +3 giờ (+3 HR) · `1` Sau +6 giờ (+6 HR) · `2` Sau +9 giờ (+9 HR) · `3` Sau +12 giờ (+12 HR) · `4` Sau +15 giờ (+15 HR) · `5` Sau +18 giờ (+18 HR) · `6` Sau +21 giờ (+21 HR) · `7` Sau +24 giờ (+24 HR)
  Nguồn: NWS NDFD

**`ndfd_rh`** — Độ ẩm tương đối · chip `HUMIDITY` · chỉ bản mới nhất
  Biến thể: `0` Sau +3 giờ (+3 HR) · `1` Sau +6 giờ (+6 HR) · `2` Sau +9 giờ (+9 HR) · `3` Sau +12 giờ (+12 HR) · `4` Sau +15 giờ (+15 HR) · `5` Sau +18 giờ (+18 HR) · `6` Sau +21 giờ (+21 HR) · `7` Sau +24 giờ (+24 HR)
  Nguồn: NWS NDFD

**`qpf`** — Lượng mưa dự báo (QPF) · chip `RAIN FORECAST` · chỉ bản mới nhất
  Miền dữ liệu có rìa cắt chéo ngoài Đại Tây Dương (khoảng kinh độ −68°): khung miền Đông nên dừng ở lon1 ≈ −69.
  Biến thể: `0` 6 giờ tới (Next 6 Hours) · `1` Ngày 1 (Day 1) · `2` Ngày 2 (Day 2) · `3` Ngày 3 (Day 3) · `4` Tổng 2 ngày (2-Day Total) · `5` Tổng 3 ngày (3-Day Total) · `6` Tổng 5 ngày (5-Day Total) · `7` Tổng 7 ngày (7-Day Total)
  Nguồn: NOAA WPC

## Giông lốc · lũ · cháy rừng (`severe`)

**`spc`** — Nguy cơ giông lốc SPC (Convective Outlook) · chip `SPC OUTLOOK` · chỉ bản mới nhất
  TSTM giông thường · MRGL 1 · SLGT 2 · ENH 3 · MDT 4 · HIGH 5.
  Biến thể: `0` Ngày 1 · 5 cấp nguy cơ (Day 1 · Categorical) · `1` Ngày 1 · xác suất lốc xoáy (Day 1 · Tornado Probability) · `2` Ngày 1 · xác suất mưa đá (Day 1 · Hail Probability) · `3` Ngày 1 · xác suất gió mạnh (Day 1 · Wind Probability) · `4` Ngày 2 · 5 cấp nguy cơ (Day 2 · Categorical) · `5` Ngày 2 · xác suất lốc xoáy (Day 2 · Tornado Probability) · `6` Ngày 2 · xác suất mưa đá (Day 2 · Hail Probability) · `7` Ngày 2 · xác suất gió mạnh (Day 2 · Wind Probability) · `8` Ngày 3 · 5 cấp nguy cơ (Day 3 · Categorical) · `9` Ngày 3 · xác suất (Day 3 · Severe Probability) · `10` Ngày 4 (Day 4) · `11` Ngày 5 (Day 5) · `12` Ngày 6 (Day 6) · `13` Ngày 7 (Day 7) · `14` Ngày 8 (Day 8)
  Nguồn: NOAA Storm Prediction Center

**`spc_md`** — Thảo luận khẩn SPC (Mesoscale Discussion) · chip `SPC MESOSCALE DISCUSSION` · chỉ bản mới nhất
  Vùng SPC đang theo dõi, thường sắp ra Watch.
  Nguồn: NOAA Storm Prediction Center

**`ero`** — Nguy cơ mưa lớn gây lũ quét (ERO) · chip `EXCESSIVE RAINFALL OUTLOOK` · chỉ bản mới nhất
  Biến thể: `0` Ngày 1 (Day 1) · `1` Ngày 2 (Day 2) · `2` Ngày 3 (Day 3) · `3` Ngày 4 (Day 4) · `4` Ngày 5 (Day 5)
  Nguồn: NOAA WPC

**`ffg`** — Ngưỡng mưa gây lũ quét (Flash Flood Guidance) · chip `FLASH FLOOD GUIDANCE` · chỉ bản mới nhất
  Lượng mưa (inch) đủ để gây lũ quét. Càng thấp càng dễ lũ.
  Biến thể: `0` Trong 1 giờ (1-Hour) · `1` Trong 3 giờ (3-Hour) · `2` Trong 6 giờ (6-Hour) · `3` Trong 12 giờ (12-Hour) · `4` Trong 24 giờ (24-Hour)
  Nguồn: NWS River Forecast Centers

**`fire`** — Nguy cơ cháy rừng SPC · chip `FIRE WEATHER OUTLOOK` · chỉ bản mới nhất
  Biến thể: `0` Ngày 1 · gió & khô (Day 1 · Wind & Low RH) · `1` Ngày 1 · giông khô (Day 1 · Dry Thunderstorms) · `2` Ngày 2 · gió & khô (Day 2 · Wind & Low RH) · `3` Ngày 2 · giông khô (Day 2 · Dry Thunderstorms) · `4` Ngày 3–8 · gió & khô (Days 3-8 · Wind & Low RH)
  Nguồn: NOAA Storm Prediction Center

## Mùa đông: tuyết, băng (`winter`)

**`wssi`** — Mức tác động bão tuyết (WSSI) · chip `WINTER STORM SEVERITY` · chỉ bản mới nhất
  Biến thể: `0` Tổng thể · 3 ngày (Overall · Days 1-3) · `1` Tổng thể · ngày 1 (Overall · Day 1) · `2` Tổng thể · ngày 2 (Overall · Day 2) · `3` Tổng thể · ngày 3 (Overall · Day 3) · `4` Lượng tuyết · 3 ngày (Snow Amount · Days 1-3) · `5` Tuyết đè nặng · 3 ngày (Snow Load · Days 1-3) · `6` Băng bám · 3 ngày (Ice Accumulation · Days 1-3) · `7` Tuyết thổi bay · 3 ngày (Blowing Snow · Days 1-3)
  Nguồn: NOAA WPC

**`wpc_snow`** — Xác suất tuyết dày / băng bám · chip `SNOW / ICE ODDS` · chỉ bản mới nhất
  Biến thể: `0` Ngày 1 · tuyết ≥ 4 in (Day 1 · Snow ≥ 4") · `1` Ngày 1 · tuyết ≥ 8 in (Day 1 · Snow ≥ 8") · `2` Ngày 1 · tuyết ≥ 12 in (Day 1 · Snow ≥ 12") · `3` Ngày 1 · băng ≥ 0,25 in (Day 1 · Ice ≥ 0.25") · `4` Ngày 2 · tuyết ≥ 4 in (Day 2 · Snow ≥ 4") · `5` Ngày 2 · tuyết ≥ 8 in (Day 2 · Snow ≥ 8") · `6` Ngày 2 · tuyết ≥ 12 in (Day 2 · Snow ≥ 12") · `7` Ngày 2 · băng ≥ 0,25 in (Day 2 · Ice ≥ 0.25") · `8` Ngày 3 · tuyết ≥ 4 in (Day 3 · Snow ≥ 4") · `9` Ngày 3 · tuyết ≥ 8 in (Day 3 · Snow ≥ 8") · `10` Ngày 3 · tuyết ≥ 12 in (Day 3 · Snow ≥ 12") · `11` Ngày 3 · băng ≥ 0,25 in (Day 3 · Ice ≥ 0.25")
  Nguồn: NOAA WPC

**`wwo`** — Triển vọng thời tiết mùa đông ngày 4–7 · chip `WINTER WEATHER OUTLOOK` · chỉ bản mới nhất
  Biến thể: `0` Ngày 4 (Day 4) · `1` Ngày 5 (Day 5) · `2` Ngày 6 (Day 6) · `3` Ngày 7 (Day 7)
  Nguồn: NOAA WPC

## Bão nhiệt đới (`tropic`)

**`tc_wind`** — Vùng gió bão hiện tại · chip `TROPICAL WINDS` · chỉ bản mới nhất
  Nguồn: NOAA NHC / nowCOAST

**`tc_ww`** — Cảnh báo bão dọc bờ biển · chip `HURRICANE ALERTS` · chỉ bản mới nhất
  Nguồn: NOAA NHC / nowCOAST

**`tc_swath`** — Dải gió bão đã quét qua · chip `WIND SWATH` · chỉ bản mới nhất
  Nguồn: NOAA NHC / nowCOAST

**`surge`** — Ngập do nước dâng (Storm Surge) · chip `STORM SURGE` · chỉ bản mới nhất
  Chỉ có khi NHC ban hành cảnh báo nước dâng.
  Nguồn: NOAA NHC / nowCOAST

**`sst`** — Nhiệt độ mặt nước biển · chip `WATER TEMPERATURE` · chỉ bản mới nhất
  Nước ≥ 26 °C (79 °F) nuôi bão mạnh lên.
  Nguồn: NOAA nowCOAST

**`sst_anom`** — Mặt nước biển ấm/lạnh hơn bình thường · chip `WATER TEMP ANOMALY` · chỉ bản mới nhất
  Nguồn: NOAA CPC

## Triển vọng dài hạn (CPC) (`long`)

**`cpc610`** — Triển vọng 6–10 ngày · chip `6-10 DAY OUTLOOK` · chỉ bản mới nhất
  Biến thể: `0` Nhiệt độ (Temperature) · `1` Lượng mưa (Precipitation)
  Nguồn: NOAA Climate Prediction Center

**`cpc814`** — Triển vọng 8–14 ngày · chip `8-14 DAY OUTLOOK` · chỉ bản mới nhất
  Biến thể: `0` Nhiệt độ (Temperature) · `1` Lượng mưa (Precipitation)
  Nguồn: NOAA Climate Prediction Center

**`cpch`** — Hiểm họa sắp tới: nóng/lạnh cực đoan, mưa lớn · chip `HAZARDS OUTLOOK` · chỉ bản mới nhất
  Biến thể: `0` 3–7 ngày · nhiệt độ (3-7 Day · Temperature) · `1` 3–7 ngày · mưa (3-7 Day · Precipitation) · `2` 3–7 ngày · cháy rừng/hạn (3-7 Day · Wildfire & Drought) · `3` 8–14 ngày · nhiệt độ (8-14 Day · Temperature) · `4` 8–14 ngày · mưa (8-14 Day · Precipitation) · `5` 8–14 ngày · cháy rừng/hạn (8-14 Day · Wildfire & Drought)
  Nguồn: NOAA Climate Prediction Center

**`drought`** — Triển vọng hạn hán · chip `DROUGHT OUTLOOK` · chỉ bản mới nhất
  Biến thể: `0` Tháng tới (Monthly) · `1` Mùa tới (Seasonal)
  Nguồn: NOAA Climate Prediction Center

## Thủy văn & môi trường (`env`)

**`nwm`** — Sông suối dâng bất thường (National Water Model) · chip `STREAMFLOW` · chỉ bản mới nhất
  Biến thể: `0` Mức bất thường (Anomaly) · `1` Lưu lượng (cfs) (Streamflow (cfs))
  Nguồn: NOAA National Water Model

**`rivfl`** — Triển vọng lũ sông · chip `RIVER FLOOD OUTLOOK` · chỉ bản mới nhất
  Nguồn: NOAA WPC

**`smoke`** — Khói cháy rừng · chip `WILDFIRE SMOKE` · chỉ bản mới nhất
  Biến thể: `0` Sát mặt đất (Near-Surface) · `1` Cả cột khí (trên cao) (Vertically Integrated)
  Nguồn: NOAA NDGD (HRRR-Smoke)

**`aq`** — Chất lượng không khí: PM2.5, ozone, bụi · chip `AIR QUALITY` · chỉ bản mới nhất
  Biến thể: `0` Bụi mịn PM2.5 (1 giờ) (PM2.5) · `1` Ozone (cao nhất 8 giờ) (Ozone 8-Hr Max) · `2` Bụi (dust) (Dust)
  Nguồn: NOAA NDGD

## Hàng không (`avn`)

**`avn_sig`** — SIGMET / G-AIRMET · chip `AVIATION HAZARDS` · chỉ bản mới nhất
  Biến thể: `0` SIGMET (SIGMET) · `1` G-AIRMET (G-AIRMET) · `2` Cảnh báo trung tâm (CWA) (Center Weather Advisory)
  Nguồn: NWS Aviation Weather Center

**`avn_pirep`** — Báo cáo phi công: nhiễu động, đóng băng · chip `PILOT REPORTS` · chỉ bản mới nhất
  Biến thể: `0` Tất cả PIREP (All PIREPs) · `1` Nhiễu động (Turbulence) · `2` Đóng băng (Icing)
  Nguồn: NWS Aviation Weather Center

**`avn_cat`** — Điều kiện bay tại sân bay (VFR/IFR) · chip `FLIGHT CONDITIONS` · chỉ bản mới nhất
  Nguồn: NWS Aviation Weather Center

## Bộ dựng sẵn

- **Giông lốc xoáy**: `spc:0`, `lsr:0`, `lightning:0`, `rad_cref:0` + `radar`
- **Bão tuyết, giá rét**: `rad_ptype:0`, `wssi:0`, `wpc_snow:0`, `chart:3`
- **Bão nhiệt đới**: `sat_ir:0`, `tc_wind:0`, `tc_ww:0`, `surge:0`, `qpf:5` + `radar`
- **Mưa lớn, lũ lụt**: `ero:0`, `qpf:5`, `qpe:3`, `nwm:0`
- **Nắng nóng, cháy rừng**: `ndfd_max:0`, `fire:0`, `smoke:0`
- **Tổng quan toàn quốc**: `sat_ir:0`, `chart:0` + `radar`
- **Dự báo dài hạn**: `cpc610:0`, `cpch:0`
