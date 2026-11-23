# Thông tin bàn giao benchmark Baseline

Gói của Hiếu được lưu local tại `results/handoff/benchmark-baseline-20261113/` và `results/handoff/benchmark-baseline-20261113.zip`. Cả hai nằm trong thư mục `results/` được Git bỏ qua: **không có trong clone mới**, cần sao lưu/chia sẻ riêng để các thành viên tái lập. File ZIP có SHA256 `e046789c3e4958fd1ef9a5134bfec3b116488319f82ebcc24f8ac6e3a429e9bb`.

## Nội dung

- `README.md`: hướng dẫn của Hiếu, nguồn, lệnh, phạm vi đo và phần còn thiếu.
- `full-run/20261113-154220/`: `runs.csv` (581 lượt), `phases.csv` (2.905 dòng), `summary.csv` và `env.toml`. Đã kiểm tra tất cả 581 trạng thái là `ok`.
- `pilots/`: 8 lượt pilot cùng kết quả, stats và stderr; Mushroom 0,01 chạm giới hạn output, không phải số đo hoàn tất.
- `config/`: config và manifest tại commit đo, SHA256 dataset và diff cấu hình pilot chưa commit; `logs/`: stdout, stderr và sổ quyết định.
- `overhead/`: script và số đo so sánh phase hook; các đường dẫn tuyệt đối trong script là của máy Hiếu và cần điều chỉnh khi chạy máy khác.

Lượt chính chạy tại commit `3ecd0c1ce032e42b271100f2531260d53dde2d65`, working tree sạch, Julia 1.12.0 một luồng, Windows 11 và i5-13600K. Cold bao gồm startup/JIT/I/O; warm không bao gồm các phần đó. Tổng cấp phát không phải peak RSS. Số liệu được ghi trước các sửa đổi sau lượt chạy; xem [báo cáo gốc](benchmark-baseline.md) và README trong gói để biết giới hạn.

## Gói bàn giao Baseline vs Optimized (19-11-2026)

Bản đã giải nén dùng để cập nhật [Chương 2](../report/chapter2.md) nằm tại `results/benchmark-baseline-optimized-20261119/` trong checkout chính. Đã kiểm lại 110 checksum trong `SHA256SUMS.txt`. Có 1.565 dòng đo trong `full-run/*/runs.csv`; sau khi bỏ 5 dòng warm count thử của Baseline tại Chess 10%, minsup 0,45 (run `20261119-180657`), tập tổng hợp còn 1.560 lượt `ok`. Chess 10%, minsup 0,99 có đủ 5 lượt warm count cho mỗi biến thể. Giữ nguyên gói thô để đối chiếu checksum.

Từ thư mục gốc có thể tạo lại biểu đồ cold scalability vào thư mục kết quả local:

```powershell
python -I docs/validation/render-baseline-optimized.py results/benchmark-baseline-optimized-20261119/full-run --output results/baseline-optimized-scalability.html
```

Gói ZIP local: `results/handoff/benchmark-baseline-optimized-20261119.zip` (308,876 bytes), SHA256 `340244FA8AD98E63DBDFA1B78569F34A49C6B4096CA50AA24B68364EE720C64D`. ZIP có 110 file kèm `SHA256SUMS.txt`; đã giải nén vào thư mục xác minh mới, tính lại tất cả 110 checksum thành công và kiểm tra ZIP đọc được. Gói gồm config/manifest, README môi trường, raw `runs.csv`, `phases.csv`, `summary.csv`, `env.toml` cho các full runs và corrected scale runs, pilot summaries, Chapter 2 draft, report analysis, source renderer và HTML scalability figure. Gói không chứa dataset gốc, Julia runtime hay output itemset toàn tập. Năm dataset trong checkout phải tải lại/giữ riêng theo manifest khi chuyển máy.

Các lần chạy hoàn chỉnh cho mỗi variant: 35 full-data cold configs × 3 reps; 35 full-data warm pairs × 5 count + 5 write; 25 scalability fractions × 3 cold + 5 warm count/write. Minsup scale cuối: Chess 0.99, Mushroom 0.2, Retail 0.004, Accidents 0.25, T10I4D100K 0.004. Tất cả subset SHA256 khớp giữa hai variant. Trial Chess 10% ở minsup 0.45 vượt 5 triệu patterns và được dừng trước output; các dòng chạy thử được loại khỏi báo cáo.

## Kiểm tra bản sao local

Đã đối chiếu SHA256 của 292 file giữa thư mục bàn giao, bản local và từng entry trong ZIP; đã kiểm tra ZIP không lỗi. Năm file trong `data/benchmark/` của checkout chính khớp SHA256 với manifest bàn giao. ZIP không chứa dữ liệu benchmark gốc hoặc output itemset lớn; các file benchmark local không được Git theo dõi và vẫn cần sao lưu hoặc tải lại theo manifest khi chuyển máy.

Đã tính lại cold median từ ba lượt trong `runs.csv` cho Retail 0,001 (36,1647333 s), Chess 0,3 (41,6806076 s), Accidents 0,2 (49,9652722 s), khớp bảng báo cáo sau làm tròn. Đây là đối chiếu đại diện, chưa phải kiểm toán toàn bộ bảng.

Phần bàn giao benchmark Baseline vs Optimized đã đo scalability ở 10/25/50/75/100% cho cả năm dataset trên cùng máy; xem gói mới ở trên và [bản phân tích kết quả](benchmark-baseline-optimized-results.md). Gói baseline cũ `benchmark-baseline-20261113.zip` và giới hạn của nó vẫn được lưu giữ riêng, không ghép số liệu khác máy/commit vào phép so sánh paired. Chưa gửi liên lạc ra ngoài hoặc thực hiện handoff cho Đăng.

## Gói SPMF–Julia Optimized đo mới (22-11-2026)

Đã đo mới 210 lượt chính, 35/35 cấu hình đủ ba repetition mỗi implementation và kiểm chứng output; 18 lượt pilot riêng. Root evidence: `results/spmf-julia-cold-20261122-v3/`, fingerprint `0490b0be675929b57d3f47a3e823c8ed1fb91e856b46127efc162077a98dddd4`. Không trộn campaign Baseline–Optimized cũ hoặc pilot v1/v2.

- ZIP raw evidence local: `results/spmf-julia-package-20261122/raw-evidence.zip`.
- SHA-256: `d95cf909f53a2b31ac74175ebd16eabcd13b39636b5133abbcc1cedd529d8837`.
- **1.136 tệp** và `SHA256SUMS.txt`; đã kiểm ZIP integrity, giải nén thư mục mới và tính lại từng checksum. Có README, source/config/machine/runtime/input provenance, CSV, measurement/validation JSON, comparisons, logs/stats. Không có dataset, executable/jar hay output itemset lớn.
- Summary đầy đủ: `results/spmf-julia-final-20261122/summary.csv` và `summary.json` (35 cặp accepted, incomplete0). Min–max và độ chính xác gốc được giữ trong CSV.
- Hình: `results/spmf-julia-final-20261122/figures/`, 11 hình × PNG/PDF, `captions.md`, `figure-data.csv`. Đây là file sinh local/ignored, **không nằm trong clone mới và không được gộp vào ZIP raw evidence**; cần sao lưu riêng cùng ZIP. Có contact sheet ở thư mục final.
- Báo cáo: [phụ lục 35 điểm](benchmark-spmf-julia-results.md), [Chương2 mục2.7](../report/chapter2.md). Generated IEEE TeX/PDF không sửa.

README trong root evidence nêu timer whole-process (startup/JIT/read/write), peak working set khác heap/allocation, caps, exact-ceil CLI mapping chỉ cho boundary pilot, resume sau harness timeout và giới hạn ba lần lặp. Source đã đo là working tree dirty trên base `70ad97c`, không phải commit sạch. Output lớn được xóa sau khi validation durable: gói giữ digest/bằng chứng chứ không cho so lại original bytes nếu không chạy miners lại.

Bàn giao local đã chuẩn bị cho Tiến, **chưa gửi ra ngoài**, chưa commit/push/PR. Mirror HF/Kaggle khớp hash chưa thiết lập; giữ URL SPMF và manifest. Đề xuất tối ưu/độ dài transaction vẫn chờ quyết định của Đăng. Gói này hoàn tất phép đo full-data SPMF–Julia, không bổ sung scalability SPMF; scalability cũ và trade-off RSS T10I4D100K vẫn có provenance riêng.
