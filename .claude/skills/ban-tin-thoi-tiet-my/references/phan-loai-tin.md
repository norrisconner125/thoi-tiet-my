# Phân loại & chọn tin hot

## 1. Điểm tự động (script, mục "0. BẢNG XẾP HẠNG ĐỀ TÀI")
Điểm tính theo **bang** và **loại sự kiện**, rồi cộng lại thành điểm bang.

| Nguồn | Điểm |
|---|---|
| Cảnh báo NWS (mỗi loại trong bang) | Tornado/Flash Flood/Extreme Wind Emergency 60 • Hurricane Warning 50 • Storm Surge Warning 40 • PDS Tornado Watch 35 • Blizzard/Ice Storm Warning 28 • Tropical Storm Warning 25 • Hurricane Watch 25 • Tornado Warning 18 • Extreme Heat/Cold Warning 18 • Winter Storm Warning 16 • Tornado Watch 16 • Flash Flood Warning 14 • High Wind Warning 9 • Severe T-storm Watch 9 • Winter Storm Watch 9 • Red Flag 7 • Flood Warning 6 • Severe T-storm Warning 5 • các Advisory 1–3 |
| Nhiều cảnh báo cùng loại | × (1 + 0,3 × (n−1)), tối đa × 2,5 |
| SPC Convective Outlook (mức cao nhất tại thành phố trong bang) | MRGL 3 • SLGT 8 • ENH 16 • MDT 28 • HIGH 40; ngày 2 chia 2, ngày 3 chia 3 |
| WPC Excessive Rainfall | Marginal 2 • Slight 6 • Moderate 18 • High 30; chia theo ngày như SPC |
| SPC Storm Reports | mỗi lốc xoáy 7 (tối đa 45) • gió 1 (tối đa 15) • mưa đá 1 (tối đa 10) • mưa đá ≥2" +3; hôm qua × 0,6 |
| Tín hiệu mô hình (ngày 1–10) | độ tin cậy CAO 6 • TRUNG BÌNH 3 mỗi ngày; tối đa 18 mỗi loại |

**Gom đề tài**
1. Mỗi bang lấy **loại sự kiện chính** = loại có điểm cao nhất.
2. Các bang **liền kề** có **cùng loại sự kiện chính** → một hệ thống.
3. Trong hệ thống, bang **≥45 điểm → video riêng**. Các bang còn lại → **một video khu vực** ("… outside Texas"), điểm = bang mạnh nhất + ½ các bang còn lại.
4. Đề tài <15 điểm bị bỏ. Mức: **≥70 RẤT HOT**, **40–69 HOT**, **15–39 ĐÁNG CHÚ Ý**.
5. AK, HI, PR, VI, GU không có bang liền kề → luôn là đề tài riêng nếu đủ điểm.

## 2. Claude điều chỉnh bằng tin tức đã xác thực
Điểm tự động chỉ đo **mức nguy hiểm khí tượng**. "Hot" với khán giả còn phụ thuộc tác động thực tế. Cộng/trừ và ghi lý do:

| Yếu tố (phải có nguồn uy tín) | Điều chỉnh |
|---|---|
| Có người chết/bị thương (cơ quan chính quyền xác nhận) | +30 |
| Lốc xoáy đánh trúng thị trấn/thành phố, thiệt hại lớn có hình ảnh từ nhà đài | +20 |
| Mất điện ≥100.000 khách hàng (PowerOutage.us / công ty điện) | +15 |
| Tuyên bố tình trạng khẩn cấp (thống đốc/thị trưởng), sơ tán | +15 |
| Kỷ lục (nhiệt độ, lượng mưa, tuyết) do NWS xác nhận | +10 |
| Ảnh hưởng thành phố lớn (top 25 vùng đô thị: NYC, LA, Chicago, Dallas–Fort Worth, Houston, Washington, Philadelphia, Miami, Atlanta, Boston, Phoenix, San Francisco, Detroit, Seattle, Minneapolis, San Diego, Tampa, Denver, Baltimore, St. Louis, Orlando, Charlotte, San Antonio, Portland, Sacramento) | +10 |
| Ảnh hưởng đi lại dịp lễ/cao điểm (Thanksgiving, Giáng sinh…), sân bay lớn hủy chuyến | +10 |
| Báo chí quốc gia (AP, NBC, ABC, CBS, CNN) đang đưa tin nổi bật | +10 |
| Sự kiện đã kết thúc, chỉ còn dọn dẹp, không có diễn biến mới | −15 |
| Chỉ có tín hiệu mô hình, chưa có sản phẩm chính thức nào | −10 |

Sau điều chỉnh, áp dụng lại ngưỡng: bang ≥45 → video riêng.
**Ví dụ:** Oklahoma 38 điểm (Tornado Watch + báo cáo lốc) nhưng có lốc xoáy EF-? đánh vào thị trấn, 2 người chết theo cơ quan quản lý khẩn cấp hạt → 38 + 30 + 20 = 88 → tách Oklahoma ra video riêng.

## 3. Đặt tên đề tài (dùng làm gốc cho tiêu đề video)
- Bang riêng: `[Bang] [Hiện tượng]` — "Texas Severe Storms", "Hurricane [Tên bão] Florida".
- Khu vực: `[Vùng] [Hiện tượng]` — "Southern Plains Severe Storms", "Upper Midwest Winter Storm". Gọi bằng tên vùng quen thuộc với người Mỹ
  (Northeast, Mid-Atlantic, Southeast, the South, Midwest, Great Lakes, Plains, Rockies, Southwest, West Coast, Pacific Northwest).
- Bão nhiệt đới có tên → dùng tên bão.
- Video khu vực có bang đã tách riêng: thêm "outside [Bang]" trong ghi chú; tiêu đề video không cần ghi "outside", chỉ cần nêu các bang còn lại.

## 4. Ví dụ bảng đề tài trong ngày
| # | Đề tài | Loại | Bang | Hiện tượng | Thời điểm | Mức | Lý do |
|---|---|---|---|---|---|---|---|
| 1 | Texas Severe Storms | Bang riêng | TX | Dông mạnh/lốc xoáy | Hôm nay | RẤT HOT | Tornado Emergency Dallas, SPC Enhanced |
| 2 | South Severe Storms | Khu vực | LA, MS, AR | Dông mạnh/lốc xoáy | Tối nay | HOT | PDS Tornado Watch, cùng hệ thống với #1 |
| 3 | Upper Midwest Winter Storm | Khu vực | MN, WI, MI, ND | Bão tuyết | Hôm nay–mai | HOT | Blizzard Warning, 3/4 mô hình tuyết lớn |
| 4 | California Fire Danger | Bang riêng | CA | Cháy rừng | Hôm nay | ĐÁNG CHÚ Ý | Red Flag Warning |
