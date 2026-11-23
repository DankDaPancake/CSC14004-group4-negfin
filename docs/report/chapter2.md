# Chương 2. Đánh giá thực nghiệm negFIN và đối chiếu SPMF

Chương này tách hai campaign: Baseline–Optimized ngày 19-11-2026 (1.560 lượt hợp lệ, gói 110 tệp khớp SHA-256, loại 5 dòng trial Chess không ghép cặp) và **SPMF NegFIN–Julia Optimized đo mới ngày 22-11-2026** (210 lượt cold chính, 35 cấu hình đủ kiểm chứng). Hai nguồn không được ghép thành phép so ba bên hay dùng lại thời gian Julia cũ. Mục 2.1–2.6 giữ số liệu Baseline–Optimized; mục 2.7 trình bày campaign SPMF mới.

## 2.1. Mục tiêu

Chương này so sánh hai biến thể Baseline và Optimized của negFIN trong cùng môi trường, cùng snapshot dữ liệu, cùng minsup và cùng cài đặt harness. Mục tiêu là xác nhận tính nhất quán output, đo thời gian thực thi warm/cold, theo dõi peak RSS và xem khả năng mở rộng theo kích thước đầu vào. Kết quả không được ghép với các benchmark cũ khác máy hoặc khác commit.

## 2.2. Thiết lập thực nghiệm

Bảng I tóm tắt môi trường và cấu hình đo.

**Bảng I.** Môi trường và cấu hình đo

| Hạng mục | Thiết lập |
|---|---|
| Hệ điều hành | Windows 11 Pro, build 26200 |
| CPU | Intel Core i5-13600K, 20 logical CPUs |
| RAM | 34,088,599,552 bytes |
| Julia | 1.12.0, một thread |
| Dữ liệu | 5 snapshot trong `data/benchmark/manifest.toml`; SHA256 được kiểm trước đo |
| Warm | đo trong process sau warm-up, tách `count` và `write` |
| Cold | CLI chạy trong process con; wall bao gồm startup/JIT/I/O |
| Peak memory | RSS tối đa của child process, bao gồm runtime |
| Số lần lặp cho mỗi biến thể | 5 cho từng chế độ warm count/write, 3 cho cold, ở cả hai phạm vi |
| Output limit | 2 GiB theo config cho CLI; lỗi/cap/timeout không tính là phép đo thành công |

Hai biến thể dùng cùng các mức minsup đã chọn và cùng giới hạn chạy. Mã harness tại thời điểm đo là `7f122e9`. [Phụ lục kết quả](../validation/benchmark-baseline-optimized-results.md) ghi số giao dịch, checksum từng snapshot và cấu hình tái lập. Bảng II tóm tắt số cấu hình và số lượt đo.

**Bảng II.** Số cấu hình ghép cặp và số lượt đo hợp lệ

| Phạm vi | Điều kiện ghép cặp | Cold mỗi biến thể | Warm count mỗi biến thể | Warm write mỗi biến thể |
|---|---:|---:|---:|---:|
| Toàn tập | 35 | 105 | 175 | 175 |
| Scalability | 25 | 75 | 125 | 125 |

Trong mỗi cấu hình và chế độ xuất, các lượt hợp lệ có cùng checksum đầu vào, số giao dịch, ngưỡng support tuyệt đối và số mẫu giữa hai biến thể. Số byte đầu ra CLI cũng khớp ở cả 60 cấu hình cold. Kiểm chứng trên từng itemset và support được ghi riêng trong [báo cáo pilot](../validation/optimized-pilot.md).

## 2.3. Kết quả cold toàn tập

Trong Bảng III, hai ô đầu là median `cold wall (giây) / peak RSS (MiB)`, ba lần chạy. Cột warm write là median `phases_total_seconds` (giây) cho `emit_mode=write` sau warm-up, thứ tự Baseline / Optimized. Pattern count và output size giống nhau giữa hai variant ở mọi điều kiện full-data.

**Bảng III.** Kết quả cold và warm write trên toàn tập (median ba lần cold, năm lần warm)

| Dataset | minsup | Baseline cold sec / MiB | Optimized cold sec / MiB | Warm write sec B/O | Patterns | Output (bytes) |
|---|---:|---:|---:|---:|---:|---:|
| Chess | 0.9 | 2.67 / 333.2 | 2.69 / 334.0 | 0.0082 / 0.0081 | 622 | 13,740 |
| Chess | 0.55 | 3.48 / 373.4 | 3.30 / 335.0 | 0.7168 / 0.4976 | 574,998 | 19,045,853 |
| Chess | 0.5 | 4.29 / 392.1 | 3.89 / 336.5 | 1.5975 / 1.1020 | 1,272,932 | 43,817,148 |
| Chess | 0.45 | 5.99 / 402.4 | 5.10 / 341.1 | 3.4233 / 2.4465 | 2,832,777 | 101,056,684 |
| Chess | 0.4 | 9.93 / 477.1 | 8.35 / 341.7 | 7.5886 / 5.6183 | 6,439,702 | 238,090,371 |
| Chess | 0.35 | 19.71 / 538.5 | 15.95 / 345.9 | 17.3788 / 13.3567 | 15,108,722 | 578,514,671 |
| Chess | 0.3 | 43.36 / 551.0 | 36.10 / 349.2 | 41.9165 / 33.5692 | 37,282,962 | 1,474,437,971 |
| Mushroom | 0.8 | 2.66 / 333.2 | 2.66 / 333.6 | 0.0093 / 0.0095 | 17 | 292 |
| Mushroom | 0.15 | 2.87 / 359.1 | 2.88 / 340.0 | 0.1349 / 0.1031 | 99,071 | 3,235,973 |
| Mushroom | 0.1 | 3.29 / 353.2 | 3.30 / 342.9 | 0.5827 / 0.4913 | 600,817 | 21,033,170 |
| Mushroom | 0.07 | 3.68 / 355.2 | 3.48 / 345.6 | 0.9286 / 0.7706 | 970,105 | 33,704,732 |
| Mushroom | 0.05 | 6.34 / 364.4 | 5.92 / 347.0 | 3.5659 / 3.2608 | 4,137,547 | 152,436,989 |
| Mushroom | 0.03 | 12.96 / 394.0 | 12.62 / 350.2 | 10.3798 / 9.8660 | 12,372,681 | 468,989,540 |
| Mushroom | 0.02 | 21.99 / 398.5 | 20.97 / 356.4 | 19.1503 / 18.4239 | 22,840,275 | 882,487,559 |
| Accidents | 0.9 | 4.69 / 713.1 | 4.51 / 711.2 | 0.7743 / 0.7580 | 31 | 643 |
| Accidents | 0.6 | 5.65 / 884.5 | 5.53 / 892.4 | 1.7277 / 1.7496 | 2,074 | 53,439 |
| Accidents | 0.45 | 7.39 / 1,203.3 | 6.35 / 1,142.4 | 3.5570 / 2.4839 | 16,123 | 465,149 |
| Accidents | 0.35 | 9.86 / 1,244.4 | 6.98 / 1,295.7 | 6.0449 / 3.2801 | 68,222 | 2,130,894 |
| Accidents | 0.3 | 13.55 / 1,433.8 | 7.66 / 1,342.0 | 10.2462 / 3.7100 | 149,545 | 4,868,487 |
| Accidents | 0.25 | 24.18 / 2,019.1 | 9.44 / 1,811.8 | 20.1684 / 5.3281 | 346,525 | 11,596,463 |
| Accidents | 0.2 | 49.54 / 2,720.1 | 12.76 / 2,594.8 | 47.1705 / 9.3931 | 889,883 | 30,935,294 |
| Retail | 0.01 | 3.08 / 457.6 | 3.07 / 402.4 | 0.1751 / 0.1442 | 159 | 2,718 |
| Retail | 0.006 | 3.90 / 546.5 | 3.29 / 476.5 | 0.7718 / 0.3114 | 417 | 7,009 |
| Retail | 0.005 | 4.34 / 573.8 | 3.49 / 513.2 | 1.1532 / 0.4586 | 580 | 9,798 |
| Retail | 0.004 | 5.37 / 644.7 | 3.88 / 569.7 | 2.1687 / 0.7027 | 831 | 14,079 |
| Retail | 0.003 | 8.30 / 822.1 | 4.54 / 782.2 | 4.6461 / 1.3191 | 1,393 | 23,758 |
| Retail | 0.002 | 16.43 / 1,194.5 | 7.37 / 1,040.3 | 12.4458 / 2.8818 | 2,691 | 46,314 |
| Retail | 0.001 | 37.97 / 1,934.2 | 11.88 / 2,082.9 | 37.5366 / 8.6906 | 7,589 | 134,198 |
| T10I4D100K | 0.02 | 5.62 / 605.9 | 3.92 / 715.5 | 2.6584 / 0.9636 | 155 | 2,304 |
| T10I4D100K | 0.015 | 8.64 / 796.3 | 4.68 / 879.6 | 6.2521 / 1.5766 | 237 | 3,521 |
| T10I4D100K | 0.01 | 14.63 / 1,186.4 | 5.72 / 1,281.9 | 13.3938 / 2.5656 | 385 | 5,769 |
| T10I4D100K | 0.008 | 17.63 / 1,285.9 | 6.35 / 1,487.9 | 16.7749 / 3.4497 | 494 | 7,467 |
| T10I4D100K | 0.006 | 20.28 / 1,343.3 | 7.40 / 1,650.8 | 19.6995 / 4.1554 | 772 | 12,418 |
| T10I4D100K | 0.004 | 23.86 / 1,417.9 | 8.63 / 1,789.4 | 22.4543 / 4.8258 | 2,001 | 36,907 |
| T10I4D100K | 0.002 | 28.49 / 1,503.5 | 9.68 / 1,895.7 | 26.7983 / 5.8002 | 13,255 | 303,364 |

## 2.4. Scalability

Mỗi tập dữ liệu được đo ở các phần tiền tố 10%, 25%, 50%, 75% và 100%. Mỗi cặp Baseline–Optimized dùng cùng một tập con có cùng SHA-256. Bảng IV ghi median cold wall và peak RSS; số mẫu khớp giữa hai biến thể ở mọi điểm.

**Bảng IV.** Scalability theo phần tiền tố dữ liệu (median ba lần cold)

| Dataset / minsup | Fraction | Patterns | Baseline sec / MiB | Optimized sec / MiB |
|---|---:|---:|---:|---:|
| Chess / 0.99 | 10% | 81,919 | 2.88 / 337.8 | 2.87 / 335.6 |
|  | 25% | 1,023 | 2.76 / 333.5 | 2.68 / 333.9 |
|  | 50% | 95 | 2.87 / 332.4 | 2.67 / 334.1 |
|  | 75% | 31 | 2.89 / 333.6 | 2.69 / 332.8 |
|  | 100% | 9 | 2.90 / 333.6 | 2.68 / 333.4 |
| Mushroom / 0.2 | 10% | 835,583 | 3.50 / 336.5 | 3.30 / 336.1 |
|  | 25% | 519,999 | 3.28 / 335.6 | 3.07 / 334.7 |
|  | 50% | 340,975 | 3.29 / 337.1 | 3.07 / 333.6 |
|  | 75% | 77,007 | 2.86 / 338.4 | 2.88 / 335.2 |
|  | 100% | 53,337 | 2.89 / 346.8 | 2.86 / 337.0 |
| Retail / 0.004 | 10% | 1,024 | 3.07 / 393.9 | 2.87 / 373.7 |
|  | 25% | 984 | 3.47 / 436.2 | 2.91 / 396.1 |
|  | 50% | 871 | 4.13 / 424.4 | 3.26 / 430.7 |
|  | 75% | 806 | 4.69 / 516.1 | 3.47 / 484.9 |
|  | 100% | 831 | 5.51 / 648.1 | 3.71 / 569.8 |
| Accidents / 0.25 | 10% | 341,911 | 6.62 / 634.0 | 3.96 / 558.5 |
|  | 25% | 340,138 | 9.88 / 936.3 | 5.08 / 865.5 |
|  | 50% | 357,049 | 14.60 / 1,300.8 | 6.73 / 1,191.8 |
|  | 75% | 341,431 | 19.04 / 1,725.4 | 8.00 / 1,451.7 |
|  | 100% | 346,525 | 23.54 / 1,949.6 | 9.46 / 1,753.9 |
| T10I4D100K / 0.004 | 10% | 2,185 | 4.69 / 543.0 | 3.30 / 478.8 |
|  | 25% | 2,053 | 7.78 / 743.2 | 4.51 / 733.2 |
|  | 50% | 2,004 | 12.94 / 1,216.9 | 5.75 / 1,112.7 |
|  | 75% | 2,020 | 18.02 / 1,213.3 | 6.94 / 1,479.3 |
|  | 100% | 2,001 | 23.97 / 1,410.3 | 8.83 / 1,789.2 |

### Nhận xét trọng tâm: T10I4D100K

Ở T10I4D100K, Optimized có median cold wall thấp hơn ở cả năm kích thước. Peak RSS giảm ở 10–50% và tăng ở 75–100%. Tại 100% và minsup 0,004, thời gian giảm từ 23,97 xuống 8,83 giây trong khi RSS tăng từ 1.410,3 lên 1.789,2 MiB (khoảng 27%). Trong lượt toàn tập ở minsup 0,002, thời gian giảm từ 28,49 xuống 9,68 giây và RSS tăng từ 1.503,5 lên 1.895,7 MiB. [Biểu đồ scalability](../validation/figures/baseline-optimized-scalability.html) thể hiện hai chỉ số trên T10I4D100K và Accidents.

## 2.5. Thảo luận

1. Median cold wall của Optimized thấp hơn ở 32/35 cấu hình toàn tập và 24/25 cấu hình scalability. Median peak RSS thấp hơn ở 23/35 và 20/25 cấu hình tương ứng. Đây là số cấu hình theo chiều chênh lệch trên một máy, với ba lần lặp cold mỗi điểm.
2. Hai mức tăng tốc lớn nhất trong lượt toàn tập là Accidents minsup 0,2 (3,88×) và Retail minsup 0,001 (3,20×). Ba lượt cold của Accidents nằm trong 49,24–51,77 giây với Baseline và 12,62–12,88 giây với Optimized. Với một số mức minsup cao, chênh lệch chỉ vài phần trăm giây và cần thêm lần lặp để đánh giá.
3. Có hai hướng thử tiếp. Đo heap theo giai đoạn và thử lưu các bitmap ít bit bật bằng cấu trúc thưa để xem có giảm RSS của T10I4D100K. Đo riêng chi phí ghi kết quả và thử ghi theo lô trên Chess và Mushroom, nơi đầu ra có thể lên tới hàng trăm MiB hoặc hơn. Đối chiếu lại từng itemset và support trước khi so hiệu năng.

## 2.6. Hạn chế và khả năng tái lập

- `Chess` scale dùng minsup 0.99 để tránh mức 0.45 sinh >5M patterns chỉ trên 10% prefix. Counts giảm không đơn điệu do prefix đầu vào không đại diện phân phối toàn tập; đây không phải phép đo output volume cố định.
- `Mushroom` scale dùng minsup 0.2; mức cũ 0.15 tạo 3.44M patterns ở 10% và không được dùng trong paired scale run.
- Gói đã giải nén tại `results/benchmark-baseline-optimized-20261119/` có 5 dòng warm count thử của Baseline ở Chess 10%, minsup 0,45, trong run `20261119-180657`. Loại đúng 5 dòng này khi tổng hợp; các lượt khác trong cùng thư mục vẫn được dùng. Ở minsup 0,99, Chess 10% có đủ 5 lượt warm count mỗi biến thể.
- Dữ liệu thô, config, thông tin máy, checksum và log được lưu ngoài Git. Xem [hướng dẫn bàn giao](../validation/benchmark-handoff.md) để xác minh gói và tái tạo biểu đồ.

Bảng chi tiết cold toàn dataset và subset SHA256: [benchmark results appendix](../validation/benchmark-baseline-optimized-results.md).

## 2.7. Đối chiếu mới với SPMF NegFIN

### 2.7.1. Thiết lập và tính đúng

Campaign ngày 22-11-2026 đo **SPMF 2.69 / Temurin 25.0.5.1+2** và **Julia 1.12.0 Optimized** trên cùng máy ở Bảng I, cùng năm snapshot và toàn bộ 35 mức minsup của Bảng III. Mỗi implementation có ba process mới mỗi điểm, tổng cộng 210 lượt chính; 18 lượt pilot tách riêng. Thứ tự lần 1/3 là SPMF→Julia, lần 2 Julia→SPMF, chạy tuần tự. Julia dùng `--startup-file=no --threads=1`; Java dùng `-XX:ActiveProcessorCount=1 -Xmx4g`. Heap Java không phải quota RSS tương đương.

Timer monotonic bao gồm startup/JIT/đọc/mining/ghi/exit; không xóa filesystem cache. Peak RSS là native Windows peak working set của child process, không phải allocation hay heap. Giới hạn mỗi process: 1.800 giây, output 2 GiB, RSS 8 GiB; dung lượng đĩa tối thiểu 20 GiB. Validation ngoài timer dùng external sort, không nạp toàn bộ output vào RAM.

Pilot đạt 9/9 điều kiện, gồm toy, fixture rìa ngưỡng, năm mức dễ và hai output lớn. Với mỗi cấu hình chính, lần đầu so chính xác từng itemset/support sau canonical hóa và phát hiện duplicate; hai lần sau phải khớp count/digest. **35/35 cấu hình đạt**, không có missing/extra/support mismatch. Support tuyệt đối là `ceil(minsup_decimal × N)` chính xác. Fixture N=100/minsup=0.07 phát hiện SPMF double ceiling=8 thay vì7; mapping CLI được ghi rõ và so với output tính tay. **35 mức thực không cần đổi chuỗi minsup**. Xem [phụ lục mới](../validation/benchmark-spmf-julia-results.md) cho threshold từng điểm và bằng chứng.

Provenance: git base `70ad97c`, working tree chưa commit; fingerprint `0490b0be675929b57d3f47a3e823c8ed1fb91e856b46127efc162077a98dddd4`. Source/config/hash, argv, logs và measurement/validation JSON nằm trong gói evidence riêng. Không gọi đây là revision benchmark sạch đã commit.

### 2.7.2. Kết quả

**Bảng V.** Mức minsup thấp nhất của mỗi dataset, median [min–max] ba lần cold mới. Bảng đầy đủ 35 điểm ở phụ lục; RSS là median MiB theo thứ tự SPMF / Julia.

| Dataset | minsup | Patterns | SPMF wall s [min–max] | Julia wall s [min–max] | RSS MiB S/J |
|---|---:|---:|---|---|---:|
| Chess | 0.3 | 37,282,962 | 5.154 [4.745–5.963] | 53.578 [36.420–57.130] | 204.2 / 349.8 |
| Mushroom | 0.02 | 22,840,275 | 2.897 [2.885–3.105] | 20.069 [19.938–20.283] | 204.4 / 356.9 |
| Retail | 0.001 | 7,589 | 3.386 [3.377–3.527] | 11.617 [11.389–11.938] | 369.5 / 2084.4 |
| Accidents | 0.2 | 889,883 | 6.696 [6.464–6.703] | 12.182 [12.181–12.332] | 352.1 / 2618.8 |
| T10I4D100K | 0.002 | 13,255 | 2.514 [2.485–2.541] | 9.222 [9.201–9.246] | 341.8 / 1937.3 |

SPMF có median whole-process wall và peak working set thấp hơn ở cả35 điểm. Tỉ số median Julia/SPMF nằm trong **1,82–14,60×**, mô tả phép đo end-to-end trên máy này, không phải tăng tốc mining-only hay kết luận Java tốt hơn Julia nói chung. Ở support cao, startup/JIT có thể chiếm phần đáng kể; chưa có profiling theo pha để tách nguyên nhân.

**Bảng VI.** Peak working set tại mức thứ tư trong bảy minsup, median ba lần mới (MiB).

| Dataset | minsup | SPMF | Julia Optimized |
|---|---:|---:|---:|
| Chess | 0.45 | 199.6 | 340.8 |
| Mushroom | 0.07 | 195.8 | 344.0 |
| Retail | 0.004 | 227.5 | 578.9 |
| Accidents | 0.35 | 256.7 | 1275.8 |
| T10I4D100K | 0.008 | 296.9 | 1400.4 |

### 2.7.3. Hình, thảo luận và giới hạn

Bộ hình local `results/spmf-julia-final-20261122/figures/` có 11 hình PNG/PDF kèm `captions.md` và `figure-data.csv`: 5 runtime–minsup (median và min–max), 5 itemsets–minsup (cùng output đã xác minh), 1 RSS tại mức thứ tư. Không đưa file sinh tự động vào Git; các đường dẫn này không có sẵn trong clone mới, nhận qua gói bàn giao local.

- **Caption runtime:** “Median ba process cold mới SPMF NegFIN và Julia Optimized; whisker min–max; whole-process wall gồm startup/JIT/read/write; support giảm từ trái sang phải.”
- **Caption itemsets:** “Số frequent itemset khớp giữa hai implementation sau so itemset/support lần đầu và count/digest ở hai lần sau; không phải số đo thời gian.”
- **Caption RSS:** “Median native Windows peak working set của ba process tại minsup thứ tư; whisker min–max; Java heap không phải RSS.”
- **Caption scalability cũ:** “Baseline–Optimized ngày19-11-2026, các prefix10/25/50/75/100%; không phải campaign SPMF mới, không ghép số đo giữa hai nguồn.”

Chess/Mushroom là trường hợp output lớn: mức thấp nhất sinh37,28/22,84 triệu itemset. Chi phí format/ghi/duyệt output có thể ảnh hưởng mạnh; chưa đo riêng nên không quy kết toàn bộ chênh lệch cho mining. Retail/T10I4D100K sinh ít mẫu hơn nhưng RSS Julia tăng khi hạ support; đây chưa phải bằng chứng nhân quả về bitmap/heap. Các ý tưởng profiling heap, cấu trúc thưa, ghi theo lô và thí nghiệm chiều dài transaction **vẫn chờ quyết định của Đăng**, không được trình bày là tối ưu đã duyệt hoặc thực hiện.

Giữ nguyên trade-off T10I4D100K trong mục2.4: Optimized nhanh hơn Baseline nhưng RSS có thể cao hơn ở prefix75–100%. Kết quả SPMF mới không phủ định hoặc thay thế phép so cũ. Chưa đo scalability SPMF.

Ba lần lặp trên một máy chưa đủ suy luận thống kê; riêng Chess0,3 Julia có khoảng36,420–57,130s, không loại mẫu chậm. Campaign bị ngắt do giới hạn harness2 giờ rồi tiếp tục từng cấu hình theo checkpoint, cùng fingerprint, không thay số đo đã lưu. Các pilot thất bại trước v3 được giữ riêng. Chưa xác minh mirror Hugging Face/Kaggle khớp byte/hash; giữ nguồn SPMF và manifest, không dùng dataset cùng tên nhưng khác encoding. Gói evidence không chứa original itemset output đã xóa sau validation; cần chạy lại để so byte một lần nữa. Xem [hướng dẫn bàn giao](../validation/benchmark-handoff.md); chưa gửi gói ra ngoài và chưa tạo PR.
