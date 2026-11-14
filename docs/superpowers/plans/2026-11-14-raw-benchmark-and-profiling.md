# Kế hoạch kiểm chứng số liệu thô và profiling Baseline

**Mục tiêu:** Kiểm tra số liệu bàn giao, vẽ lại từ CSV thô và xác định nguyên nhân tốn tài nguyên trước khi chọn tối ưu. Giữ Baseline và contract hiện có.

## 1. Kiểm chứng gói bàn giao

- [x] Đọc `runs.csv`, `phases.csv`, `summary.csv`, `env.toml` trong `results/handoff/benchmark-baseline-20261113/full-run/20261113-154220/` của checkout chính; xác nhận checksum input đầy đủ, commit, status, khóa từng lượt và số lần lặp.
- [x] Tính độc lập median/min/max/n theo từng cấu hình và giai đoạn, đối chiếu toàn bộ `summary.csv`; kiểm tra tính liên kết khóa giữa phase và run. Kết quả: `docs/validation/raw-benchmark-audit.md`.
- [x] Đối chiếu các cột số của bảng cold, warm và scalability với dữ liệu gốc theo độ làm tròn; các ô `*`/`≈0` là ký hiệu định tính, không kiểm định số. Xem phạm vi cụ thể trong `raw-benchmark-audit.md`.

## 2. Đồ thị từ dữ liệu gốc

- [x] Bổ sung kiểm thử nhóm số liệu từ fixture nhỏ, gồm lượt thất bại/thiếu giá trị và phạm vi warm/cold; test đã fail trước khi cài đặt.
- [x] Cập nhật script nhận đường dẫn gói dữ liệu qua tham số, không phụ thuộc tuyệt đối vào máy; dựng median và khoảng min–max từ từng lượt, giữ nhãn đơn vị, dataset và phạm vi.
- [x] Kiểm tra số điểm và giá trị nguồn trong CSV gốc, kiểm tra trực quan hình, cập nhật giải thích và giới hạn; không commit dataset hoặc output khai thác lớn.

## 3. Profiling và hướng tiếp theo

- [x] Ghi môi trường và chạy cấu hình pilot Retail 0,001/0,002/0,004, Chess 0,3/0,45/0,55 và Accidents 0,45; xem phạm vi count/write và số lần đo trong báo cáo profiling.
- [ ] Dùng profiler Julia phân tích CPU và cấp phát; pilot đã chạy count với callback fingerprint và write trên Chess 0,55, chưa đo allocation stack hay lặp đủ để ước lượng overhead tin cậy.
- [ ] Đối chiếu đầy đủ itemset/support trước và sau instrumentation; Chess 0,55, Retail 0,002 và Accidents 0,45 đã khớp SPMF qua file CLI có cùng SHA256 với cặp pilot write. Các workload count nặng hơn 0,3/0,001 mới so số mẫu/fingerprint, chưa đối chiếu chính xác.
- [x] Ghi giả thuyết ưu tiên và kế hoạch Optimized riêng dựa trên pilot; chưa tự coi thang scalability 20/40/60/80/100% là đáp ứng checklist 10/25/50/75/100%.

## Kết thúc

- [ ] Chạy kiểm thử liên quan và suite Julia, cập nhật tài liệu và PR hiện có; không merge khi chưa được giao.
