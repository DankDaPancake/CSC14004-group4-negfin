# Chương 2. Đánh giá thực nghiệm Baseline và Optimized

> **Trạng thái:** bản nháp số liệu ngày 19-11-2026. Bảng cold/warm/scalability được tổng hợp từ raw runs cùng máy. Đã tạo biểu đồ scalability HTML/SVG; chưa tạo biểu đồ ladder cold. ZIP bàn giao local đã tạo và kiểm SHA256; chưa có PR.

## 2.1. Mục tiêu

Chương này so sánh hai biến thể Baseline và Optimized của negFIN trong cùng môi trường, cùng snapshot dữ liệu, cùng minsup và cùng cài đặt harness. Mục tiêu là xác nhận tính nhất quán output, đo thời gian thực thi warm/cold, theo dõi peak RSS và xem khả năng mở rộng theo kích thước đầu vào. Kết quả không được ghép với các benchmark cũ khác máy hoặc khác commit.

## 2.2. Thiết lập thực nghiệm

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
| Repetitions | warm 5 lần, cold 3 lần; scalability warm 5, cold 3 |
| Output limit | 2 GiB theo config cho CLI; lỗi/cap/timeout không tính là phép đo thành công |

Nguồn dữ liệu, transaction count và hash đầy đủ được ghi trong [phụ lục raw results](../validation/benchmark-baseline-optimized-results.md). Cấu hình paired nằm tại `bench/config-baseline-20261119.toml` và `bench/config-optimized-20261119.toml`; hai file giống nhau trừ trường `variant` và các minsup scalability chung đã hiệu chỉnh sau khi sàng lọc count-only.

## 2.3. Kết quả cold toàn tập

Hai ô đầu là median `cold wall (giây) / peak RSS (MiB)`, ba lần chạy. Cột warm write là median `phases_total_seconds` (giây) cho `emit_mode=write` sau warm-up, thứ tự Baseline / Optimized. Pattern count và output size giống nhau giữa hai variant ở mọi điều kiện full-data.

| Dataset | minsup | Baseline cold sec / MiB | Optimized cold sec / MiB | Warm write sec B/O | Patterns | Output (bytes) |
|---|---:|---:|---:|---:|---:|---:|
| Chess | 0.9 | 2.67 / 333.2 | 2.69 / 334.0 | 0.0082 / 0.0081 | 622 | 13,740 |
| Chess | 0.55 | 3.48 / 373.4 | 3.30 / 335.0 | 0.7168 / 0.4976 | 574,998 | 19,045,853 |
| Chess | 0.5 | 4.29 / 392.1 | 3.89 / 336.5 | 1.5975 / 1.1020 | 1,272,932 | 43,817,148 |
| Chess | 0.45 | 5.99 / 402.4 | 5.10 / 341.1 | 3.4233 / 2.4465 | 2,832,777 | 101,056,684 |
| Chess | 0.4 | 9.93 / 477.1 | 8.35 / 341.7 | 7.5886 / 5.6183 | 6,439,702 | 238,090,371 |
| Chess | 0.35 | 19.71 / 538.5 | 15.95 / 345.9 | 17.3788 / 13.3567 | 15,108,722 | 578,514,671 |
| Chess | 0.3 | 43.36 / 551.0 | 36.10 / 349.2 | 41.9165 / 33.5692 | 37,282,962 | 1,474,437,971 |
| Mushroom | 0.8 | 2.66 / 333.2 | 2.66 / 333.6 | 0.0095 / 0.0095 | 17 | 292 |
| Mushroom | 0.15 | 2.87 / 359.1 | 2.88 / 340.0 | 0.1348 / 0.1031 | 99,071 | 3,235,973 |
| Mushroom | 0.1 | 3.29 / 353.2 | 3.30 / 342.9 | 0.5764 / 0.4913 | 600,817 | 21,033,170 |
| Mushroom | 0.07 | 3.68 / 355.2 | 3.48 / 345.6 | 0.9447 / 0.7706 | 970,105 | 33,704,732 |
| Mushroom | 0.05 | 6.34 / 364.4 | 5.92 / 347.0 | 3.5802 / 3.2608 | 4,137,547 | 152,436,989 |
| Mushroom | 0.03 | 12.96 / 394.0 | 12.62 / 350.2 | 10.4256 / 9.8660 | 12,372,681 | 468,989,540 |
| Mushroom | 0.02 | 21.99 / 398.5 | 20.97 / 356.4 | 19.2417 / 18.4239 | 22,840,275 | 882,487,559 |
| Accidents | 0.9 | 4.69 / 713.1 | 4.51 / 711.2 | 0.7776 / 0.7580 | 31 | 643 |
| Accidents | 0.6 | 5.65 / 884.5 | 5.53 / 892.4 | 1.7368 / 1.7496 | 2,074 | 53,439 |
| Accidents | 0.45 | 7.39 / 1,203.3 | 6.35 / 1,142.4 | 3.5167 / 2.4839 | 16,123 | 465,149 |
| Accidents | 0.35 | 9.86 / 1,244.4 | 6.98 / 1,295.7 | 6.0349 / 3.2801 | 68,222 | 2,130,894 |
| Accidents | 0.3 | 13.55 / 1,433.8 | 7.66 / 1,342.0 | 10.0843 / 3.7100 | 149,545 | 4,868,487 |
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

Scalability fractions are 10%, 25%, 50%, 75%, and 100% for each of five datasets. Each pair uses the same prefix subset SHA256. The table reports cold wall and RSS medians; all pattern counts match between variants.

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

Optimized nhanh hơn ở cả năm fractions, nhưng RSS không giảm đồng đều. Tại 10–50%, Optimized RSS bằng hoặc thấp hơn nhẹ; 75% tăng khoảng 266 MiB, 100% tăng khoảng 379 MiB (khoảng 27%). Dù đỉnh khoảng 1.79 GiB thấp đáng kể so với 32 GiB RAM vật lý của máy, đây vẫn là trade-off thực, không phải cải thiện bộ nhớ. Với full data ở minsup 0.002, cold Optimized median khoảng 1.90 GiB so với Baseline 1.47 GiB, nhưng nhanh hơn khoảng 2.9×.

## 2.5. Thảo luận

1. Output giữa Baseline và Optimized khớp số patterns và output bytes trên từng full-data selected minsup; trên scalability, hashes và counts khớp ở toàn bộ subset.
2. Cải thiện runtime lớn nhất xuất hiện ở workload nhiều output: Retail 0.001 cold 11.88s so với 37.97s; Accidents 0.2 là 12.76s so với 49.54s. Ở minsup cao, startup/JIT/I/O chiếm tỷ lệ lớn hơn và chênh lệch nhỏ.
3. Bộ nhớ tùy workload. Optimized thường giảm RSS trên Chess/Mushroom và nhiều mức Accidents/Retail, nhưng có thể tăng trên T10I4D100K khi minsup giảm. Không suy diễn kết quả một dataset thành đặc tính chung.
4. Câu hỏi thảo luận với Đăng: phần tăng RSS của T10I4D100K có thể liên quan đến cách biểu diễn dữ liệu/bitmap ở mức minsup thấp không? Cần benchmark lặp lại trên máy khác hoặc profiler allocation/heap để kiểm tra giả thuyết này; chưa có bằng chứng nhân quả từ thí nghiệm hiện tại.

## 2.6. Hạn chế và khả năng tái lập

- `Chess` scale dùng minsup 0.99 để tránh mức 0.45 sinh >5M patterns chỉ trên 10% prefix. Counts giảm không đơn điệu do prefix đầu vào không đại diện phân phối toàn tập; đây không phải phép đo output volume cố định.
- `Mushroom` scale dùng minsup 0.2; mức cũ 0.15 tạo 3.44M patterns ở 10% và không được dùng trong paired scale run.
- Baseline full warm primary run có đủ count và write rows cho cả 35 dataset/minsup pairs. Harness tự giảm Chess 10% count từ 5 xuống 3 repetitions sau khi lần đầu vượt 60 giây; đây là hành vi đã ghi nhận trong raw CSV.
- Một lần chạy scale Baseline đầu tiên dừng ở Chess 10% count và chỉ lưu 5 rows count-only; không dùng các rows đó như phép đo đầy đủ.
- Dữ liệu raw, subset hashes, environment, config và logs ở `results/handoff/benchmark-baseline-optimized-20261119/` (bị Git ignore). ZIP local `results/handoff/benchmark-baseline-optimized-20261119.zip` đã tạo và kiểm tra toàn bộ checksum của 110 file sau giải nén; byte size cùng SHA256 được ghi trong [handoff record](../validation/benchmark-handoff.md). ZIP không chứa dataset hoặc output itemset toàn tập.
- Biểu đồ scalability HTML/SVG có thể tái tạo bằng `python -I docs/validation/render-baseline-optimized.py results/handoff/benchmark-baseline-optimized-20261119/full-run --output docs/validation/figures/baseline-optimized-scalability.html`. Biểu đồ ladder warm/cold còn thiếu. Legacy matplotlib plotting test chưa chạy được vì runtime không có matplotlib; renderer paired mới có 3 test focused pass.

Bảng chi tiết cold toàn dataset và subset SHA256: [benchmark results appendix](../validation/benchmark-baseline-optimized-results.md).
