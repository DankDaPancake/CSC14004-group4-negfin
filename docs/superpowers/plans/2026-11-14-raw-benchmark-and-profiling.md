# Kế hoạch kiểm chứng số liệu thô và profiling Baseline

**Mục tiêu:** Kiểm tra số liệu bàn giao, vẽ lại từ CSV thô và xác định nguyên nhân tốn tài nguyên trước khi chọn tối ưu. Giữ Baseline và contract hiện có.

## 1. Kiểm chứng gói bàn giao

- [ ] Đọc `runs.csv`, `phases.csv`, `summary.csv`, `env.toml` trong `results/handoff/benchmark-baseline-20261113/full-run/20261113-154220/` của checkout chính; xác nhận checksum, commit, status, khóa từng lượt và số lần lặp.
- [x] Tính độc lập median/min/max/n theo từng cấu hình và giai đoạn, đối chiếu toàn bộ `summary.csv`; kiểm tra tính liên kết khóa giữa phase và run. Kết quả: `docs/validation/raw-benchmark-audit.md`.
- [ ] Đối chiếu các bảng cold, warm và scalability trong báo cáo với số liệu gốc theo độ làm tròn; đã kiểm tra đầy đủ wall/RSS của 35 dòng cold, còn warm và scalability.

## 2. Đồ thị từ dữ liệu gốc

- [ ] Bổ sung kiểm thử parser và nhóm số liệu từ fixture nhỏ, gồm thiếu input và phạm vi warm/cold; xác nhận test fail trước khi cài đặt.
- [ ] Cập nhật script nhận đường dẫn gói dữ liệu qua tham số, không phụ thuộc tuyệt đối vào máy; dựng median và khoảng min–max từ từng lượt, giữ nhãn đơn vị, dataset và phạm vi.
- [ ] So sánh số điểm và giá trị với CSV gốc, kiểm tra trực quan hình, cập nhật giải thích và giới hạn; không commit dataset hoặc output khai thác lớn.

## 3. Profiling và hướng tiếp theo

- [ ] Ghi rõ môi trường và chọn Retail 0,001, Chess 0,3 và Accidents đại diện; chọn cấu hình pilot nhỏ trước để kiểm tra công cụ, giới hạn runtime và dung lượng.
- [ ] Dùng profiler Julia xác định hotspot CPU và cấp phát, tách count/write khi có thể; giữ nguyên Baseline, mô tả overhead và không suy luận quan hệ nhân quả từ tương quan.
- [ ] Đối chiếu mẫu đầu ra/support trước và sau instrumentation; so kết quả ít nhất một workload lặp lại. Lưu lệnh, commit, ngưỡng và phiên bản.
- [ ] Ghi giả thuyết ưu tiên và kế hoạch Optimized riêng sau khi có bằng chứng; chưa tự coi thang scalability 20/40/60/80/100% là đáp ứng checklist 10/25/50/75/100%.

## Kết thúc

- [ ] Chạy kiểm thử liên quan và suite Julia, cập nhật tài liệu và PR hiện có; không merge khi chưa được giao.
