// Phần dùng chung cho bản đồ 2D (map.html) và 3D (map3d.html):
// danh sách bang, tên/màu cảnh báo NWS, tải dữ liệu NWS/METAR, thang màu số liệu.
const NWS = 'https://api.weather.gov';
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const store = {
  get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} }
};
const unit = store.get('unit') || 'F';
const dark = matchMedia('(prefers-color-scheme: dark)').matches;

// ---------- Khu vực: [tên, minLat, minLon, maxLat, maxLon] ----------
const STATES = {
  AL: ['Alabama', 30.1, -88.5, 35.0, -84.9], AK: ['Alaska', 51.2, -179.9, 71.4, -129.9], AZ: ['Arizona', 31.3, -114.8, 37.0, -109.0],
  AR: ['Arkansas', 33.0, -94.6, 36.5, -89.6], CA: ['California', 32.5, -124.4, 42.0, -114.1], CO: ['Colorado', 37.0, -109.1, 41.0, -102.0],
  CT: ['Connecticut', 41.0, -73.7, 42.1, -71.8], DE: ['Delaware', 38.4, -75.8, 39.8, -75.0], DC: ['Washington D.C.', 38.8, -77.1, 39.0, -76.9],
  FL: ['Florida', 24.5, -87.6, 31.0, -80.0], GA: ['Georgia', 30.4, -85.6, 35.0, -80.8], HI: ['Hawaii', 18.9, -160.3, 22.2, -154.8],
  ID: ['Idaho', 42.0, -117.2, 49.0, -111.0], IL: ['Illinois', 37.0, -91.5, 42.5, -87.5], IN: ['Indiana', 37.8, -88.1, 41.8, -84.8],
  IA: ['Iowa', 40.4, -96.6, 43.5, -90.1], KS: ['Kansas', 37.0, -102.1, 40.0, -94.6], KY: ['Kentucky', 36.5, -89.6, 39.1, -81.9],
  LA: ['Louisiana', 28.9, -94.0, 33.0, -88.8], ME: ['Maine', 43.1, -71.1, 47.5, -66.9], MD: ['Maryland', 37.9, -79.5, 39.7, -75.0],
  MA: ['Massachusetts', 41.2, -73.5, 42.9, -69.9], MI: ['Michigan', 41.7, -90.4, 48.3, -82.4], MN: ['Minnesota', 43.5, -97.2, 49.4, -89.5],
  MS: ['Mississippi', 30.2, -91.7, 35.0, -88.1], MO: ['Missouri', 36.0, -95.8, 40.6, -89.1], MT: ['Montana', 44.4, -116.1, 49.0, -104.0],
  NE: ['Nebraska', 40.0, -104.1, 43.0, -95.3], NV: ['Nevada', 35.0, -120.0, 42.0, -114.0], NH: ['New Hampshire', 42.7, -72.6, 45.3, -70.6],
  NJ: ['New Jersey', 38.9, -75.6, 41.4, -73.9], NM: ['New Mexico', 31.3, -109.1, 37.0, -103.0], NY: ['New York', 40.5, -79.8, 45.0, -71.9],
  NC: ['North Carolina', 33.8, -84.3, 36.6, -75.5], ND: ['North Dakota', 45.9, -104.1, 49.0, -96.6], OH: ['Ohio', 38.4, -84.8, 42.0, -80.5],
  OK: ['Oklahoma', 33.6, -103.0, 37.0, -94.4], OR: ['Oregon', 42.0, -124.6, 46.3, -116.5], PA: ['Pennsylvania', 39.7, -80.5, 42.3, -74.7],
  RI: ['Rhode Island', 41.1, -71.9, 42.0, -71.1], SC: ['South Carolina', 32.0, -83.4, 35.2, -78.5], SD: ['South Dakota', 42.5, -104.1, 45.9, -96.4],
  TN: ['Tennessee', 35.0, -90.3, 36.7, -81.6], TX: ['Texas', 25.8, -106.6, 36.5, -93.5], UT: ['Utah', 37.0, -114.1, 42.0, -109.0],
  VT: ['Vermont', 42.7, -73.4, 45.0, -71.5], VA: ['Virginia', 36.5, -83.7, 39.5, -75.2], WA: ['Washington', 45.5, -124.8, 49.0, -116.9],
  WV: ['West Virginia', 37.2, -82.6, 40.6, -77.7], WI: ['Wisconsin', 42.5, -92.9, 47.1, -86.8], WY: ['Wyoming', 41.0, -111.1, 45.0, -104.1],
  PR: ['Puerto Rico', 17.9, -67.3, 18.5, -65.6]
};
// Vị trí đặt huy hiệu số cảnh báo (khi tâm khung bao lệch khỏi bang)
const CENTER_FIX = { FL: [28.4, -81.8], LA: [31.0, -92.3], MI: [44.2, -85.0], AK: [64.0, -152.0], HI: [20.6, -157.0], MD: [39.1, -76.9],
  VA: [37.6, -78.7], NY: [42.9, -75.5], CA: [37.2, -119.5], MA: [42.3, -71.9], ID: [44.2, -114.6], TX: [31.3, -99.3], OK: [35.5, -97.4],
  MN: [46.3, -94.3], KY: [37.5, -85.3], TN: [35.8, -86.3], NC: [35.5, -79.4], WV: [38.6, -80.6], NJ: [40.1, -74.6], NV: [39.3, -116.9] };
const stateCenter = st => CENTER_FIX[st] || [(STATES[st][1] + STATES[st][3]) / 2, (STATES[st][2] + STATES[st][4]) / 2];
const US_BBOX = [17.5, -179.9, 71.5, -64.5];

// ---------- Tên và màu cảnh báo (bảng màu chính thức của NWS) ----------
const EVENTS = {
  'Tornado Warning': ['Cảnh báo lốc xoáy', '#FF0000'],
  'Extreme Wind Warning': ['Cảnh báo gió cực mạnh', '#FF8C00'],
  'Severe Thunderstorm Warning': ['Cảnh báo dông mạnh', '#FFA500'],
  'Flash Flood Warning': ['Cảnh báo lũ quét', '#8B0000'],
  'Flash Flood Emergency': ['Khẩn cấp lũ quét', '#8B0000'],
  'Hurricane Warning': ['Cảnh báo bão cuồng phong', '#DC143C'],
  'Hurricane Watch': ['Theo dõi bão cuồng phong', '#FF00FF'],
  'Tropical Storm Warning': ['Cảnh báo bão nhiệt đới', '#B22222'],
  'Tropical Storm Watch': ['Theo dõi bão nhiệt đới', '#F08080'],
  'Storm Surge Warning': ['Cảnh báo nước dâng do bão', '#B524F7'],
  'Storm Surge Watch': ['Theo dõi nước dâng do bão', '#DB7FF7'],
  'Tornado Watch': ['Theo dõi lốc xoáy', '#FFFF00'],
  'Severe Thunderstorm Watch': ['Theo dõi dông mạnh', '#DB7093'],
  'Flood Warning': ['Cảnh báo lũ', '#00FF00'],
  'Flood Watch': ['Theo dõi lũ', '#2E8B57'],
  'Flood Advisory': ['Khuyến cáo ngập', '#00FF7F'],
  'Flash Flood Watch': ['Theo dõi lũ quét', '#2E8B57'],
  'Coastal Flood Warning': ['Cảnh báo ngập ven biển', '#228B22'],
  'Coastal Flood Advisory': ['Khuyến cáo ngập ven biển', '#7CFC00'],
  'Coastal Flood Watch': ['Theo dõi ngập ven biển', '#66CDAA'],
  'Blizzard Warning': ['Cảnh báo bão tuyết', '#FF4500'],
  'Ice Storm Warning': ['Cảnh báo bão băng', '#8B008B'],
  'Winter Storm Warning': ['Cảnh báo bão mùa đông', '#FF69B4'],
  'Winter Storm Watch': ['Theo dõi bão mùa đông', '#4682B4'],
  'Winter Weather Advisory': ['Khuyến cáo thời tiết mùa đông', '#7B68EE'],
  'Lake Effect Snow Warning': ['Cảnh báo tuyết hiệu ứng hồ', '#008B8B'],
  'Extreme Cold Warning': ['Cảnh báo rét cực đoan', '#0000FF'],
  'Extreme Cold Watch': ['Theo dõi rét cực đoan', '#5F9EA0'],
  'Cold Weather Advisory': ['Khuyến cáo trời lạnh', '#AFEEEE'],
  'Wind Chill Warning': ['Cảnh báo rét do gió', '#B0C4DE'],
  'Wind Chill Advisory': ['Khuyến cáo rét do gió', '#AFEEEE'],
  'Freeze Warning': ['Cảnh báo đóng băng', '#483D8B'],
  'Freeze Watch': ['Theo dõi đóng băng', '#00FFFF'],
  'Frost Advisory': ['Khuyến cáo sương giá', '#6495ED'],
  'Extreme Heat Warning': ['Cảnh báo nắng nóng cực đoan', '#C71585'],
  'Excessive Heat Warning': ['Cảnh báo nắng nóng cực đoan', '#C71585'],
  'Extreme Heat Watch': ['Theo dõi nắng nóng cực đoan', '#800000'],
  'Heat Advisory': ['Khuyến cáo nắng nóng', '#FF7F50'],
  'High Wind Warning': ['Cảnh báo gió mạnh', '#DAA520'],
  'High Wind Watch': ['Theo dõi gió mạnh', '#B8860B'],
  'Wind Advisory': ['Khuyến cáo gió', '#D2B48C'],
  'Red Flag Warning': ['Cảnh báo cháy rừng (cờ đỏ)', '#FF1493'],
  'Fire Weather Watch': ['Theo dõi thời tiết dễ cháy', '#FFDEAD'],
  'Dense Fog Advisory': ['Khuyến cáo sương mù dày', '#708090'],
  'Dense Smoke Advisory': ['Khuyến cáo khói dày', '#F0E68C'],
  'Air Quality Alert': ['Cảnh báo chất lượng không khí', '#808080'],
  'Special Weather Statement': ['Thông báo thời tiết đặc biệt', '#FFE4B5'],
  'Gale Warning': ['Cảnh báo gió giật trên biển', '#DDA0DD'],
  'Storm Warning': ['Cảnh báo bão trên biển', '#9400D3'],
  'Hurricane Force Wind Warning': ['Cảnh báo gió cấp bão trên biển', '#CD5C5C'],
  'Small Craft Advisory': ['Khuyến cáo tàu nhỏ', '#D8BFD8'],
  'Special Marine Warning': ['Cảnh báo hàng hải đặc biệt', '#FFA500'],
  'Marine Weather Statement': ['Thông báo thời tiết biển', '#FFDAB9'],
  'High Surf Warning': ['Cảnh báo sóng lớn', '#228B22'],
  'High Surf Advisory': ['Khuyến cáo sóng lớn', '#BA55D3'],
  'Rip Current Statement': ['Thông báo dòng chảy xa bờ', '#40E0D0'],
  'Beach Hazards Statement': ['Thông báo nguy hiểm bãi biển', '#40E0D0'],
  'Hydrologic Outlook': ['Triển vọng thủy văn', '#90EE90'],
  'Hazardous Weather Outlook': ['Triển vọng thời tiết nguy hiểm', '#EEE8AA'],
  'Avalanche Warning': ['Cảnh báo tuyết lở', '#1E90FF'],
  'Dust Storm Warning': ['Cảnh báo bão bụi', '#FFE4C4'],
  'Blowing Dust Advisory': ['Khuyến cáo bụi bay', '#BDB76B']
};
// Thứ tự ưu tiên: nguy hiểm nhất vẽ trên cùng và đứng đầu danh sách
const PRIORITY = ['Tornado Warning', 'Extreme Wind Warning', 'Flash Flood Emergency', 'Hurricane Warning', 'Storm Surge Warning',
  'Flash Flood Warning', 'Severe Thunderstorm Warning', 'Tropical Storm Warning', 'Special Marine Warning', 'Blizzard Warning',
  'Ice Storm Warning', 'Winter Storm Warning', 'Extreme Heat Warning', 'Excessive Heat Warning', 'Extreme Cold Warning',
  'High Wind Warning', 'Flood Warning', 'Red Flag Warning', 'Tornado Watch', 'Severe Thunderstorm Watch', 'Hurricane Watch',
  'Storm Surge Watch', 'Tropical Storm Watch', 'Flash Flood Watch', 'Flood Watch', 'Winter Storm Watch'];
function rank(event) {
  const i = PRIORITY.indexOf(event);
  if (i >= 0) return i;
  return /Warning|Emergency/.test(event) ? 100 : /Watch/.test(event) ? 200 : /Advisory/.test(event) ? 300 : 400;
}
function eventColor(event) {
  if (EVENTS[event]) return EVENTS[event][1];
  let h = 0; for (const c of event) h = (h * 31 + c.charCodeAt(0)) % 360;
  return `hsl(${h} 55% 55%)`;
}
const eventVi = e => EVENTS[e]?.[0] || e;
const fmtTime = s => s ? new Date(s).toLocaleString('vi-VN', { weekday: 'short', day: 'numeric', month: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';

// ---------- Tải dữ liệu ----------
async function nws(url, tries = 2) {
  for (let i = 0; i < tries; i++) {
    try {
      const r = await fetch(url);
      if (r.ok) return r.json();
      if (r.status === 404 || i === tries - 1) throw new Error('HTTP ' + r.status);
    } catch (e) { if (i === tries - 1) throw e; }
    await new Promise(res => setTimeout(res, 700));
  }
}
// Bộ nhớ đệm hình dạng vùng (IndexedDB) — vùng gần như không đổi, lưu 30 ngày
const zdb = (() => {
  let dbp;
  const open = () => dbp ||= new Promise((res, rej) => {
    const r = indexedDB.open('nws-zones', 1);
    r.onupgradeneeded = () => r.result.createObjectStore('z');
    r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
  });
  return {
    async get(k) { try { const db = await open(); return await new Promise(res => { const q = db.transaction('z').objectStore('z').get(k); q.onsuccess = () => res(q.result); q.onerror = () => res(undefined); }); } catch { return undefined; } },
    async set(k, v) { try { const db = await open(); db.transaction('z', 'readwrite').objectStore('z').put(v, k); } catch {} }
  };
})();
const zoneMem = new Map();
function getZone(url) {
  if (!zoneMem.has(url)) zoneMem.set(url, (async () => {
    const hit = await zdb.get(url);
    if (hit && Date.now() - hit.t < 30 * 864e5) return hit.g;
    const z = await nws(url, 2);
    if (z.geometry) zdb.set(url, { g: z.geometry, t: Date.now() });
    return z.geometry;
  })().catch(() => { zoneMem.delete(url); return null; }));
  return zoneMem.get(url);
}
// Chạy nhiều việc cùng lúc nhưng giới hạn số lượng để không quá tải NWS
async function pool(items, n, fn) {
  let i = 0;
  await Promise.all(Array.from({ length: Math.min(n, items.length) }, async () => { while (i < items.length) await fn(items[i++]); }));
}

// ---------- Số liệu quan trắc (METAR) ----------
const US_ID = /^(K|PA|PH|PG|TJ|TI)/;
const num = v => (v === null || v === undefined || v === '' || isNaN(+v)) ? null : +v;
function fromAWC(o) {
  const alt = num(o.altim);
  return {
    id: o.icaoId, name: o.name || '', lat: +o.lat, lon: +o.lon, t: num(o.temp), td: num(o.dewp),
    wdir: o.wdir === 'VRB' ? null : num(o.wdir), wspd: num(o.wspd), wgst: num(o.wgst),
    vis: o.visib == null ? null : parseFloat(String(o.visib).replace('+', '')),
    altim: alt == null ? null : alt > 100 ? alt / 33.8639 : alt,
    wx: o.wxString || '', raw: o.rawOb || '', time: (o.obsTime || 0) * 1000, cat: o.fltCat || ''
  };
}
// Lấy quan trắc METAR trong khung bao [minLat, minLon, maxLat, maxLon]: thử AWC trực tiếp, lỗi thì dùng bản sao.
// Trả về { list (mới nhất mỗi trạm Mỹ, ≤ 3 giờ), source }.
async function fetchObs(bb) {
  let list = null, source = '';
  try {
    const r = await fetch(`https://aviationweather.gov/api/data/metar?bbox=${bb.map(v => v.toFixed(2)).join(',')}&format=json&hours=2`);
    if (!r.ok) throw new Error(r.status);
    list = (await r.json()).map(fromAWC); source = 'AWC trực tiếp';
  } catch {
    try {
      const d = await (await fetch('data/metars-us.json?t=' + Math.floor(Date.now() / 300000))).json();
      list = d.obs.filter(o => o.lat >= bb[0] && o.lat <= bb[2] && o.lon >= bb[1] && o.lon <= bb[3]);
      source = 'bản sao lúc ' + new Date(d.fetchedAt).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    } catch { list = []; }
  }
  const latest = new Map();
  list.filter(o => o.id && US_ID.test(o.id) && isFinite(o.lat) && Date.now() - o.time < 3 * 3600e3)
    .forEach(o => { const p = latest.get(o.id); if (!p || o.time > p.time) latest.set(o.id, o); });
  return { list: [...latest.values()], source };
}
const regionBBox = (region, pad = 0.3) => {
  if (region === 'US') return US_BBOX;
  const b = STATES[region].slice(1);
  return [b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad];
};

// Đơn vị và thang màu cho từng loại số liệu
const toF = c => c * 9 / 5 + 32;
const METRICS = {
  t:     { name: 'Nhiệt độ', get: o => o.t == null ? null : unit === 'F' ? toF(o.t) : o.t, fmt: v => Math.round(v) + '°', unit: '°' + unit,
           stops: unit === 'F' ? [[-10, '#9e3fbf'], [10, '#5b5be0'], [32, '#3d9bff'], [50, '#33c3c3'], [65, '#5cc94e'], [75, '#e8d43a'], [85, '#f39a2b'], [95, '#e8432e'], [105, '#a8162b']]
                                : [[-23, '#9e3fbf'], [-12, '#5b5be0'], [0, '#3d9bff'], [10, '#33c3c3'], [18, '#5cc94e'], [24, '#e8d43a'], [29, '#f39a2b'], [35, '#e8432e'], [40, '#a8162b']] },
  td:    { name: 'Điểm sương', get: o => o.td == null ? null : unit === 'F' ? toF(o.td) : o.td, fmt: v => Math.round(v) + '°', unit: '°' + unit,
           stops: unit === 'F' ? [[0, '#8d6e4a'], [30, '#c9a46b'], [45, '#d8d8a0'], [55, '#7fd17f'], [65, '#2fa84f'], [72, '#167a8a'], [78, '#3b3bb3']]
                                : [[-18, '#8d6e4a'], [-1, '#c9a46b'], [7, '#d8d8a0'], [13, '#7fd17f'], [18, '#2fa84f'], [22, '#167a8a'], [26, '#3b3bb3']] },
  wspd:  { name: 'Gió', get: o => o.wspd == null ? null : o.wspd * 1.15078, fmt: v => Math.round(v), unit: 'mph',
           stops: [[0, '#dfe7ef'], [10, '#9fd3f5'], [20, '#5cc94e'], [30, '#e8d43a'], [40, '#f39a2b'], [50, '#e8432e'], [70, '#9e3fbf']] },
  wgst:  { name: 'Gió giật', get: o => o.wgst == null ? null : o.wgst * 1.15078, fmt: v => Math.round(v), unit: 'mph',
           stops: [[15, '#9fd3f5'], [25, '#5cc94e'], [35, '#e8d43a'], [45, '#f39a2b'], [58, '#e8432e'], [75, '#9e3fbf']] },
  vis:   { name: 'Tầm nhìn', get: o => o.vis, fmt: v => v >= 10 ? '10+' : v < 1 ? v.toFixed(2).replace(/0$/, '') : v.toFixed(1).replace('.0', ''), unit: 'dặm',
           stops: [[0, '#9e3fbf'], [1, '#e8432e'], [3, '#f39a2b'], [5, '#e8d43a'], [10, '#5cc94e']] },
  altim: { name: 'Áp suất', get: o => o.altim, fmt: v => v.toFixed(2), unit: 'inHg',
           stops: [[29.2, '#9e3fbf'], [29.5, '#e8432e'], [29.8, '#e8d43a'], [30.0, '#5cc94e'], [30.2, '#33c3c3'], [30.5, '#3d6bff']] }
};
function colorAt(stops, v) {
  if (v <= stops[0][0]) return stops[0][1];
  for (let i = 1; i < stops.length; i++) if (v <= stops[i][0]) {
    const [v0, c0] = stops[i - 1], [v1, c1] = stops[i], k = (v - v0) / (v1 - v0);
    const h = c => [1, 3, 5].map(j => parseInt(c.slice(j, j + 2), 16));
    const a = h(c0), b = h(c1);
    return '#' + a.map((x, j) => Math.round(x + (b[j] - x) * k).toString(16).padStart(2, '0')).join('');
  }
  return stops[stops.length - 1][1];
}
const textOn = hex => { const [r, g, b] = [1, 3, 5].map(j => parseInt(hex.slice(j, j + 2), 16)); return (r * 299 + g * 587 + b * 114) / 1000 > 140 ? '#111' : '#fff'; };
