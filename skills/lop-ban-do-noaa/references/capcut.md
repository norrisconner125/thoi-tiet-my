# Đưa clip vào CapCut

## Cách 1 — Dựng tay (không cần skill khác)

1. Mở CapCut PC → dự án 1920×1080 (16:9).
2. Import cả thư mục `lop_noaa/`. Kéo `N01.mp4`, `N02.mp4`… vào timeline chính theo thứ tự lời đọc.
3. Cắt độ dài cho khớp voice. Clip tĩnh có zoom chậm từ đầu đến cuối, nên cắt bớt đuôi vẫn mượt. Clip chạy hình nên giữ đủ ít nhất một vòng (`số khung × khung_giay + 1.2 s`).
4. Chuyển cảnh: Mix 0.5–0.8 s giữa hai bản đồ cùng vùng; cắt thẳng khi đổi vùng.
5. Muốn tự gõ chữ bằng template CapCut: dùng `<id>_sach.png` (bản đồ không có chữ), đặt thời lượng bằng lời đọc, thêm keyframe Scale 100 → 106 % cho giống clip.

Ghi chú:
- Clip không có âm thanh. Đừng thêm nhạc nền nếu kênh theo kiểu ban-tin-ve-tinh.
- Dòng nguồn ở đáy khung là phần ghi công dữ liệu NOAA/USGS; đừng che bằng phụ đề. Phụ đề CapCut nên đặt cao hơn ~70 px.

## Cách 2 — Cùng skill `ban-tin-ve-tinh`

`ban-tin-ve-tinh` ghi thẳng dự án CapCut và có sẵn 4 lớp (vệ tinh, radar lưu trữ, mô hình, cảnh báo NWS). Dùng skill này để thêm lớp nó không có:

1. Đặt `"ra": "<case>/lop_noaa"` trong `canh.json`, xuất clip.
2. Chạy lại kiểm kê của ban-tin-ve-tinh:
   `python -X utf8 "<ban-tin-ve-tinh>/scripts/kiem_ke.py" "<case>" --voice … --srt …`
   Clip trong `lop_noaa/` được đánh số `V..` trong `_tt/tu_lieu.json` (tra theo tên file).
3. Trong `_tt/lap_edl.py`:
   ```python
   edl_ban_do.lap(case, "ten-v2",
       chen={12: [{"id": "V31"}],                 # câu 12: thay bản đồ cũ bằng clip SPC
             13: ["BAN_DO", {"id": "V32"}]},      # câu 13: nửa đầu bản đồ cũ, nửa sau clip LSR
       do_hoa=["V31", "V32"], ...)                # đồ hoạ: không gắn thẻ địa danh
   ```
4. `dung_capcut.py --thu` để xem `_tt/timeline.txt`, rồi ghi dự án mới (`-v2`…), CapCut phải tắt hẳn.

Độ dài: ban-tin-ve-tinh dùng clip từ giây `ss` trong độ dài câu, nên `giay` của cảnh nên ≥ độ dài câu (hoặc tổng các câu) sẽ chèn. Đọc `_tt/cau.json` để lấy `t1 − t0`.
