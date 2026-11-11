# Ghi nhận triển khai Baseline

Ngày triển khai: 12/11/2026. Nhánh local: `feat/negfin-baseline`. Thuật toán: negFIN, bitmap BigInt, Julia 1.12.0. Không push, publish hoặc gửi tin nhắn cho các thành viên.

## Quyết định khi triển khai

1. Dùng repo mới riêng ở `group04-fim-negfin/`, trên nhánh feature, không thêm worktree thứ hai vì chưa có code/nhánh khác cần bảo vệ. Nếu có công việc song song sau này, cần checkout riêng.
2. Tải runtime portable có xác minh SHA256 vào `.tools/` bên ngoài repo; không thay PATH hệ thống. Chi phí là dung lượng và thời gian tải; đường dẫn portable phụ thuộc máy.
3. Cho phép bookkeeping PowerShell nếu script Bash không tương thích Windows; thực tế các script task-start/task-done đã chạy được và có ledger RED/GREEN. Rủi ro nếu phải dùng thủ công là sai trạng thái ledger, cần đối chiếu Git/test.
4. Sửa lỗi trong snippet kế hoạch: constructor Julia đúng là `BigInt(...)` hoặc `big(...)`, không có hàm `bigint(...)`. Chỉ sửa cú pháp, không đổi biểu diễn hay thuật toán.
5. Nâng runtime tham chiếu từ Java 21 lên Java 25 vì SPMF 2.67a dùng class-file version 69. Chi phí là yêu cầu Java mới cho người chạy test SPMF; thuật toán Julia không phụ thuộc Java.
6. Tự chuẩn bị public benchmark, manifest/checksum và harness để kiểm chứng phần Baseline, thay vì đợi Hiếu cung cấp. Không thay đổi phân công lâu dài hoặc coi toàn bộ benchmark Chương 2 đã hoàn thành.
7. Dùng đúng snapshot nguồn SPMF có 8.416 dòng cho Mushroom; ghi rõ khác 8.124 trong mô tả đề, không tự cắt/chỉnh dữ liệu. Khi nhóm đổi nguồn dataset phải lập manifest và kiểm chứng lại.
8. Bàn giao CLI/API bằng tài liệu và test; việc Hiếu/Tiến xác nhận trực tiếp trên máy và dữ liệu ứng dụng riêng vẫn cần nhóm thực hiện, chưa có bằng chứng để đánh dấu đã xảy ra.

## Phạm vi đã kiểm chứng

Local suite, toy expected, bitmap >64, promotion, oracle độc lập, parser tham chiếu và correctness trên 5 file full ở manifest. Không phải benchmark so tốc độ chính thức; không phải ứng dụng thực tế hay Colab.

Output SPMF được staging vào đường dẫn mới cho mỗi lần chạy để không vô tình dùng lại kết quả cũ khi SPMF thất bại. Regression cho input tham chiếu không tồn tại đã được quan sát FAIL trước khi sửa.
