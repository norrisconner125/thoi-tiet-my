# Thời Tiết Mỹ

App thời tiết cho nước Mỹ, dữ liệu chính thức từ NOAA:

- Thời tiết hiện tại (trạm quan trắc gần nhất), dự báo 48 giờ và 7 ngày — National Weather Service API
- Cảnh báo thời tiết nguy hiểm, vẽ vùng cảnh báo trên bản đồ
- Bản đồ radar (NOAA/NCEP MRMS) dùng Leaflet
- Bản thảo luận dự báo (Area Forecast Discussion) của văn phòng NWS
- Theo dõi bão từ National Hurricane Center + Triển vọng thời tiết nhiệt đới
- **Bản đồ cảnh báo** (`map.html`): mọi cảnh báo hiện hành của NWS theo bang/toàn quốc, tô màu theo bảng màu chính thức,
  kèm số liệu quan trắc METAR (nhiệt độ, điểm sương, gió, gió giật, tầm nhìn, áp suất) của hơn 2.000 trạm
- **Bản đồ 3D kiểu nhà đài** (`map3d.html`, MapLibre GL): địa hình thật, ảnh vệ tinh, vùng cảnh báo dựng khối
  (càng nguy hiểm càng cao, xếp chồng khi trùng vùng), cột số liệu 3D, radar phủ địa hình,
  chế độ "Dẫn chương trình" tự bay tới từng cảnh báo kèm thanh chữ như trên TV
- Cài lên điện thoại/máy tính như app (PWA), mở được khi mất mạng

Không cần API key, không cần server riêng.

## Đưa app lên mạng bằng GitHub Pages (miễn phí)

1. Tạo tài khoản tại https://github.com nếu chưa có.
2. Bấm **New repository**, đặt tên ví dụ `thoi-tiet-my`, chọn **Public**, bấm **Create repository**.
3. Trong repo vừa tạo, bấm **uploading an existing file**, kéo **toàn bộ nội dung** thư mục này vào
   (gồm `index.html`, `sw.js`, `manifest.webmanifest`, `.nojekyll`, thư mục `icons`, `data`, `.github`), rồi bấm **Commit changes**.
   - Lưu ý: thư mục `.github` bắt đầu bằng dấu chấm nên có thể bị ẩn. Trên macOS bấm `Cmd+Shift+.` để hiện, trên Windows bật "Hidden items".
4. Vào **Settings → Pages**. Ở mục **Source** chọn **GitHub Actions**.
5. Vào tab **Actions**, chọn workflow **Triển khai app**, bấm **Run workflow**.
   Workflow này đăng app và tải dữ liệu NOAA mới (bão NHC, quan trắc METAR) mỗi 30 phút.
6. Sau 1–2 phút, app có tại: `https://<tên-tài-khoản>.github.io/thoi-tiet-my/`

## Cài lên điện thoại

- **iPhone (Safari):** mở link → nút Chia sẻ → **Thêm vào MH chính**.
- **Android (Chrome):** mở link → menu ⋮ → **Cài đặt ứng dụng** (hoặc bấm nút **Cài app** trong trang).
- **Máy tính (Chrome/Edge):** bấm biểu tượng cài đặt ở thanh địa chỉ, hoặc nút **Cài app**.

## Chạy thử trên máy (không cần đăng lên mạng)

```bash
python -m http.server 8000
```
rồi mở http://localhost:8000

## Ghi chú

- Dữ liệu NWS chỉ phủ lãnh thổ Hoa Kỳ.
- Workflow `.github/workflows/deploy.yml` chạy `scripts/fetch_noaa.py` để tạo `data/CurrentStorms.json` và `data/metars-us.json`
  mỗi 30 phút (không commit vào repo), vì trình duyệt có thể bị chặn khi gọi thẳng NHC/AWC.
  App luôn thử gọi thẳng trước, lỗi mới dùng bản sao này.
- Bản đồ cảnh báo lưu hình dạng các vùng NWS trong trình duyệt 30 ngày, nên lần đầu xem một bang sẽ chậm hơn các lần sau.
- GitHub có thể tự tắt workflow theo lịch nếu repo không có hoạt động trong 60 ngày; khi đó vào tab Actions bấm **Enable workflow**.
- Muốn cập nhật app sau khi sửa: tải file mới lên repo, rồi tăng `VERSION` trong `sw.js` (ví dụ `v3` → `v4`) để điện thoại nhận bản mới.
