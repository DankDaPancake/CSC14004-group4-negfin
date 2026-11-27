# Kế hoạch hoàn tất bài nộp CSC14004

**Mục tiêu:** Nộp một link GitHub công khai có báo cáo IEEE và demo tái lập được. Thực hiện theo thứ tự dưới đây.

1. [x] **Merge báo cáo IEEE.** [PR #18](https://github.com/DankDaPancake/CSC14004-group4-negfin/pull/18) đã merge vào `main` ở `167d277`, CI pass. Bản PDF gồm 12 trang, với tài liệu tham khảo bắt đầu ở trang 12.
2. [x] **Tách demo theo môi trường.** [PR #19](https://github.com/DankDaPancake/CSC14004-group4-negfin/pull/19) đã merge hai notebook vào `main`. Run All local trên Windows dùng Julia 1.12.0. Nhóm cũng đã chạy Colab tới cell cuối trên `1ff1cfa` với Julia 1.12.6 và variant `baseline`. Kết quả hai ứng dụng khớp với README.
3. [x] **Xác minh nguồn tải.** Tải thử theo manifest và so SHA-256. TA cho phép dùng FIMI nếu truy cập ổn định khi chấm. Với tập chỉ có URL SPMF, ghi rõ nguồn và hỏi lại TA nếu cần xác nhận ngoại lệ lưu trữ. Ngày 27-11-2026, cả bảy URL trong manifest đều tải được không cần đăng nhập và khớp SHA-256; xem [kết quả xác minh](../../validation/dataset-source-verification.md). Còn chờ TA xác nhận link SPMF cho Mushroom và cách dựng lại Retail, T10I4D100K từ FIMI.
4. [ ] **Kiểm tra commit chốt.** Chạy lại Julia suite và hai notebook, cập nhật kết quả trong README và thử mở PDF, Colab và link dữ liệu khi chưa đăng nhập.
5. [ ] **Nộp và ôn vấn đáp.** Nộp một link repo công khai trên Moodle. Ôn cách negFIN đếm support, tỉa nhánh, phạm vi đo benchmark và cách diễn giải hai ứng dụng.

Phản hồi TA cho phép dùng thư viện hỗ trợ tiền xử lý nếu ghi rõ mục đích. Hai ứng dụng vẫn chạy negFIN của nhóm. Giao diện là tùy chọn và tách notebook riêng cho từng ứng dụng là khuyến nghị.
