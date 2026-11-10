// Bộ lớp dữ liệu thời tiết đầy đủ kiểu nhà đài cho bản đồ 3D (MapLibre).
// Mọi nguồn đều là dịch vụ chính thức, miễn phí, không cần API key, có CORS:
//   - NOAA nowCOAST (WMS): vệ tinh GOES, sét, bão nhiệt đới, nước dâng, nhiệt độ mặt biển
//   - NOAA/NCEP MRMS (WMS): radar tổng hợp, loại mưa, đỉnh mây vang
//   - NWS mapservices (ArcGIS): SPC, WPC, CPC, NDFD, RFC, NOHRSC, NWM, chất lượng không khí, hàng không
//   - Iowa Environmental Mesonet: radar vận tốc từng trạm NEXRAD, radar dự báo HRRR
// Cần có sẵn: map (maplibregl.Map), $, esc, store (noaa-common.js).

const AG = 'https://mapservices.weather.noaa.gov/';
const NC = 'https://nowcoast.noaa.gov/geoserver/ows?service=WMS&version=1.3.0';
const OG = l => `https://opengeo.ncep.noaa.gov/geoserver/conus/${l}/ows?service=WMS&version=1.3.0`;
const IEMT = 'https://mesonet.agron.iastate.edu/cache/tile.py/1.0.0/';
const WMS_Q = '&request=GetMap&styles=&format=image/png&transparent=true&width=512&height=512&crs=EPSG:3857&bbox={bbox-epsg-3857}&layers=';

const SV = {
  ndfd: 'raster/rest/services/NDFD/NDFD_temp/MapServer',
  qpe: 'raster/rest/services/obs/rfc_qpe/MapServer',
  snow: 'raster/rest/services/snow/NOHRSC_Snow_Analysis/MapServer',
  ffg: 'raster/rest/services/precip/rfc_gridded_ffg/MapServer',
  wwo: 'raster/rest/services/outlooks/winter_weather_outlook/MapServer',
  sstw: 'raster/rest/services/climate/cpc_wkly_sst/MapServer',
  sfc: 'vector/rest/services/obs/surface_obs/MapServer',
  lsr: 'vector/rest/services/obs/nws_local_storm_reports/MapServer',
  spc: 'vector/rest/services/outlooks/SPC_wx_outlks/MapServer',
  md: 'vector/rest/services/outlooks/spc_mesoscale_discussion/MapServer',
  fire: 'vector/rest/services/fire_weather/SPC_firewx/MapServer',
  ero: 'vector/rest/services/hazards/wpc_precip_hazards/MapServer',
  cpch: 'vector/rest/services/hazards/cpc_weather_hazards/MapServer',
  qpf: 'vector/rest/services/precip/wpc_qpf/MapServer',
  wpcw: 'vector/rest/services/precip/wpc_prob_winter_precip/MapServer',
  wssi: 'vector/rest/services/outlooks/wpc_wssi/MapServer',
  chart: 'vector/rest/services/outlooks/natl_fcst_wx_chart/MapServer',
  c610: 'vector/rest/services/outlooks/cpc_6_10_day_outlk/MapServer',
  c814: 'vector/rest/services/outlooks/cpc_8_14_day_outlk/MapServer',
  drought: 'vector/rest/services/outlooks/cpc_drought_outlk/MapServer',
  rivfl: 'vector/rest/services/outlooks/sig_riv_fld_outlk/MapServer',
  nwm: 'vector/rest/services/obs/NWM_Stream_Analysis/MapServer',
  avn: 'vector/rest/services/aviation/awc_aviation_weather/MapServer'
};
const IS = s => `raster/rest/services/${s}/ImageServer`;

// Các dải giờ dự báo NDFD (nhóm lớp trong dịch vụ NDFD_temp, cách 3 giờ)
const hrs = (first, lab) => [3, 6, 9, 12, 15, 18, 21, 24].map((h, i) => [`${lab} +${h} giờ`, String(first + i * 4)]);

const GROUPS = [
  ['sat', 'Vệ tinh GOES'],
  ['radar', 'Radar & sét'],
  ['obs', 'Quan trắc thực tế'],
  ['fcst', 'Dự báo'],
  ['severe', 'Giông lốc · lũ · cháy rừng'],
  ['winter', 'Mùa đông: tuyết, băng'],
  ['tropic', 'Bão nhiệt đới'],
  ['long', 'Triển vọng dài hạn (CPC)'],
  ['env', 'Thủy văn & môi trường'],
  ['avn', 'Hàng không']
];

// t: wms | ags (ArcGIS MapServer) | agi (ArcGIS ImageServer) | xyz
// v: [nhãn biến thể, giá trị]; op: độ đục mặc định; below: nằm dưới radar (ảnh vệ tinh phủ kín)
const CATALOG = [
  // ---------- Vệ tinh ----------
  { id: 'sat_vis', g: 'sat', name: 'Ảnh mây thật (Visible)', en: 'GOES Visible', t: 'wms', base: NC, v: [['', 'satellite:goes_visible_imagery']], op: 0.85, below: true, noLeg: true, src: 'NOAA nowCOAST / GOES', note: 'Chỉ có ban ngày (sáng sớm miền Tây còn tối).' },
  { id: 'sat_ir', g: 'sat', name: 'Hồng ngoại – đỉnh mây lạnh (IR)', en: 'GOES Longwave IR', t: 'wms', base: NC, v: [['', 'satellite:goes_longwave_imagery']], op: 0.8, below: true, noLeg: true, src: 'NOAA nowCOAST / GOES', note: 'Mây càng sáng/lạnh càng cao, giông càng mạnh. Dùng được cả đêm.' },
  { id: 'sat_wv', g: 'sat', name: 'Hơi nước tầng cao (Water Vapor)', en: 'GOES Water Vapor', t: 'wms', base: NC, v: [['', 'satellite:goes_water_vapor_imagery']], op: 0.8, below: true, noLeg: true, src: 'NOAA nowCOAST / GOES', note: 'Thấy dòng tia, rãnh áp thấp, khí khô.' },
  { id: 'sat_sw', g: 'sat', name: 'Sóng ngắn – sương mù, điểm cháy (Shortwave)', en: 'GOES Shortwave IR', t: 'wms', base: NC, v: [['', 'satellite:goes_shortwave_imagery']], op: 0.8, below: true, noLeg: true, src: 'NOAA nowCOAST / GOES' },
  { id: 'sat_snow', g: 'sat', name: 'Phân biệt tuyết và mây (Snow/Ice)', en: 'GOES Snow/Ice', t: 'wms', base: NC, v: [['', 'satellite:goes_snow_ice_imagery']], op: 0.85, below: true, noLeg: true, src: 'NOAA nowCOAST / GOES' },

  // ---------- Radar ----------
  { id: 'rad_cref', g: 'radar', name: 'Phản hồi tổng hợp (Composite Reflectivity)', en: 'MRMS Composite Reflectivity', t: 'wms', og: 'conus_cref_qcd', v: [['', 'conus_cref_qcd']], op: 0.75, src: 'NOAA/NCEP MRMS', note: 'Cường độ mạnh nhất trên cả cột khí – thấy lõi mưa đá.' },
  { id: 'rad_ptype', g: 'radar', name: 'Loại mưa: mưa / tuyết / băng (Precip Type)', en: 'MRMS Precipitation Type', t: 'wms', og: 'conus_pcpn_typ', v: [['', 'conus_pcpn_typ']], op: 0.8, src: 'NOAA/NCEP MRMS' },
  { id: 'rad_tops', g: 'radar', name: 'Độ cao đỉnh mây vang (Echo Tops)', en: 'MRMS Echo Tops', t: 'wms', og: 'conus_neet_v18', v: [['', 'conus_neet_v18']], op: 0.75, src: 'NOAA/NCEP MRMS', note: 'Đỉnh càng cao, giông càng mạnh.' },
  { id: 'rad_site', g: 'radar', name: 'Radar từng trạm: vận tốc gió (Velocity)', en: 'NEXRAD Level III', t: 'xyz', site: true,
    tpl: IEMT + 'ridge::{site}-{v}-0/{z}/{x}/{y}.png', v: [['Vận tốc (Velocity)', 'N0U'], ['Vận tốc tương đối với ô bão (SRV)', 'N0S'], ['Phản hồi độ phân giải cao (N0B)', 'N0B']], op: 0.85,
    src: 'NWS NEXRAD qua Iowa Environmental Mesonet', note: 'Xanh: gió hướng về radar, đỏ: gió đi ra xa. Xanh – đỏ sát nhau = vòng xoáy (dấu hiệu lốc xoáy).',
    scale: [['#00e0ff', 'về radar'], ['#0a6e0a', ''], ['#7f7f7f', '0'], ['#7a0a0a', ''], ['#ff2a2a', 'ra xa']] },
  { id: 'lightning', g: 'radar', name: 'Mật độ sét (Lightning)', en: 'Lightning Strike Density', t: 'wms', base: NC, v: [['', 'lightning_detection:ldn_lightning_strike_density']], op: 0.9, src: 'NOAA nowCOAST' },

  // ---------- Quan trắc ----------
  { id: 'obs_sfc', g: 'obs', name: 'Bảng số trạm: nhiệt độ, điểm sương, áp suất', en: 'Surface Station Plots', t: 'ags', svc: SV.sfc, v: [['', '0']], op: 1, noLeg: true, src: 'NWS / NOAA', note: 'Đỏ: nhiệt độ (°F) · xanh lá: điểm sương (°F) · xanh dương: áp suất (mb). Phóng to để thấy thêm trạm.' },
  { id: 'obs_wind', g: 'obs', name: 'Gió quan trắc tại sân bay (mũi tên gió)', en: 'METAR Wind Arrows', t: 'ags', svc: SV.avn, v: [['', '12']], op: 1, src: 'NWS / AWC' },
  { id: 'obs_cloud', g: 'obs', name: 'Độ che phủ mây', en: 'Total Cloud Cover', t: 'ags', svc: SV.sfc, v: [['', '100']], op: 1, src: 'NWS / NOAA' },
  { id: 'lsr', g: 'obs', name: 'Báo cáo thiệt hại: lốc, mưa đá, gió, lũ (LSR)', en: 'Local Storm Reports', t: 'ags', svc: SV.lsr, v: [['24 giờ qua', '0'], ['48 giờ qua', '1'], ['72 giờ qua', '2']], op: 1, src: 'NWS Local Storm Reports' },
  { id: 'qpe', g: 'obs', name: 'Lượng mưa đã rơi (Observed Precip)', en: 'RFC QPE', t: 'ags', svc: SV.qpe,
    v: [['1 giờ qua', '5'], ['3 giờ qua', '13'], ['6 giờ qua', '17'], ['24 giờ qua', '25'], ['72 giờ qua', '37'], ['7 ngày qua', '53'], ['30 ngày qua', '65'], ['Từ đầu tháng', '89'], ['% so với bình thường – 30 ngày', '224']], op: 0.75, src: 'NWS River Forecast Centers' },
  { id: 'snow_depth', g: 'obs', name: 'Độ dày tuyết trên mặt đất', en: 'NOHRSC Snow Analysis', t: 'ags', svc: SV.snow, v: [['Độ dày tuyết', '0'], ['Lượng nước trong tuyết (SWE)', '4']], op: 0.75, src: 'NOAA NOHRSC' },
  { id: 'snow_cover', g: 'obs', name: 'Vùng phủ tuyết & băng (1 km)', en: 'IMS Snow & Ice', t: 'agi', svc: IS('obs/usnic_ims_snow_ice_1km'), v: [['', '']], op: 0.6, src: 'U.S. National Ice Center' },

  // ---------- Dự báo ----------
  { id: 'hrrr', g: 'fcst', name: 'Radar dự báo HRRR (Future Radar)', en: 'HRRR Simulated Reflectivity', t: 'xyz', anim: true,
    tpl: IEMT + 'hrrr::REFD-F{v}-0/{z}/{x}/{y}.png', v: Array.from({ length: 18 }, (_, i) => [`+${i + 1} giờ`, String((i + 1) * 60).padStart(4, '0')]), op: 0.8,
    src: 'NOAA HRRR qua Iowa Environmental Mesonet', note: 'Mô phỏng radar từ lượt chạy HRRR mới nhất, tới 18 giờ. Bấm ▶ để chạy.', scale: 'dbz' },
  { id: 'chart', g: 'fcst', name: 'Bản đồ dự báo toàn quốc: front, H/L, vùng mưa', en: 'WPC National Forecast Chart', t: 'ags', svc: SV.chart,
    v: [['Hôm nay – đầy đủ', '1,2,3,4,5,6,7,8,9,10,11'], ['Ngày mai – đầy đủ', '13,14,15,16,17,18,19,20,21,22,23'], ['Ngày kia – đầy đủ', '25,26,27,28,29,30,31,32,33,34,35'], ['Hôm nay – chỉ front & H/L', '1,2'], ['Ngày mai – chỉ front & H/L', '13,14']], op: 0.9, src: 'NOAA WPC' },
  { id: 'ndfd_t', g: 'fcst', name: 'Nhiệt độ dự báo theo giờ', en: 'NDFD Temperature', t: 'ags', svc: SV.ndfd, v: hrs(9, 'Sau'), op: 0.6, src: 'NWS NDFD' },
  { id: 'ndfd_max', g: 'fcst', name: 'Nhiệt độ cao nhất / thấp nhất', en: 'NDFD Max/Min Temperature', t: 'ags', svc: SV.ndfd,
    v: [['Cao nhất hôm nay', '124'], ['Cao nhất ngày mai', '128'], ['Cao nhất ngày kia', '132'], ['Thấp nhất đêm nay', '137'], ['Thấp nhất đêm mai', '141']], op: 0.6, src: 'NWS NDFD' },
  { id: 'ndfd_apt', g: 'fcst', name: 'Nhiệt độ cảm nhận (Heat Index / Wind Chill)', en: 'NDFD Apparent Temperature', t: 'ags', svc: SV.ndfd, v: hrs(50, 'Sau'), op: 0.6, src: 'NWS NDFD' },
  { id: 'ndfd_rh', g: 'fcst', name: 'Độ ẩm tương đối', en: 'NDFD Relative Humidity', t: 'ags', svc: SV.ndfd, v: hrs(91, 'Sau'), op: 0.6, src: 'NWS NDFD' },
  { id: 'qpf', g: 'fcst', name: 'Lượng mưa dự báo (QPF)', en: 'WPC Quantitative Precip Forecast', t: 'ags', svc: SV.qpf,
    v: [['6 giờ tới', '7'], ['Ngày 1', '1'], ['Ngày 2', '2'], ['Ngày 3', '3'], ['Tổng 2 ngày', '8'], ['Tổng 3 ngày', '9'], ['Tổng 5 ngày', '10'], ['Tổng 7 ngày', '11']], op: 0.65, src: 'NOAA WPC' },

  // ---------- Giông lốc, lũ, cháy ----------
  { id: 'spc', g: 'severe', name: 'Nguy cơ giông lốc SPC (Convective Outlook)', en: 'SPC Convective Outlook', t: 'ags', svc: SV.spc,
    v: [['Ngày 1 · 5 cấp nguy cơ', '1'], ['Ngày 1 · xác suất lốc xoáy', '3'], ['Ngày 1 · xác suất mưa đá', '5'], ['Ngày 1 · xác suất gió mạnh', '7'],
      ['Ngày 2 · 5 cấp nguy cơ', '9'], ['Ngày 2 · xác suất lốc xoáy', '11'], ['Ngày 2 · xác suất mưa đá', '13'], ['Ngày 2 · xác suất gió mạnh', '15'],
      ['Ngày 3 · 5 cấp nguy cơ', '17'], ['Ngày 3 · xác suất', '19'], ['Ngày 4', '21'], ['Ngày 5', '22'], ['Ngày 6', '23'], ['Ngày 7', '24'], ['Ngày 8', '25']], op: 0.55, src: 'NOAA Storm Prediction Center',
    note: 'TSTM giông thường · MRGL 1 · SLGT 2 · ENH 3 · MDT 4 · HIGH 5.' },
  { id: 'spc_md', g: 'severe', name: 'Thảo luận khẩn SPC (Mesoscale Discussion)', en: 'SPC Mesoscale Discussions', t: 'ags', svc: SV.md, v: [['', '0']], op: 0.9, src: 'NOAA Storm Prediction Center', note: 'Vùng SPC đang theo dõi, thường sắp ra Watch.' },
  { id: 'ero', g: 'severe', name: 'Nguy cơ mưa lớn gây lũ quét (ERO)', en: 'WPC Excessive Rainfall Outlook', t: 'ags', svc: SV.ero, v: [['Ngày 1', '0'], ['Ngày 2', '1'], ['Ngày 3', '2'], ['Ngày 4', '3'], ['Ngày 5', '4']], op: 0.55, src: 'NOAA WPC' },
  { id: 'ffg', g: 'severe', name: 'Ngưỡng mưa gây lũ quét (Flash Flood Guidance)', en: 'RFC Flash Flood Guidance', t: 'ags', svc: SV.ffg, v: [['Trong 1 giờ', '0'], ['Trong 3 giờ', '4'], ['Trong 6 giờ', '8'], ['Trong 12 giờ', '12'], ['Trong 24 giờ', '16']], op: 0.6, src: 'NWS River Forecast Centers', note: 'Lượng mưa (inch) đủ để gây lũ quét. Càng thấp càng dễ lũ.' },
  { id: 'fire', g: 'severe', name: 'Nguy cơ cháy rừng SPC', en: 'SPC Fire Weather Outlook', t: 'ags', svc: SV.fire,
    v: [['Ngày 1 · gió & khô', '1'], ['Ngày 1 · giông khô', '2'], ['Ngày 2 · gió & khô', '4'], ['Ngày 2 · giông khô', '5'], ['Ngày 3–8 · gió & khô', '8,11,14,17,20,23']], op: 0.6, src: 'NOAA Storm Prediction Center' },

  // ---------- Mùa đông ----------
  { id: 'wssi', g: 'winter', name: 'Mức tác động bão tuyết (WSSI)', en: 'WPC Winter Storm Severity Index', t: 'ags', svc: SV.wssi,
    v: [['Tổng thể · 3 ngày', '4'], ['Tổng thể · ngày 1', '1'], ['Tổng thể · ngày 2', '2'], ['Tổng thể · ngày 3', '3'], ['Lượng tuyết · 3 ngày', '9'], ['Tuyết đè nặng · 3 ngày', '14'], ['Băng bám · 3 ngày', '19'], ['Tuyết thổi bay · 3 ngày', '27']], op: 0.6, src: 'NOAA WPC' },
  { id: 'wpc_snow', g: 'winter', name: 'Xác suất tuyết dày / băng bám', en: 'WPC Winter Precip Probabilities', t: 'ags', svc: SV.wpcw,
    v: [['Ngày 1 · tuyết ≥ 4 in', '1'], ['Ngày 1 · tuyết ≥ 8 in', '2'], ['Ngày 1 · tuyết ≥ 12 in', '3'], ['Ngày 1 · băng ≥ 0,25 in', '4'],
      ['Ngày 2 · tuyết ≥ 4 in', '6'], ['Ngày 2 · tuyết ≥ 8 in', '7'], ['Ngày 2 · tuyết ≥ 12 in', '8'], ['Ngày 2 · băng ≥ 0,25 in', '9'],
      ['Ngày 3 · tuyết ≥ 4 in', '11'], ['Ngày 3 · tuyết ≥ 8 in', '12'], ['Ngày 3 · tuyết ≥ 12 in', '13'], ['Ngày 3 · băng ≥ 0,25 in', '14']], op: 0.6, src: 'NOAA WPC' },
  { id: 'wwo', g: 'winter', name: 'Triển vọng thời tiết mùa đông ngày 4–7', en: 'WPC Winter Weather Outlook', t: 'ags', svc: SV.wwo, v: [['Ngày 4', '0'], ['Ngày 5', '20'], ['Ngày 6', '16'], ['Ngày 7', '24']], op: 0.6, src: 'NOAA WPC' },

  // ---------- Bão nhiệt đới ----------
  { id: 'tc_wind', g: 'tropic', name: 'Vùng gió bão hiện tại', en: 'NHC Current Wind Extent', t: 'wms', base: NC, v: [['', 'tropical_cyclones:tropical_cyclone_current_wind_extent']], op: 0.6, src: 'NOAA NHC / nowCOAST' },
  { id: 'tc_ww', g: 'tropic', name: 'Cảnh báo bão dọc bờ biển', en: 'NHC Coastal Watches/Warnings', t: 'wms', base: NC, v: [['', 'tropical_cyclones:tropical_cyclone_watches_warnings']], op: 1, src: 'NOAA NHC / nowCOAST' },
  { id: 'tc_swath', g: 'tropic', name: 'Dải gió bão đã quét qua', en: 'NHC Observed Wind Swath', t: 'wms', base: NC, v: [['', 'tropical_cyclones:tropical_cyclone_observed_wind_extent']], op: 0.55, src: 'NOAA NHC / nowCOAST' },
  { id: 'surge', g: 'tropic', name: 'Ngập do nước dâng (Storm Surge)', en: 'NHC Potential Storm Surge Flooding', t: 'wms', base: NC, v: [['', 'tropical_storm_surge:inundation']], op: 0.8, src: 'NOAA NHC / nowCOAST', note: 'Chỉ có khi NHC ban hành cảnh báo nước dâng.' },
  { id: 'sst', g: 'tropic', name: 'Nhiệt độ mặt nước biển', en: 'Sea Surface Temperature', t: 'wms', base: NC, v: [['', 'sea_surface_temperature:global_sea_surface_temperature']], op: 0.7, src: 'NOAA nowCOAST', note: 'Nước ≥ 26 °C (79 °F) nuôi bão mạnh lên.' },
  { id: 'sst_anom', g: 'tropic', name: 'Mặt nước biển ấm/lạnh hơn bình thường', en: 'CPC Weekly SST Anomaly', t: 'ags', svc: SV.sstw, v: [['', '4']], op: 0.65, src: 'NOAA CPC' },

  // ---------- Dài hạn ----------
  { id: 'cpc610', g: 'long', name: 'Triển vọng 6–10 ngày', en: 'CPC 6–10 Day Outlook', t: 'ags', svc: SV.c610, v: [['Nhiệt độ', '0'], ['Lượng mưa', '1']], op: 0.6, src: 'NOAA Climate Prediction Center' },
  { id: 'cpc814', g: 'long', name: 'Triển vọng 8–14 ngày', en: 'CPC 8–14 Day Outlook', t: 'ags', svc: SV.c814, v: [['Nhiệt độ', '0'], ['Lượng mưa', '1']], op: 0.6, src: 'NOAA Climate Prediction Center' },
  { id: 'cpch', g: 'long', name: 'Hiểm họa sắp tới: nóng/lạnh cực đoan, mưa lớn', en: 'CPC Hazards Outlook', t: 'ags', svc: SV.cpch,
    v: [['3–7 ngày · nhiệt độ', '1'], ['3–7 ngày · mưa', '4'], ['3–7 ngày · cháy rừng/hạn', '7'], ['8–14 ngày · nhiệt độ', '3'], ['8–14 ngày · mưa', '6'], ['8–14 ngày · cháy rừng/hạn', '8']], op: 0.6, src: 'NOAA Climate Prediction Center' },
  { id: 'drought', g: 'long', name: 'Triển vọng hạn hán', en: 'CPC Drought Outlook', t: 'ags', svc: SV.drought, v: [['Tháng tới', '1'], ['Mùa tới', '4']], op: 0.6, src: 'NOAA Climate Prediction Center' },

  // ---------- Thủy văn & môi trường ----------
  { id: 'nwm', g: 'env', name: 'Sông suối dâng bất thường (National Water Model)', en: 'NWM Streamflow Anomaly', t: 'ags', svc: SV.nwm, v: [['Mức bất thường', '14'], ['Lưu lượng (cfs)', '0']], op: 0.9, src: 'NOAA National Water Model' },
  { id: 'rivfl', g: 'env', name: 'Triển vọng lũ sông', en: 'Significant River Flood Outlook', t: 'ags', svc: SV.rivfl, v: [['', '0']], op: 0.6, src: 'NOAA WPC' },
  { id: 'smoke', g: 'env', name: 'Khói cháy rừng', en: 'NDGD Smoke', t: 'agi', svcs: [['Sát mặt đất', IS('air_quality/ndgd_smoke_sfc_1hr_avg_time')], ['Cả cột khí (trên cao)', IS('air_quality/ndgd_smoke_vert_1hr_avg_time')]], op: 0.7, src: 'NOAA NDGD (HRRR-Smoke)' },
  { id: 'aq', g: 'env', name: 'Chất lượng không khí: PM2.5, ozone, bụi', en: 'NDGD Air Quality', t: 'agi', svcs: [['Bụi mịn PM2.5 (1 giờ)', IS('air_quality/ndgd_apm25_hr01')], ['Ozone (cao nhất 8 giờ)', IS('air_quality/ndgd_ozone_8hr_max_time')], ['Bụi (dust)', IS('air_quality/ndgd_dust_sfc_time')]], op: 0.6, src: 'NOAA NDGD' },

  // ---------- Hàng không ----------
  { id: 'avn_sig', g: 'avn', name: 'SIGMET / G-AIRMET', en: 'AWC SIGMET & G-AIRMET', t: 'ags', svc: SV.avn, v: [['SIGMET', '111'], ['G-AIRMET', '110'], ['Cảnh báo trung tâm (CWA)', '113']], op: 0.7, src: 'NWS Aviation Weather Center' },
  { id: 'avn_pirep', g: 'avn', name: 'Báo cáo phi công: nhiễu động, đóng băng', en: 'Pilot Reports', t: 'ags', svc: SV.avn, v: [['Tất cả PIREP', '0'], ['Nhiễu động', '1'], ['Đóng băng', '3']], op: 1, src: 'NWS Aviation Weather Center' },
  { id: 'avn_cat', g: 'avn', name: 'Điều kiện bay tại sân bay (VFR/IFR)', en: 'METAR Flight Category', t: 'ags', svc: SV.avn, v: [['', '34']], op: 1, src: 'NWS Aviation Weather Center' }
];
CATALOG.forEach(e => { if (e.svcs) e.v = e.svcs; });
const BYID = Object.fromEntries(CATALOG.map(e => [e.id, e]));

// Bộ lớp dựng sẵn cho từng loại bản tin
const PRESETS = [
  ['Giông lốc xoáy', { spc: 0, lsr: 0, lightning: 0, rad_cref: 0 }, { radar: 'now' }],
  ['Bão tuyết, giá rét', { rad_ptype: 0, wssi: 0, wpc_snow: 0, chart: 3 }, {}],
  ['Bão nhiệt đới', { sat_ir: 0, tc_wind: 0, tc_ww: 0, surge: 0, qpf: 5 }, { radar: 'now' }],
  ['Mưa lớn, lũ lụt', { ero: 0, qpf: 5, qpe: 3, nwm: 0 }, {}],
  ['Nắng nóng, cháy rừng', { ndfd_max: 0, fire: 0, smoke: 0 }, {}],
  ['Tổng quan toàn quốc', { sat_ir: 0, chart: 0 }, { radar: 'now' }],
  ['Dự báo dài hạn', { cpc610: 0, cpch: 0 }, {}]
];

// ---------------- URL ô ảnh ----------------
// Ảnh WMS/ArcGIS lấy ô 512 px: ít lượt gọi hơn 4 lần (máy chủ NWS dễ trả 504 khi bị gọi dồn); ô XYZ của IEM là 256 px
const tileSize = e => e.t === 'xyz' ? 256 : 512;
// Dịch vụ raster của NWS: mỗi nhóm gồm Boundary (+1), Footprint (+2), Image (+3) → chỉ lấy ảnh, bỏ khung viền
const agsIds = (e, ids) => e.svc?.startsWith('raster/') ? ids.split(',').map(x => +x + 3).join(',') : ids;
const agsLayers = ids => 'show:' + ids;
function tileUrl(e, vi) {
  const val = e.v[vi][1];
  if (e.t === 'wms') return (e.og ? OG(e.og) : e.base) + WMS_Q + val;
  if (e.t === 'ags') return `${AG}${e.svc}/export?bbox={bbox-epsg-3857}&bboxSR=3857&imageSR=3857&size=512,512&dpi=96&format=png32&transparent=true&layers=${agsLayers(agsIds(e, val))}&f=image`;
  if (e.t === 'agi') return `${AG}${e.svcs ? val : e.svc}/exportImage?bbox={bbox-epsg-3857}&bboxSR=3857&imageSR=3857&size=512,512&format=png&transparent=true&f=image`;
  return e.tpl.replace('{v}', val).replace('{site}', radarSite || 'TLX');
}

// ---------------- Trạng thái ----------------
// active: id -> { vi: chỉ số biến thể, op: độ đục }
const active = new Map();
function saveLayers() {
  store.set('map3dLayers', Object.fromEntries([...active].map(([id, s]) => [id, [s.vi, s.op]])));
  const u = new URL(location.href);
  if (active.size) u.searchParams.set('lop', [...active].map(([id, s]) => `${id}.${s.vi}`).join(','));
  else u.searchParams.delete('lop');
  history.replaceState(null, '', u);
}

const beforeId = e => e.below ? (map.getLayer('radar-conus') ? 'radar-conus' : 'alerts-line') : 'alerts-line';
function addMapLayer(e, s) {
  const id = 'ov-' + e.id;
  removeMapLayer(e);
  map.addSource(id, { type: 'raster', tiles: [tileUrl(e, s.vi)], tileSize: tileSize(e), attribution: e.src });
  map.addLayer({ id, type: 'raster', source: id, paint: { 'raster-opacity': s.op, 'raster-fade-duration': 150 } }, beforeId(e));
}
function removeMapLayer(e) {
  const id = 'ov-' + e.id;
  if (map.getLayer(id)) map.removeLayer(id);
  if (map.getSource(id)) map.removeSource(id);
  stopAnim(e.id);
}

function setLayer(id, on, vi, op) {
  const e = BYID[id]; if (!e) return;
  if (!on) { active.delete(id); removeMapLayer(e); }
  else {
    const s = active.get(id) || { vi: 0, op: e.op };
    if (vi != null && e.v[vi]) s.vi = vi;
    if (op != null) s.op = op;
    active.set(id, s);
    openGroups.add(e.g);
    addMapLayer(e, s);
    if (e.site) ensureSites();
  }
  saveLayers(); renderPanel(); renderLayerLegend();
}
function setVariant(id, vi) {
  const e = BYID[id], s = active.get(id); if (!s) return;
  stopAnim(id);
  s.vi = vi;
  map.getSource('ov-' + id)?.setTiles([tileUrl(e, vi)]);
  saveLayers(); renderLayerLegend(); updateAnimBar();
}
function setOpacity(id, op) {
  const s = active.get(id); if (!s) return;
  s.op = op;
  if (map.getLayer('ov-' + id)) map.setPaintProperty('ov-' + id, 'raster-opacity', op);
  const a = anims.get(id), fid = a && `ov-${id}-f${a.i}`;
  if (fid && map.getLayer(fid)) map.setPaintProperty(fid, 'raster-opacity', op);
  saveLayers();
}
function clearAll() { [...active.keys()].forEach(id => { active.delete(id); removeMapLayer(BYID[id]); }); saveLayers(); renderPanel(); renderLayerLegend(); }
function applyPreset(i) {
  const [, set, extra] = PRESETS[i];
  clearAll();
  Object.entries(set).forEach(([id, vi]) => { const e = BYID[id]; active.set(id, { vi, op: e.op }); openGroups.add(e.g); addMapLayer(e, active.get(id)); });
  if (extra.radar && typeof setRadarMode === 'function' && $('radarMode').value === 'off') { $('radarMode').value = extra.radar; setRadarMode(extra.radar); }
  saveLayers(); renderPanel(); renderLayerLegend();
}

// ---------------- Radar từng trạm: chọn trạm gần tâm bản đồ ----------------
let radarSite = null, radarSiteAuto = true, sites = null;
async function ensureSites() {
  if (sites) return pickSite();
  try {
    const j = await (await fetch('https://mesonet.agron.iastate.edu/geojson/network/NEXRAD.geojson')).json();
    sites = j.features.filter(f => /^[A-Z]{3}$/.test(f.id)).map(f => ({ id: f.id, name: f.properties.sname, st: f.properties.state, lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] }))
      .sort((a, b) => (a.st + a.name).localeCompare(b.st + b.name));
  } catch { sites = []; }
  renderPanel();
  pickSite();
}
function pickSite() {
  if (!sites?.length || !radarSiteAuto) return;
  const c = map.getCenter();
  let best = null, bd = 1e9;
  for (const s of sites) { const d = (s.lon - c.lng) ** 2 * Math.cos(c.lat * Math.PI / 180) ** 2 + (s.lat - c.lat) ** 2; if (d < bd) { bd = d; best = s; } }
  if (best && best.id !== radarSite) { radarSite = best.id; refreshSite(); }
}
function refreshSite() {
  const s = active.get('rad_site'); if (s) map.getSource('ov-rad_site')?.setTiles([tileUrl(BYID.rad_site, s.vi)]);
  const el = document.querySelector('#lyrList [data-site]'); if (el) el.value = radarSiteAuto ? '' : radarSite;
  const lab = document.querySelector('#lyrList .sitelab'); if (lab) lab.textContent = siteLabel();
  renderLayerLegend();
}
const siteLabel = () => { const s = sites?.find(x => x.id === radarSite); return s ? `Trạm K${s.id} · ${s.name}, ${s.st}` : ''; };

// ---------------- Chạy hình (HRRR) ----------------
const anims = new Map();
function startAnim(id) {
  const e = BYID[id], s = active.get(id); if (!e || !s) return;
  stopAnim(id);
  const frames = e.v.map((_, i) => i);
  frames.forEach(i => {
    const fid = `ov-${id}-f${i}`;
    map.addSource(fid, { type: 'raster', tiles: [tileUrl(e, i)], tileSize: tileSize(e) });
    map.addLayer({ id: fid, type: 'raster', source: fid, paint: { 'raster-opacity': 0, 'raster-opacity-transition': { duration: 0 }, 'raster-fade-duration': 0 } }, beforeId(e));
  });
  if (map.getLayer('ov-' + id)) map.setLayoutProperty('ov-' + id, 'visibility', 'none');
  const a = { frames, i: s.vi, hold: 0, timer: null };
  anims.set(id, a);
  const show = i => {
    frames.forEach(j => map.getLayer(`ov-${id}-f${j}`) && map.setPaintProperty(`ov-${id}-f${j}`, 'raster-opacity', j === i ? s.op : 0));
    a.i = i; s.vi = i; updateAnimBar();
    const sel = document.querySelector(`#lyrList [data-id="${id}"] select[data-act="v"]`); if (sel) sel.value = i;
  };
  show(a.i);
  a.timer = setInterval(() => { if (a.i === frames.length - 1 && a.hold++ < 2) return; a.hold = 0; show((a.i + 1) % frames.length); }, 900);
  renderPanel();
}
function stopAnim(id) {
  const a = anims.get(id); if (!a) return;
  clearInterval(a.timer);
  a.frames.forEach(i => { const fid = `ov-${id}-f${i}`; if (map.getLayer(fid)) map.removeLayer(fid); if (map.getSource(fid)) map.removeSource(fid); });
  anims.delete(id);
  const s = active.get(id);
  if (s && map.getLayer('ov-' + id)) { map.getSource('ov-' + id).setTiles([tileUrl(BYID[id], s.vi)]); map.setLayoutProperty('ov-' + id, 'visibility', 'visible'); }
  updateAnimBar(); renderPanel();
}
// Nhãn giờ dự báo nổi trên bản đồ (hiện cả khi trình chiếu)
function updateAnimBar() {
  const s = active.get('hrrr'), bar = $('abar');
  if (!bar) return;
  bar.hidden = !s;
  if (s) bar.innerHTML = `<span class="lab">Radar dự báo HRRR</span><span class="now">${esc(BYID.hrrr.v[s.vi][0])}</span>`;
}

// ---------------- Chú giải ----------------
const legCache = new Map();
async function agsLegend(svc) {
  if (!legCache.has(svc)) legCache.set(svc, (async () => {
    const [lg, info] = await Promise.all([fetch(AG + svc + '/legend?f=json').then(r => r.json()), svc.endsWith('MapServer') ? fetch(AG + svc + '?f=json').then(r => r.json()) : Promise.resolve({ layers: [] })]);
    const kids = new Map((info.layers || []).map(l => [l.id, l.subLayerIds || []]));
    return { layers: lg.layers || [], kids };
  })().catch(err => { legCache.delete(svc); throw err; }));
  return legCache.get(svc);
}
const swatch = x => `<img alt="" src="data:${x.contentType};base64,${x.imageData}">`;
const shortNum = s => String(s).replace(/(\d+\.\d{2})\d+/g, '$1');
function legendItemsHtml(items, raster) {
  items = items.filter(x => x.imageData && (x.label ?? '') !== '');
  if (!items.length) return '';
  // Bảng màu liên tục (raster nhiều mức): vẽ dải màu, chỉ ghi nhãn đầu – cuối
  if (raster && items.length > 14) return `<div class="lgstrip">${items.map(swatch).join('')}</div><div class="scale-lab"><span>${esc(shortNum(items[0].label))}</span><span>${esc(shortNum(items[items.length - 1].label))}</span></div>`;
  // Nhiều ký hiệu (vd các loại báo cáo thiệt hại): xếp 2 cột
  return `<div class="lgg${items.length > 8 ? ' two' : ''}">${items.map(x => `<div class="lgi">${swatch(x)}<span>${esc(shortNum(x.label))}</span></div>`).join('')}</div>`;
}
async function legendFor(e, vi) {
  const val = e.v[vi][1];
  if (e.noLeg) return '';
  if (e.scale === 'dbz') return `<div class="scale">${['#04e9e7', '#019ff4', '#0300f4', '#02fd02', '#01c501', '#008e00', '#fdf802', '#e5bc00', '#fd9500', '#fd0000', '#d40000', '#bc0000', '#f800fd', '#9854c6'].map(c => `<i style="background:${c}"></i>`).join('')}</div><div class="scale-lab"><span>mưa nhẹ</span><span>giông mạnh, mưa đá</span></div>`;
  if (Array.isArray(e.scale)) return `<div class="scale">${e.scale.map(([c]) => `<i style="background:${c}"></i>`).join('')}</div><div class="scale-lab">${e.scale.filter(x => x[1]).map(x => `<span>${esc(x[1])}</span>`).join('')}</div>`;
  if (e.t === 'wms') {
    const url = (e.og ? OG(e.og) : e.base) + '&request=GetLegendGraphic&format=image/png&layer=' + encodeURIComponent(val);
    return `<img class="lgwms" alt="" src="${esc(url)}" onerror="this.remove()">`;
  }
  if (e.t === 'ags' || e.t === 'agi') {
    const svc = e.t === 'agi' && e.svcs ? val : e.svc;
    const { layers, kids } = await agsLegend(svc);
    if (e.t === 'agi') return legendItemsHtml(layers.flatMap(l => l.legend), true);
    const want = new Set(), walk = id => { want.add(id); (kids.get(id) || []).forEach(walk); };
    agsIds(e, val).split(',').forEach(x => walk(+x));
    const parts = layers.filter(l => want.has(l.layerId)).map(l => ({ name: l.layerName, html: legendItemsHtml(l.legend, /raster|image/i.test(l.layerType || '')) })).filter(p => p.html);
    // Nhiều lớp con có cùng chú giải (vd bản đồ toàn quốc): bỏ trùng
    const seen = new Set();
    return parts.filter(p => !seen.has(p.html) && seen.add(p.html)).map(p => (parts.length > 1 && !/^Image$/i.test(p.name) ? `<div class="lgsub">${esc(p.name.replace(/_/g, ' '))}</div>` : '') + p.html).join('');
  }
  return '';
}
let legGen = 0;
async function renderLayerLegend() {
  const box = $('legendLayers'); if (!box) return;
  const my = ++legGen, list = [...active].map(([id, s]) => [BYID[id], s]);
  if (!list.length) { box.innerHTML = ''; return; }
  box.innerHTML = list.map(([e, s]) => `<div class="lgblk" data-lg="${e.id}"><h3 class="sec">${esc(e.name)}</h3><div class="lgv">${esc([e.v[s.vi][0], e.site ? siteLabel() : ''].filter(Boolean).join(' · '))}</div><div class="lgc"><p class="note">Đang tải chú giải…</p></div>${e.note ? `<p class="note">${esc(e.note)}</p>` : ''}<p class="note src">Nguồn: ${esc(e.src)}</p></div>`).join('');
  for (const [e, s] of list) {
    let html = '';
    try { html = await legendFor(e, s.vi); } catch { html = ''; }
    if (my !== legGen) return;
    const c = box.querySelector(`[data-lg="${e.id}"] .lgc`);
    if (c) c.innerHTML = html || (e.noLeg ? '' : '<p class="note">Không có chú giải hoặc hiện không có dữ liệu.</p>');
  }
}

// ---------------- Bảng điều khiển ----------------
let filterText = '';
// Nhóm đang mở: người dùng tự mở/đóng; bật một lớp (kể cả qua bộ dựng sẵn) thì mở nhóm của nó
const openGroups = new Set();
function renderPanel() {
  const box = $('lyrList'); if (!box) return;
  const q = filterText.trim().toLowerCase();
  box.innerHTML = GROUPS.map(([g, gname]) => {
    const items = CATALOG.filter(e => e.g === g && (!q || (e.name + ' ' + e.en).toLowerCase().includes(q)));
    if (!items.length) return '';
    const n = items.filter(e => active.has(e.id)).length;
    const open = q || openGroups.has(g);
    return `<details data-g="${g}"${open ? ' open' : ''}><summary>${esc(gname)} <span class="cnt">${n ? n + ' bật · ' : ''}${items.length}</span></summary>${items.map(e => {
      const s = active.get(e.id), on = !!s;
      return `<div class="lr${on ? ' on' : ''}" data-id="${e.id}">
        <label class="lname"><input type="checkbox" data-act="on"${on ? ' checked' : ''}><span>${esc(e.name)}<small>${esc(e.en)}</small></span></label>
        ${on ? `<div class="lctl">
          ${e.v.length > 1 ? `<select data-act="v" aria-label="Chọn biến thể ${esc(e.name)}">${e.v.map(([l], i) => `<option value="${i}"${i === s.vi ? ' selected' : ''}>${esc(l)}</option>`).join('')}</select>` : ''}
          ${e.anim ? `<button type="button" data-act="anim" aria-pressed="${anims.has(e.id)}">${anims.has(e.id) ? '⏸ Dừng' : '▶ Chạy'}</button>` : ''}
          ${e.site ? `<select data-act="site" data-site aria-label="Chọn trạm radar"><option value="">Tự động: trạm gần tâm bản đồ</option>${(sites || []).map(x => `<option value="${x.id}"${!radarSiteAuto && x.id === radarSite ? ' selected' : ''}>${x.st} · K${x.id} ${esc(x.name)}</option>`).join('')}</select><div class="sitelab">${esc(siteLabel())}</div>` : ''}
          <label class="op">Độ đậm <input type="range" data-act="op" min="0.1" max="1" step="0.05" value="${s.op}"></label>
        </div>` : ''}
      </div>`;
    }).join('')}</details>`;
  }).join('') || '<p class="note">Không có lớp nào khớp.</p>';
  $('lyrCount').textContent = active.size ? ` (${active.size})` : '';
}

function initLayerPanel() {
  $('lyrPresets').innerHTML = PRESETS.map(([n], i) => `<button type="button" data-p="${i}">${esc(n)}</button>`).join('') + '<button type="button" data-p="off">Tắt hết</button>';
  $('lyrPresets').onclick = ev => { const b = ev.target.closest('[data-p]'); if (!b) return; b.dataset.p === 'off' ? clearAll() : applyPreset(+b.dataset.p); };
  $('lyrSearch').oninput = ev => { filterText = ev.target.value; renderPanel(); };
  const list = $('lyrList');
  list.addEventListener('toggle', ev => { const d = ev.target; if (d.dataset?.g && !filterText) d.open ? openGroups.add(d.dataset.g) : openGroups.delete(d.dataset.g); }, true);
  list.addEventListener('change', ev => {
    const r = ev.target.closest('[data-id]'); if (!r) return;
    const id = r.dataset.id, act = ev.target.dataset.act;
    if (act === 'on') setLayer(id, ev.target.checked);
    else if (act === 'v') { setVariant(id, +ev.target.value); }
    else if (act === 'site') { radarSiteAuto = !ev.target.value; if (ev.target.value) radarSite = ev.target.value; radarSiteAuto ? pickSite() : refreshSite(); }
  });
  list.addEventListener('input', ev => { if (ev.target.dataset.act === 'op') setOpacity(ev.target.closest('[data-id]').dataset.id, +ev.target.value); });
  list.addEventListener('click', ev => { const b = ev.target.closest('[data-act="anim"]'); if (!b) return; const id = b.closest('[data-id]').dataset.id; anims.has(id) ? stopAnim(id) : startAnim(id); });
  const toggle = open => { $('lyrPanel').hidden = !open; $('lyrBtn').setAttribute('aria-expanded', String(open)); };
  $('lyrBtn').onclick = () => toggle($('lyrPanel').hidden);
  $('lyrClose').onclick = () => toggle(false);
  map.on('moveend', () => { if (active.has('rad_site')) pickSite(); });
  // Làm mới ảnh mỗi 10 phút (dữ liệu NOAA cập nhật liên tục)
  setInterval(() => active.forEach((s, id) => { if (!anims.has(id)) map.getSource('ov-' + id)?.setTiles([tileUrl(BYID[id], s.vi) + '&_t=' + Date.now()]); }), 10 * 60 * 1000);

  // Khôi phục: ưu tiên ?lop=id.biến_thể,... trên đường dẫn (để chia sẻ/trình chiếu), sau đó lần dùng trước
  const fromUrl = new URLSearchParams(location.search).get('lop');
  const saved = fromUrl != null ? Object.fromEntries(fromUrl.split(',').filter(Boolean).map(x => { const [id, vi] = x.split('.'); return [id, [+vi || 0, null]]; })) : (store.get('map3dLayers') || {});
  Object.entries(saved).forEach(([id, [vi, op]]) => { const e = BYID[id]; if (!e) return; active.set(id, { vi: e.v[vi] ? vi : 0, op: op ?? e.op }); openGroups.add(e.g); addMapLayer(e, active.get(id)); if (e.site) ensureSites(); });
  saveLayers(); renderPanel(); renderLayerLegend(); updateAnimBar();
}
