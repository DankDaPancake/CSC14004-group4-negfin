# Kế hoạch hoàn tất bài nộp CSC14004

**Mục tiêu:** Nộp một link GitHub công khai có báo cáo IEEE và demo tái lập được. Thực hiện theo thứ tự dưới đây.

1. [x] **Merge báo cáo IEEE.** [PR #18](https://github.com/DankDaPancake/CSC14004-group4-negfin/pull/18) đã merge vào `main` ở `167d277`, CI pass. Bản PDF gồm 12 trang, với tài liệu tham khảo bắt đầu ở trang 12.
2. [ ] **Tách demo theo môi trường.** Đã tạo `notebooks/demo_local.ipynb` và `notebooks/demo_colab.ipynb`. Local tìm checkout hiện tại và dùng Julia đã cài. Colab lấy source theo `REF` và chuẩn bị runtime cần thiết. Cả hai dùng cùng các cell xử lý dữ liệu và giải thích công dụng `pandas` và `openpyxl`. Run All trên Windows với Julia 1.12.0 đã khớp số liệu README. Bản Colab đã qua kiểm tra cấu trúc và cú pháp, còn chờ Run all trên runtime Colab mới.
3. [ ] **Xác minh nguồn tải.** Tải thử theo manifest và so SHA-256. TA cho phép dùng FIMI nếu truy cập ổn định khi chấm. Với tập chỉ có URL SPMF, ghi rõ nguồn và hỏi lại TA nếu cần xác nhận ngoại lệ lưu trữ.
4. [ ] **Kiểm tra commit chốt.** Chạy lại Julia suite và hai notebook, cập nhật kết quả trong README và thử mở PDF, Colab và link dữ liệu khi chưa đăng nhập.
5. [ ] **Nộp và ôn vấn đáp.** Nộp một link repo công khai trên Moodle. Ôn cách negFIN đếm support, tỉa nhánh, phạm vi đo benchmark và cách diễn giải hai ứng dụng.

Phản hồi TA cho phép dùng thư viện hỗ trợ tiền xử lý nếu ghi rõ mục đích. Hai ứng dụng vẫn chạy negFIN của nhóm. Giao diện là tùy chọn và tách notebook riêng cho từng ứng dụng là khuyến nghị.
