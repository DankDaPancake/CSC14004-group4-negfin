# Kế hoạch tổng hợp benchmark cho Chương 2

**Mục tiêu** — Tổng hợp kết quả bàn giao ngày 19-11-2026 vào Chương 2, với số liệu có thể đối chiếu lại từ các lượt đo thô.

**Nguồn** — Gói `results/benchmark-baseline-optimized-20261119/` và cấu hình paired đã merge trong PR #10.

- [x] Kiểm SHA-256 của gói, đối chiếu số lượt theo scope, variant và chế độ xuất. Kiểm cặp theo dataset, fraction, minsup, checksum, số mẫu và số byte output cold.
- [x] Tính lại median cold wall và peak RSS theo cấu hình. Tổng hợp độ phủ, tốc độ và bộ nhớ trong `docs/report/chapter2.md`, giữ bảng chi tiết và nêu riêng trường hợp T10I4D100K.
- [x] Cập nhật `docs/validation/benchmark-handoff.md` và README với đường dẫn gói local, hướng dẫn tái lập và giới hạn dữ liệu. Giữ raw runs ngoài Git.
- [x] Đối chiếu 60 dòng bảng với CSV, chạy lại renderer và test Julia trước khi mở PR.
