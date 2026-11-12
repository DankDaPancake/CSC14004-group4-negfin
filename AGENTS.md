# Hướng dẫn làm việc trong repository

Áp dụng cho người và các coding agent làm việc trong repository này. Ưu tiên chỉ dẫn cụ thể của người dùng và các quy định có phạm vi hẹp hơn trong thư mục con.

## Nhánh và pull request

- `main` là nhánh được bảo vệ. Không commit hoặc push trực tiếp lên `main`, kể cả thay đổi nhỏ; không force push, xóa hoặc viết lại lịch sử `main`.
- Trước khi triển khai, kiểm tra `git status`, cập nhật thông tin `origin/main` và tạo một nhánh riêng từ `origin/main` mới nhất. Không ghi đè, xóa hay tự ý đưa thay đổi chưa commit của người khác vào nhánh mới. Nếu công việc phụ thuộc vào nhánh chưa merge, tạo nhánh từ nhánh phụ thuộc và ghi rõ trong PR.
- Đặt tên theo mục đích: `feature/<mo-ta-ngan>`, `fix/<mo-ta-ngan>`, `docs/<mo-ta-ngan>`, `test/<mo-ta-ngan>`, `ci/<mo-ta-ngan>` hoặc `chore/<mo-ta-ngan>`. Dùng chữ thường và dấu gạch ngang; ví dụ `feature/optimized-bitmap`.
- Mỗi nhánh tập trung vào một thay đổi có thể review. Đẩy nhánh riêng và mở PR vào `main`; mô tả mục đích, thay đổi và kết quả kiểm thử. Thông thường cần ít nhất một người khác duyệt trước khi merge; quản trị viên có thể tự kiểm tra và bỏ qua yêu cầu review khi cần. Xử lý các nhận xét và lỗi CI trước khi merge.
- Không tự merge PR hoặc thay đổi cấu hình bảo vệ nhánh nếu chưa được giao nhiệm vụ. Không force push nhánh dùng chung nếu chưa có thỏa thuận với người liên quan.

## Phát triển và kiểm chứng

- Dự án dùng Julia >= 1.9; giữ Baseline negFIN và định dạng CLI/SPMF theo `docs/baseline-contract.md`. Không thêm phụ thuộc FIM để thay thế cài đặt của nhóm.
- Chạy `julia --startup-file=no --project=. test/runtests.jl` trước khi mở PR; báo rõ test chưa chạy hoặc thất bại. Với thay đổi thuật toán, bổ sung kiểm chứng correctness thích hợp và đối chiếu SPMF theo README khi có đủ dữ liệu và runtime.
- Ghi rõ phạm vi đo khi benchmark; không nhầm tổng cấp phát với peak RAM, và không so sánh thời gian có phạm vi startup/JIT/I/O khác nhau.
- Không commit dataset benchmark lớn, runtime, jar, kết quả sinh tự động hoặc thông tin bí mật. Giữ checksum và hướng dẫn tái lập theo manifest và README.
- Không chỉnh sửa hoặc xóa những thay đổi sẵn có ngoài phạm vi nhiệm vụ. Cập nhật tài liệu khi hành vi hoặc cách tái lập thay đổi.
