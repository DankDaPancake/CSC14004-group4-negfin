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

Kết quả và Chương 2 đã vào `main` qua [PR #16](https://github.com/DankDaPancake/CSC14004-group4-negfin/pull/16). Gói nhận được tại `results/spmf-julia-handoff-20261122/` chứa `evidence/raw-evidence.zip`, `results/summary.csv` và `results/figures/` (11 hình PNG/PDF, caption và dữ liệu hình). Đã xác minh 35 checksum của gói ngoài và 1.136 checksum bên trong ZIP. Gói nằm ngoài Git.

Đăng đã tính lại median và min–max từ 210 lượt chính. Cả 70 dòng summary khớp dữ liệu hình. Bảng V và VI của Chương 2 cùng 35 dòng phụ lục khớp sau làm tròn. Bằng chứng của 35 cấu hình ghi nhận itemset/support khớp ở cặp đầu và digest chuẩn hóa khớp ở hai lần lặp tiếp theo. SPMF có median thời gian toàn tiến trình và peak working set thấp hơn tại cả 35 điểm trên máy đo. Phạm vi thời gian gồm khởi động, JIT, đọc và ghi.

Tiến dùng hình và caption trong gói để cập nhật bản IEEE, tóm tắt và kết luận. Dùng riêng kết quả scalability Baseline–Optimized ngày 19-11 cho phần về kích thước đầu vào; đợt 22-11 đo SPMF–Julia trên toàn tập. Mirror HF/Kaggle khớp hash vẫn chưa được xác minh.

## Bổ sung của Đăng

- [Pilot độ dài giao dịch](transaction-length-pilot.md) hoàn tất 24 lượt warm count ở bốn độ dài. Khi tăng từ 10 lên 20 item/giao dịch, cả hai mức đều có 512 mẫu, còn số node BMC tăng từ 86.572 lên 183.235 và thời gian tăng ở cả hai biến thể. Dùng ví dụ này cho phần dữ liệu tổng hợp trong Chương 2. CSV từng lượt nằm tại `results/transaction-length-pilot-20261125.csv`.
- Dùng hai đề xuất trong pilot cho phần hướng phát triển: thử bitmap thưa sau khi định vị chi phí heap và thử ghi theo lô sau khi đo riêng chi phí xuất. Đây là các thí nghiệm tiếp theo để đánh giá bộ nhớ và thời gian.
