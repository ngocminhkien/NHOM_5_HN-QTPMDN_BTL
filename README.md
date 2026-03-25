# 🏢 Hệ thống Quản lý Tài sản Doanh nghiệp (Enterprise Asset Management)
Hệ thống ERP chuyên nghiệp được xây dựng trên nền tảng Odoo, tích hợp chặt chẽ quy trình Quản lý Tài sản với Nguồn nhân lực (HRM) và Kế toán (Accounting). 

## 📋 Giới thiệu Dự án
Dự án nhằm tự động hóa vòng đời của một tài sản từ khi định hình mua sắm, phân bổ sử dụng, khấu hao định kỳ, đến lúc thanh lý xuất toán. 
Hệ thống cung cấp cái nhìn 360 độ về chi phí tài sản trên phương diện tài chính, đồng thời hỗ trợ quản lý định danh vật lý (QR Code), lịch bảo trì tự động và theo dõi biến động nhật ký (Chatter/Audit Trail).

## 🏗 Kiến trúc Modules
Hệ thống bao gồm hệ sinh thái các module liên kết chặt chẽ với nhau:
* **`quan_ly_tai_san`** (Core): Module gốc quản lý Dashboard, danh mục tài sản, kiểm kê, đơn mượn trả, phân bổ và luân chuyển tài sản. Liên kết chặt chẽ với module Nhân sự chuẩn (`hr`).
* **`dnu_accounting_asset`** (Extension): Model kế thừa siêu cấu trúc, mang đến **Tự động hóa Mức 2 và Mức 3** liên quan đến hạch toán và khấu hao dài hạn.
* **`dnu_asset` & `nhan_su`** (Base): Khung sườn quản trị cơ sở độc lập gồm chứng chỉ, cấp bậc nhân viên và dữ liệu định danh vật lý sơ cấp.

## ✨ Các Tính năng Đột phá (Mức 1 đến Mức 3)
1. **Tích hợp HRM & Kế toán (Mức 1):** Ràng buộc bàn giao tài sản dựa trên trạng thái nghỉ việc của nhân viên quản lý một cách linh hoạt qua REST Request.
2. **Khấu hao & Bút toán Tự động (Mức 2):** 
   - Tự động sinh bảng Kế hoạch Khấu hao dự kiến kéo dài nhiều năm.
   - **Cron Job Kế toán:** Lịch trình chạy ngầm hàng tháng tự động sinh sổ nhật ký `account.move` mà không cần thao tác bấm xác nhận thủ công.
3. **Thanh lý Tài sản (Asset Disposal):** Wizard ghi nhận tài sản thanh lý. Tự động `cancelled` vạch khấu hao tương lai, đồng thời tạo cụm Bút toán *Ghi giảm TSCĐ*, *Chi tiết cấu thành tài sản* và *Doanh thu thanh lý* nội trong một Database Transaction duy nhất giúp bảo toàn toàn vẹn dữ liệu (ACID).
4. **QR Code Inventory:** Dynamic Gen mã QR cho phép quét điện thoại trỏ thẳng URL vào hồ sơ tài sản (Form View).
5. **Dashboard Báo cáo Tài chính (Pivot & Graph):** Ứng dụng SQL Aggregation của Postgres đẩy tải từ Backend Python, phân rã Chi phí khấu hao và Nguyên giá theo "Phòng ban" cực kỳ tối ưu RAM.
6. **Bảo trì Định kỳ Tự động (Mức 3):** Server check định kỳ rạng sáng, hệ thống tự động chèn Action/Todo nhắc nhở nhân viên 3 ngày trước hạn bảo trì.

## 🚀 Hướng dẫn Cài đặt
1. Khởi động môi trường Odoo Service `odoo-bin`.
2. Mở trình quản lý Apps -> Kích hoạt chế độ Developer Mode -> `Update Apps List`.
3. Đảm bảo hệ thống đã cài đặt các base module của Odoo: `hr`, `account`, `mail`.
4. Tìm và ấn Install theo thứ tự sau để rải Sequence Data an toàn: `nhan_su` -> `dnu_asset` -> `quan_ly_tai_san` -> `dnu_accounting_asset`.
5. Cài đặt thêm thư viện python OS: `pip install qrcode`.

---

## 🔄 Luồng nghiệp vụ: Từ lúc mua đến lúc thanh lý (Business Flow)
*(Mô tả phân đoạn để dựng biểu đồ mô hình hóa - Mermaid/Flowchart)*

1. **Khởi tạo Tài sản (Draft State):** Kế toán viên hoặc Quản trị viên nhập thông tin "Nguyên giá", "Loại tài sản", "Thời gian khấu hao dự kiến". Tài sản mới chưa tham gia vào CSDL Kế toán.
2. **Cấp phát & Bắt đầu sử dụng (In Use State):** 
   - Chọn "Nhân viên sử dụng" (Cơ chế Constrain: Chặn cấp phát nếu nhân viên đã nghỉ việc).
   - Nhấn hành động `Xác nhận bắt đầu sử dụng`: Hệ thống tự nội quy sinh Bảng Lịch trình Khấu hao các kỳ tương lai (Draft Depreciation Lines). Chuyển trạng thái sang `in_use`. Sinh tự động mã định danh QR Code.
3. **Luân chuyển / Mượn trả (Lifecycle Logging):** Người dùng tạo phiếu Luân chuyển, hệ thống ghi đè Bộ phận sử dụng mới để điều hướng chi phí hạch toán sang đúng phòng ban sau này.
4. **Khấu hao định kỳ (Auto-Depreciation via Cron):** Đến ngày đã định của mỗi tháng, Hệ thống Scheduler ngầm chạy rà soát Bảng lịch trình, khóa (`POST`) bút toán sổ nhật ký (`account.move`), qua đó hạch toán Nợ 214/Có ABC và tự cập nhật trừ "Giá trị còn lại".
5. **Bảo trì tài sản (Maintenance Phase):** CSDL theo dõi ngày bảo trì định kỳ. Trước 3 ngày, Cron Job gắp đúng Account của nhân viên đang giữ tài sản để sinh một Mail Activity Todo dội về Notification Odoo của họ.
6. **Thanh lý tài sản (End of Life / Disposal):** 
   - Kế toán nhấn "Thanh lý", khai báo "Giá bán / Giá thanh lý".
   - Hệ thống ra lệnh `Update` chốt chặn: HỦY (`cancelled`) các dòng lịch trình khấu hao còn dang dở.
   - Khởi tạo cụm bút toán đồng thời: Ghi giảm 211, Tăng Khấu hao lũy kế 214, Gắn vào Chi phí thanh lý 811 hoặc Ghi nhận Thu nhập khác 711. Kết nối với Tiền mặt 111.
   - Tài sản chính thức chuyển về trạng thái `Disposed` - Đóng rào vĩnh viễn vòng đời của tài nguyên vật lý này.
