# Kế hoạch hoàn tất bài nộp CSC14004

**Mục tiêu:** Nộp một link GitHub công khai có báo cáo IEEE và demo tái lập được. Thực hiện theo thứ tự dưới đây.

1. [x] **Merge báo cáo IEEE.** [PR #18](https://github.com/DankDaPancake/CSC14004-group4-negfin/pull/18) đã merge vào `main` ở `167d277`, CI pass. Bản PDF gồm 12 trang, với tài liệu tham khảo bắt đầu ở trang 12.
2. [x] **Tách demo theo môi trường.** [PR #19](https://github.com/DankDaPancake/CSC14004-group4-negfin/pull/19) đã merge hai notebook vào `main`. Run All local trên Windows dùng Julia 1.12.0. Nhóm cũng đã chạy Colab tới cell cuối trên `1ff1cfa` với Julia 1.12.6 và variant `baseline`. Kết quả hai ứng dụng khớp với README.
3. [x] **Xác minh nguồn tải.** Ngày 27-11-2026, cả bảy URL trong manifest đều tải được không cần đăng nhập và khớp SHA-256. Thầy chấp nhận dùng FIMI và đã xác nhận có thể tải Mushroom trực tiếp từ SPMF kèm kiểm tra SHA-256. Xem [kết quả xác minh](../../validation/dataset-source-verification.md) và [hướng dẫn khôi phục Retail và T10I4D100K từ FIMI](../../validation/fimi-recovery.md).
4. [ ] **Kiểm tra commit chốt.** Chạy lại Julia suite và hai notebook trên cùng commit. Giữ output cell tổng kết cuối trong từng notebook để ghi lại SHA đã chạy, phiên bản Julia, variant và kết quả hai ứng dụng. Cập nhật kết quả trong README và thử mở PDF, Colab và link dữ liệu khi chưa đăng nhập.
5. [ ] **Nộp và ôn vấn đáp.** Nộp một link repo công khai trên Moodle. Ôn cách negFIN đếm support, tỉa nhánh, phạm vi đo benchmark và cách diễn giải hai ứng dụng.

Phản hồi TA cho phép dùng thư viện hỗ trợ tiền xử lý nếu ghi rõ mục đích. Hai ứng dụng vẫn chạy negFIN của nhóm. Giao diện là tùy chọn và tách notebook riêng cho từng ứng dụng là khuyến nghị.
