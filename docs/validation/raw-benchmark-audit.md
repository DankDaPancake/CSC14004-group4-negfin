# Đối chiếu dữ liệu thô benchmark

Kiểm tra trên gói `results/handoff/benchmark-baseline-20261113/full-run/20261113-154220/` của checkout chính. Gói này không được Git theo dõi; xem [benchmark-handoff.md](benchmark-handoff.md). Đây là kiểm tra tính nhất quán nội bộ, không chứng minh phép đo phản ánh đúng runtime hoặc correctness thuật toán.

Để kiểm tra lại summary và liên kết khóa run/phase: `python docs/validation/audit-raw-benchmark.py <đường-dẫn-tới-20261113-154220>`. Script này không thay thế đối chiếu bảng cold hoặc kiểm tra tên từng phase.

## Kết quả ngày 14/11/2026

- `runs.csv`: 581 lượt, tất cả ghi `ok`; mỗi khóa run_id/variant/scope/dataset/fraction/minsup/emit_mode/repetition là duy nhất.
- `phases.csv`: 2.905 dòng, đủ 5 dòng trên mỗi lượt, không có khóa phase mồ côi. Đây là kiểm tra số dòng; chưa xác nhận danh tính đầy đủ của cả năm phase.
- Tính lại độc lập từ `runs.csv` và `phases.csv`: đủ 2.250 nhóm trong `summary.csv`, không trùng khóa, không thiếu nhóm, không sai median/min/max/n trong dung sai số thực 1e-11 tương đối hoặc 1e-9 tuyệt đối.
- Đối chiếu 35 dòng bảng cold với ba lượt raw mỗi cấu hình: median/min/max của wall và peak RSS khớp sau làm tròn (lần lượt sai số tối đa 0,00051 giây và 0,051 MiB). Chưa đối chiếu toàn bộ bảng warm, scalability hoặc số lượng itemset trong báo cáo.
- Kiểm tra tên phase: từng lượt có đúng một mỗi tên normalize, prepare, build_bmc, collect_nodesets và mine. Kiểm tra 35 dòng warm: min_count, n_patterns, bmc_nodes, negative_records_scanned, median build_bmc và mine khớp. Với 10 dòng scalability, cold median wall và RSS khớp. Các cột khác chưa được kiểm toán đầy đủ.
- Kiểm tra thêm 210 giá trị trên 35 dòng warm: output, normalize+prepare, tổng count/write, cấp phát mine và GC khớp trong dung sai làm tròn. Kiểm tra thêm 80 giá trị trên 10 dòng scalability: số giao dịch, mẫu, mine, build, normalize+prepare, tổng warm, node và record quét khớp. Ở đây normalize+prepare là tổng hai median theo cách bảng báo cáo được xây dựng; đồ thị mới dùng median của tổng theo từng lượt.
- Đối chiếu 90 tổ hợp metric/cấu hình của đồ thị cold/scalability với các nhóm `summary.csv`: median/min/max/n khớp trong dung sai số thực. Kiểm tra 12 ô hiệu write−count có giá trị số và 35 ô RSS trừ nền: đều khớp trong dung sai làm tròn; các ô `*`/`≈0` không được kiểm định số. Hai phép trừ vẫn là ước lượng, không phải số đo trực tiếp.
- Trên 43 nhóm dataset/minsup/fraction, các counter có mặt trong `runs.csv` nhất quán; SHA256 input của tất cả run warm/cold trên tập đầy đủ khớp `env.toml`. Không suy diễn checksum tập con từ checksum tập đầy đủ.

## Bước tiếp theo

Biểu đồ đã được dựng từ CSV. Khi profiling, giữ code Baseline nguyên vẹn, đo overhead, ghi commit/dataset/minsup và so mẫu kết quả. Dữ liệu gốc và summary nhất quán không đồng nghĩa phương pháp đo không có bias.
