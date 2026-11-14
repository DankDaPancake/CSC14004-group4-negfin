# Đối chiếu dữ liệu thô benchmark

Kiểm tra trên gói `results/handoff/benchmark-baseline-20261113/full-run/20261113-154220/` của checkout chính. Gói này không được Git theo dõi; xem [benchmark-handoff.md](benchmark-handoff.md). Đây là kiểm tra tính nhất quán nội bộ, không chứng minh phép đo phản ánh đúng runtime hoặc correctness thuật toán.

Để kiểm tra lại summary và liên kết khóa run/phase: `python docs/validation/audit-raw-benchmark.py <đường-dẫn-tới-20261113-154220>`. Script này không thay thế đối chiếu bảng cold hoặc kiểm tra tên từng phase.

## Kết quả ngày 14/11/2026

- `runs.csv`: 581 lượt, tất cả ghi `ok`; mỗi khóa run_id/variant/scope/dataset/fraction/minsup/emit_mode/repetition là duy nhất.
- `phases.csv`: 2.905 dòng, đủ 5 dòng trên mỗi lượt, không có khóa phase mồ côi. Đây là kiểm tra số dòng; chưa xác nhận danh tính đầy đủ của cả năm phase.
- Tính lại độc lập từ `runs.csv` và `phases.csv`: đủ 2.250 nhóm trong `summary.csv`, không trùng khóa, không thiếu nhóm, không sai median/min/max/n trong dung sai số thực 1e-11 tương đối hoặc 1e-9 tuyệt đối.
- Đối chiếu 35 dòng bảng cold với ba lượt raw mỗi cấu hình: median/min/max của wall và peak RSS khớp sau làm tròn (lần lượt sai số tối đa 0,00051 giây và 0,051 MiB). Chưa đối chiếu toàn bộ bảng warm, scalability hoặc số lượng itemset trong báo cáo.

## Bước tiếp theo

Kiểm tra phase name và tính nhất quán counters/hash theo cấu hình; đối chiếu các bảng warm và scalability với dữ liệu thô. Sau đó tạo biểu đồ từ CSV thay vì bảng báo cáo đã làm tròn. Khi profiling, giữ code Baseline nguyên vẹn, đo overhead, ghi commit/dataset/minsup và so mẫu kết quả.
