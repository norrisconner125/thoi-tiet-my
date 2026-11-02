// Service worker: cho phép cài app và mở được khi mất mạng (hiện dữ liệu lần tải gần nhất).
const VERSION = 'v3';
const SHELL = [
  './', './index.html', './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png', './icons/favicon.png',
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css'
];
self.addEventListener('install', e => {
  // Lưu từng file riêng: một file lỗi (vd CDN chậm) không làm hỏng cả bước cài
  e.waitUntil(caches.open('shell-' + VERSION)
    .then(c => Promise.all(SHELL.map(u => c.add(u).catch(() => console.warn('Không lưu được', u)))))
    .then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(k => !k.endsWith(VERSION)).map(k => caches.delete(k))
  )).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // Ảnh nền bản đồ và radar: không lưu (quá nhiều, nhanh cũ)
  if (/cartocdn|opengeo\.ncep|radar\.weather/.test(url.host)) return;
  // Dữ liệu thời tiết: luôn lấy mới, mất mạng thì dùng bản đã lưu
  if (/api\.weather\.gov|nhc\.noaa\.gov|open-meteo/.test(url.host) || url.pathname.includes('/data/')) {
    e.respondWith(fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open('data-' + VERSION).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req)));
    return;
  }
  // Giao diện app: dùng bản lưu ngay, cập nhật ngầm
  e.respondWith(caches.match(req).then(hit => {
    const net = fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open('shell-' + VERSION).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => hit);
    return hit || net;
  }));
});
