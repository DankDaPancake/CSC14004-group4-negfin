# Thông tin bàn giao benchmark Baseline

Gói của Hiếu được lưu local tại `results/handoff/benchmark-baseline-20261113/` và `results/handoff/benchmark-baseline-20261113.zip`. Cả hai nằm trong thư mục `results/` được Git bỏ qua: **không có trong clone mới**, cần sao lưu/chia sẻ riêng để các thành viên tái lập. File ZIP có SHA256 `e046789c3e4958fd1ef9a5134bfec3b116488319f82ebcc24f8ac6e3a429e9bb`.

## Nội dung

- `README.md`: hướng dẫn của Hiếu, nguồn, lệnh, phạm vi đo và phần còn thiếu.
- `full-run/20261113-154220/`: `runs.csv` (581 lượt), `phases.csv` (2.905 dòng), `summary.csv` và `env.toml`. Đã kiểm tra tất cả 581 trạng thái là `ok`.
- `pilots/`: 8 lượt pilot cùng kết quả, stats và stderr; Mushroom 0,01 chạm giới hạn output, không phải số đo hoàn tất.
- `config/`: config và manifest tại commit đo, SHA256 dataset và diff cấu hình pilot chưa commit; `logs/`: stdout, stderr và sổ quyết định.
- `overhead/`: script và số đo so sánh phase hook; các đường dẫn tuyệt đối trong script là của máy Hiếu và cần điều chỉnh khi chạy máy khác.

Lượt chính chạy tại commit `3ecd0c1ce032e42b271100f2531260d53dde2d65`, working tree sạch, Julia 1.12.0 một luồng, Windows 11 và i5-13600K. Cold bao gồm startup/JIT/I/O; warm không bao gồm các phần đó. Tổng cấp phát không phải peak RSS. Số liệu được ghi trước các sửa đổi sau lượt chạy; xem [báo cáo gốc](benchmark-baseline.md) và README trong gói để biết giới hạn.

## Kiểm tra bản sao local

Đã đối chiếu SHA256 của 292 file giữa thư mục bàn giao, bản local và từng entry trong ZIP; đã kiểm tra ZIP không lỗi. Năm file trong `data/benchmark/` của checkout chính khớp SHA256 với manifest bàn giao. ZIP không chứa dữ liệu benchmark gốc hoặc output itemset lớn; các file benchmark local không được Git theo dõi và vẫn cần sao lưu hoặc tải lại theo manifest khi chuyển máy.

Đã tính lại cold median từ ba lượt trong `runs.csv` cho Retail 0,001 (36,1647333 s), Chess 0,3 (41,6806076 s), Accidents 0,2 (49,9652722 s), khớp bảng báo cáo sau làm tròn. Đây là đối chiếu đại diện, chưa phải kiểm toán toàn bộ bảng.

Scalability hiện chỉ có 20/40/60/80/100%; cần bổ sung hoặc xác nhận các mức 10/25/50/75/100%. Chưa có bằng chứng nguồn Hugging Face/Kaggle của cả năm tập khớp snapshot. Những điểm này không được giải quyết bằng việc sao chép gói.
