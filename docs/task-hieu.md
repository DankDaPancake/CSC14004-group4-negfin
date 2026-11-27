# Task còn lại của Hiếu — xác minh nguồn tải benchmark

Benchmark Baseline–Optimized và Julia–SPMF đã hoàn tất, kết quả và hình đã vào [báo cáo IEEE](Report.pdf). Phần còn lại của Hiếu là **xác minh người chấm có thể tải lại đúng năm snapshot đã dùng để đo**. Hai ZIP bàn giao chứa bằng chứng benchmark. Các file đầu vào cần tải theo [manifest benchmark](../data/benchmark/manifest.toml).

## Các bước thực hiện

1. Tạo thư mục tạm ngoài đường dẫn dữ liệu hiện có. Tải mới, không cần đăng nhập, từ `source_url` trong manifest. Với Chess và Accidents, tải thử thêm `mirror_url` của FIMI.
2. Tính SHA-256 của từng file vừa tải. Với một file trên Windows, dùng `Get-FileHash -Algorithm SHA256 -LiteralPath <đường-dẫn-file>`. So với trường `sha256` tương ứng, bỏ qua khác biệt hoa thường của chuỗi hash. Dùng tên `path` trong manifest khi hướng dẫn khôi phục file.
3. Ghi kết quả cho từng URL, gồm ngày kiểm, trạng thái tải, SHA-256 thực tế và kết luận **khớp / khác hash / lỗi tải**. Nếu hash khác, giữ snapshot hiện tại và báo Đăng để cùng xử lý thay vì đổi hash trong manifest.
4. TA đã xác nhận FIMI dùng được nếu nguồn khả dụng khi chấm. Chess và Accidents có mirror FIMI từng khớp hash. Mushroom, Retail và T10I4D100K hiện chỉ có link SPMF trong manifest. Ghi rõ nguồn đã xác minh cho ba tập này và điểm cần TA xác nhận nếu chưa chốt được ngoại lệ lưu trữ.

| Snapshot | File trong manifest | Nguồn cần kiểm |
|---|---|---|
| Chess | `chess.txt` | SPMF và mirror FIMI |
| Mushroom | `mushrooms.txt` | SPMF |
| Retail | `retail.txt` | SPMF |
| Accidents | `accidents.txt` | SPMF và mirror FIMI |
| T10I4D100K | `T10I4D100K.txt` | SPMF |

## Bàn giao cho Đăng

Gửi một bảng có các cột **Tập | URL đã thử | Ngày kiểm | SHA-256 thực tế | Kết luận**, kèm danh sách điểm còn vướng. Nếu cần sửa đường dẫn, mở PR cập nhật README hoặc manifest, chỉ dùng URL đã tải được và kiểm đúng snapshot. Giữ file dữ liệu lớn ngoài Git. Phần xác minh nguồn tải được theo dõi trong [checklist nộp bài](superpowers/plans/2026-11-26-submission-checklist.md).
