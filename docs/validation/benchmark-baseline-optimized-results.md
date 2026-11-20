# Benchmark Baseline vs Optimized (19-11-2026)

> **Cập nhật 20-11-2026.** Phân tích được tính từ raw CSV của các lần chạy cùng máy. Biểu đồ scalability dạng HTML/SVG được sinh bởi script thuần Python, không phụ thuộc matplotlib. Biểu đồ ladder warm/cold chưa sinh; PR chứa tài liệu này cùng kết quả đã mở, ZIP bàn giao local có SHA256 trong handoff.

## Phạm vi và cách đọc

Đo Baseline và Optimized bằng Julia 1.12.0, một Julia thread, trên Windows 11 Pro build 26200, Intel Core i5-13600K (20 logical CPUs), RAM 34,088,599,552 bytes. Checkout đo bắt đầu từ `34719b8bfec785dab15728cd2d013e2605a215ee`; mã benchmark/validator và báo cáo được lưu trong branch PR này. Dùng các snapshot dữ liệu đã kiểm SHA256 với `data/benchmark/manifest.toml`.

Warm là phép đo trong process sau warm-up; `count` không ghi output, `write` đo luồng phát output trong harness. Cold là tiến trình Julia con và `process_wall_seconds` bao gồm startup/JIT/I/O; `maxrss_bytes` là peak RSS tiến trình con (bao gồm runtime), không phải tổng allocation. `output_bytes` là output của CLI. Các lần timeout/output-cap/error không được tính là số liệu thành công; các run hợp lệ trong bảng dưới đều có 3 lần cold hoặc 5 lần warm, trừ run Baseline đầu tiên đã bị dừng và loại khỏi bảng.

### Trạng thái raw runs

| Variant | Full warm | Full cold | Scalability warm | Scalability cold | Lỗi trong run dùng báo cáo |
|---|---:|---:|---:|---:|---:|
| Baseline | 35 pairs × 2 modes × 5 (350 rows) | 35 cấu hình × 3 | 25 cấu hình × 5 hoàn tất; +5 count-only rows từ thử dừng, loại | 25 cấu hình × 3 | 0 |
| Optimized | 35 pairs × 2 modes × 5 (350 rows) | 35 cấu hình × 3 | 25 cấu hình × 5 | 25 cấu hình × 3 | 0 |

Baseline full warm chính có đủ `count` và `write`, mỗi mode 5 lần ở 35 dataset/minsup pairs (350 rows). Tổng 477 warm rows Baseline khi nhìn toàn thư mục gồm 127 rows của run cũ `20261119-175623` bị dừng trong warm Accidents; không gộp vào median. Optimized warm có đủ 350 rows.

Lượt Baseline full-data chính (`20261119-180657`) hoàn tất warm/cold. Thử scale đầu tiên trong run đó dừng sau 5 row Chess 10% count-only: minsup cũ 0.45 sinh ít nhất 5,000,001 patterns trên 320 transactions. Những rows đó được loại khỏi scale medians. Dùng cổng callback-only với cap 1,000,000 patterns trước khi chạy lại. Final paired scale minsup: Chess 0.99, Mushroom 0.2, Retail 0.004, Accidents 0.25, T10I4D100K 0.004. Hai variant có cùng SHA256 cho mỗi subset tại 10/25/50/75/100%.

Lượt Baseline cũ (`20261119-175623`) dừng giữa warm Accidents với 127 rows; được giữ riêng. Lượt Baseline full-data chính (`20261119-180657`) hoàn tất. Thử scalability đầu tiên (`20261119-180657`) dừng sau 5 row Chess 10% count-only: minsup cũ 0.45 sinh ít nhất 5,000,001 patterns trên 320 transactions. Không ghi output cho thử này và không coi rows đó là benchmark hoàn tất. Thay vì lặp lại, dùng cổng đếm callback-only cap 1,000,000 patterns trước khi chạy cả hai variant. Minsup scalability đã hiệu chỉnh giống nhau trong hai config: Chess 0.99, Mushroom 0.2, Retail 0.004, Accidents 0.25, T10I4D100K 0.004. Hai variant cùng SHA256 cho từng subset ở 10/25/50/75/100%.

## Full-dataset cold: median (3 lần)

RSS là MiB; output là bytes; `patterns` là số frequent itemsets. Thời gian và RSS được lấy trực tiếp từ cold CLI rows. Cột warm write thể hiện median `phases_total_seconds` cho `emit_mode=write` trong process đã warm-up (giây), thứ tự Baseline / Optimized. Đây là số liệu có sẵn cho tất cả các cặp; count-only rows không dùng thay thế write.

| Dataset | minsup | Baseline giây / RSS MiB | Optimized giây / RSS MiB | Warm write median (B/O giây) | Patterns | Output bytes |
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
| Accidents | 0.45 | 7.39 / 1,203.3 | 6.35 / 1,142.4 | 3.5170 / 2.4839 | 16,123 | 465,149 |
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

## Scalability cold: median (3 lần), mọi subset cùng SHA

| Dataset | Fraction | Patterns | Baseline giây / RSS MiB | Optimized giây / RSS MiB |
|---|---:|---:|---:|---:|
| Chess, minsup 0.99 | 10% | 81,919 | 2.88 / 337.8 | 2.87 / 335.6 |
|  | 25% | 1,023 | 2.76 / 333.5 | 2.68 / 333.9 |
|  | 50% | 95 | 2.87 / 332.4 | 2.67 / 334.1 |
|  | 75% | 31 | 2.89 / 333.6 | 2.69 / 332.8 |
|  | 100% | 9 | 2.90 / 333.6 | 2.68 / 333.4 |
| Mushroom, minsup 0.2 | 10% | 835,583 | 3.50 / 336.5 | 3.30 / 336.1 |
|  | 25% | 519,999 | 3.28 / 335.6 | 3.07 / 334.7 |
|  | 50% | 340,975 | 3.29 / 337.1 | 3.07 / 333.6 |
|  | 75% | 77,007 | 2.86 / 338.4 | 2.88 / 335.2 |
|  | 100% | 53,337 | 2.89 / 346.8 | 2.86 / 337.0 |
| Retail, minsup 0.004 | 10% | 1,024 | 3.07 / 393.9 | 2.87 / 373.7 |
|  | 25% | 984 | 3.47 / 436.2 | 2.91 / 396.1 |
|  | 50% | 871 | 4.13 / 424.4 | 3.26 / 430.7 |
|  | 75% | 806 | 4.69 / 516.1 | 3.47 / 484.9 |
|  | 100% | 831 | 5.51 / 648.1 | 3.71 / 569.8 |
| Accidents, minsup 0.25 | 10% | 341,911 | 6.62 / 634.0 | 3.96 / 558.5 |
|  | 25% | 340,138 | 9.88 / 936.3 | 5.08 / 865.5 |
|  | 50% | 357,049 | 14.60 / 1,300.8 | 6.73 / 1,191.8 |
|  | 75% | 341,431 | 19.04 / 1,725.4 | 8.00 / 1,451.7 |
|  | 100% | 346,525 | 23.54 / 1,949.6 | 9.46 / 1,753.9 |
| T10I4D100K, minsup 0.004 | 10% | 2,185 | 4.69 / 543.0 | 3.30 / 478.8 |
|  | 25% | 2,053 | 7.78 / 743.2 | 4.51 / 733.2 |
|  | 50% | 2,004 | 12.94 / 1,216.9 | 5.75 / 1,112.7 |
|  | 75% | 2,020 | 18.02 / 1,213.3 | 6.94 / 1,479.3 |
|  | 100% | 2,001 | 23.97 / 1,410.3 | 8.83 / 1,789.2 |

### T10I4D100K: memory trade-off

At the selected scalability minsup 0.004, Optimized reduces cold wall time at every fraction, from 4.69s to 3.30s at 10% and 23.97s to 8.83s at 100%. RSS is lower through 50%, but higher at 75% (+266 MiB, about 22%) and 100% (+379 MiB, about 27%). At minsup 0.002 in the full-data ladder, median peak RSS is 1,895.7 MiB for Optimized and 1,503.5 MiB for Baseline, with cold wall time falling from 28.49s to 9.68s.

At Accidents 100%, Optimized is faster (9.46s vs 23.54s) and has lower median RSS (1,753.9 MiB vs 1,949.6 MiB).

## Interpretation

- Pattern counts and CLI output bytes match between variants at every full-data selected condition listed. Every scalability subset hash matches across variants; pattern counts are equal at all 25 sizes.
- Optimized shows its clearest runtime advantage at lower minsup / higher output counts. For example, cold Retail 0.001 is 11.88s vs 37.97s, and Accidents 0.2 is 12.76s vs 49.54s. At the less demanding end, startup and I/O dominate, so runtimes are close.
- RSS is dataset- and workload-dependent. Optimized is consistently lower for Chess and Mushroom cold ladders, but T10I4D100K’s lower minsup increases Optimized RSS relative to Baseline. Highlight both throughput and memory; do not call the memory change a universal improvement.
- These are single-machine results from one Julia/OS/CPU setup. Cold RSS includes Julia runtime; small differences can be noise. The run used three repetitions per cold point, so ranges and medians should accompany claims in a publication.

## Limitations and incomplete work

- The original `scalability_minsup.Chess = 0.45` setting was unsafe even at 10%; the interrupted count-only probe exceeded 5M patterns. The corrected 0.99 setting yields 81,919 patterns at 10% and only 9 at full data. This means Chess is a fixed-minsup scalability study, not a fixed-output-volume study; prefix composition changes its pattern count non-monotonically.
- The selected 10% Mushroom support 0.15 produced 3.44M patterns in a callback-only screen, but it was not used in scale runs. The corrected, paired support is 0.2 (835,583 patterns at 10%).
- The supplied raw CSVs contain five warm `count` and five warm `write` rows per variant for every accepted full-data and scalability condition, including Chess 10% at corrected minsup 0.99. An earlier interrupted 127-row run remains separate and is excluded from the report.
- The interrupted first scale attempt is preserved in run `20261119-180657`; only the separately rerun corrected scope is included in this table.
- The interactive scalability visualization is `docs/validation/figures/baseline-optimized-scalability.html`; the full cold-ladder runtime/RSS chart is still pending. The legacy matplotlib plotting suite cannot import `matplotlib` in this Python runtime; the new stdlib-only paired renderer has three focused tests passing. A ZIP with 110 verified file-level SHA256 entries has been created locally and recorded in `docs/validation/benchmark-handoff.md`. No external handoff to Đăng has occurred.

## Reproduction

From repository root with the same local datasets and Julia 1.12.0:

```powershell
$julia = 'C:\Users\tlthi\AppData\Local\Programs\Julia-1.12.0\bin\julia.exe'
foreach ($variant in @('baseline', 'optimized')) {
  $config = "bench/config-$variant-20261119.toml"
  foreach ($dataset in @('Chess','Mushroom','Retail','Accidents','T10I4D100K')) {
    & $julia --startup-file=no --project=. bench/run.jl --scope warm --dataset $dataset --config $config
    & $julia --startup-file=no --project=. bench/run.jl --scope cold --dataset $dataset --config $config
    & $julia --startup-file=no --project=. bench/run.jl --scope scalability --dataset $dataset --config $config
  }
}
```

Raw successful full-data runs: Baseline directories `20261119-180657`, `20261119-201827`, `20261119-201921`, `20261119-202028`, `20261119-202240`, `20261119-203622`; Optimized `20261119-193203`, `20261119-193521`, `20261119-193957`, `20261119-194539`, `20261119-194819`, `20261119-195232`, `20261119-195513`, `20261119-195759`, `20261119-200150`, `20261119-200348`. Corrected scalability runs: Baseline `20261119-201827` through `20261119-203622`; Optimized `20261119-204859` through `20261119-205638`. The concise run ledger is `results/handoff/benchmark-baseline-optimized-20261119/full-run/scalability.log` and `optimized-warm-cold.log`.
