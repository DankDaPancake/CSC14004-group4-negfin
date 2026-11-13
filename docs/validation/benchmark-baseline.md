# Benchmark negFIN Baseline

Đợt đo 13/11/2026, theo [thiết kế](../superpowers/specs/2026-11-13-baseline-benchmark-design.md). Đây là số liệu ban đầu cho Chương 2 và mốc đối chứng cho bản Optimized; chưa phải phân tích cuối.

## Cấu hình

| Mục | Giá trị |
|---|---|
| Máy | Intel Core i5-13600K (14 core: 6P + 8E, 20 luồng), 31,75 GiB RAM |
| Hệ điều hành | Windows 11 Pro 10.0.26200 x64 |
| Julia | 1.12.0 portable, 1 luồng (`Threads.nthreads() = 1`), `--startup-file=no` |
| Commit | `3ecd0c1`, working tree sạch (`env.toml`) |
| Lần chạy chính | `results/bench/20261113-154220/`, 15:42–17:40, 581 lần đo, tất cả `ok` |
| Harness | chạy ở commit `3ecd0c1`, trước bản sửa runner `c5f3d5b`. Bản sửa chỉ ảnh hưởng tới các lần chạy bị kill vì timeout hoặc output cap; lần chạy chính không có lần nào như vậy, nên số liệu không bị ảnh hưởng |
| CPU affinity | không đặt; máy có lõi lai P/E |

Dữ liệu: 5 file trong `data/benchmark/`, SHA256 khớp [manifest](../../data/benchmark/manifest.toml) và được kiểm lại trước mỗi lần đo.

## Lệnh chạy

```powershell
$julia = 'D:\.tools\julia-1.12.0\bin\julia.exe'
& $julia --startup-file=no --project=. bench/pilot.jl --dataset Chess      # lặp cho 5 tập
& $julia --startup-file=no --project=. bench/run.jl --all                  # warm + cold + scalability
```

Các mức minsup và tham số lặp nằm trong [`bench/config.toml`](../../bench/config.toml).

## Phạm vi đo

| Phạm vi | Đo gì | Gồm | Không gồm |
|---|---|---|---|
| **warm** | thời gian, byte cấp phát, GC theo giai đoạn | các giai đoạn trong `mine_baseline`, đo trong cùng process sau warm-up trên toy; 5 lần, báo median | khởi động Julia, JIT, đọc file (đo riêng là `read_seconds`) |
| warm `count` | khai thác | tạo vector ID cho từng mẫu trong `emit_family!`; emit chỉ tăng bộ đếm | định dạng và ghi output |
| warm `write` | khai thác + ghi | như `count`, cộng `write_itemset` vào file tạm | rename |
| **cold** | wall-clock toàn process, peak RSS | khởi động Julia, load module, JIT, đọc, khai thác, ghi, rename, ghi stats; 3 lần, báo median | — |
| peak RSS | `Sys.maxrss()` của process con | runtime Julia | — |

- `bytes` là **tổng byte cấp phát** trong giai đoạn, không phải bộ nhớ đỉnh.
- Peak RSS nền của process chỉ load NegFIN là **263,9 MiB**; cột "− nền" chỉ là ước lượng.
- Cột "ghi output" bằng `write − count` (median từng chế độ). Cột này chỉ có ý nghĩa khi chênh lệch lớn hơn độ dao động giữa các lần lặp; xem [độ tin cậy](#độ-tin-cậy-của-số-đo-warm).

## Chọn minsup (pilot)

Mỗi tập chạy một thang minsup giảm dần, mỗi mức 1 lần cold, giới hạn 120 s và 2 GiB output. `select_levels` chọn 5–7 mức trải đều theo log(`mine_write_seconds`).

| Tập | Run pilot | Mức đã thử | Mức chọn | Dừng vì |
|---|---|---|---|---|
| Chess | `20261113-152931` | 0.9 → 0.3 (13 mức) | 0.9, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3 | hết thang |
| Retail | `20261113-152726` | 0.01 → 0.001 (8 mức) | 0.01, 0.006, 0.005, 0.004, 0.003, 0.002, 0.001 | hết thang |
| Mushroom | `20261113-153910` | 0.8 → 0.01 (14 mức) | 0.8, 0.15, 0.1, 0.07, 0.05, 0.03, 0.02 | 0.01 vượt 2 GiB output |
| Accidents | `20261113-153557` | 0.9 → 0.2 (14 mức) | 0.9, 0.6, 0.45, 0.35, 0.3, 0.25, 0.2 | hết thang |
| T10I4D100K | `20261113-153310` | 0.02 → 0.002 (7 mức) | cả 7 mức | hết thang |

Số liệu từng mức của pilot (1 lần cold; `mine_write_seconds` gồm JIT, chỉ dùng để xếp hạng):

| Tập | minsup | min_count | Mẫu | Output MiB | mine_write s | Wall s | Peak RSS MiB |
|---|---|---:|---:|---:|---:|---:|---:|
| Chess | 0.9 | 2.877 | 622 | 0,0 | 0,713 | 2,788 | 327,0 |
| Chess | 0.85 | 2.717 | 2.669 | 0,1 | 0,497 | 2,515 | 329,2 |
| Chess | 0.8 | 2.557 | 8.227 | 0,2 | 0,494 | 2,492 | 327,6 |
| Chess | 0.75 | 2.397 | 20.993 | 0,6 | 0,502 | 2,558 | 329,0 |
| Chess | 0.7 | 2.238 | 48.731 | 1,4 | 0,548 | 2,523 | 334,2 |
| Chess | 0.65 | 2.078 | 111.239 | 3,2 | 0,660 | 2,716 | 354,3 |
| Chess | 0.6 | 1.918 | 254.944 | 7,7 | 0,874 | 3,163 | 383,8 |
| Chess | 0.55 | 1.758 | 574.998 | 18,2 | 1,192 | 3,601 | 370,9 |
| Chess | 0.5 | 1.598 | 1.272.932 | 41,8 | 2,466 | 4,895 | 391,8 |
| Chess | 0.45 | 1.439 | 2.832.777 | 96,4 | 5,716 | 8,088 | 411,0 |
| Chess | 0.4 | 1.279 | 6.439.702 | 227,1 | 12,351 | 14,651 | 464,6 |
| Chess | 0.35 | 1.119 | 15.108.722 | 551,7 | 24,891 | 27,027 | 531,7 |
| Chess | 0.3 | 959 | 37.282.962 | 1.406,1 | 62,557 | 64,709 | 541,3 |
| Retail | 0.01 | 882 | 159 | 0,0 | 0,752 | 2,916 | 422,7 |
| Retail | 0.008 | 706 | 243 | 0,0 | 0,883 | 3,071 | 476,2 |
| Retail | 0.006 | 529 | 417 | 0,0 | 1,367 | 3,743 | 506,9 |
| Retail | 0.005 | 441 | 580 | 0,0 | 2,041 | 4,307 | 564,5 |
| Retail | 0.004 | 353 | 831 | 0,0 | 3,887 | 6,429 | 705,5 |
| Retail | 0.003 | 265 | 1.393 | 0,0 | 7,747 | 10,137 | 937,0 |
| Retail | 0.002 | 177 | 2.691 | 0,0 | 18,459 | 20,866 | 1.187,6 |
| Retail | 0.001 | 89 | 7.589 | 0,1 | 55,380 | 58,116 | 2.051,4 |
| Mushroom | 0.8 | 6.733 | 17 | 0,0 | 0,489 | 2,535 | 329,9 |
| Mushroom | 0.7 | 5.892 | 31 | 0,0 | 0,473 | 2,574 | 330,2 |
| Mushroom | 0.6 | 5.050 | 51 | 0,0 | 0,500 | 2,502 | 330,2 |
| Mushroom | 0.5 | 4.208 | 163 | 0,0 | 0,474 | 2,518 | 329,6 |
| Mushroom | 0.4 | 3.367 | 505 | 0,0 | 0,470 | 2,505 | 329,8 |
| Mushroom | 0.3 | 2.525 | 2.587 | 0,1 | 0,502 | 2,519 | 332,3 |
| Mushroom | 0.2 | 1.684 | 53.337 | 1,7 | 0,605 | 2,708 | 338,3 |
| Mushroom | 0.15 | 1.263 | 99.071 | 3,1 | 0,663 | 2,683 | 350,2 |
| Mushroom | 0.1 | 842 | 600.817 | 20,1 | 1,061 | 3,174 | 342,8 |
| Mushroom | 0.07 | 590 | 970.105 | 32,1 | 1,425 | 3,634 | 343,4 |
| Mushroom | 0.05 | 421 | 4.137.547 | 145,4 | 4,522 | 6,669 | 359,2 |
| Mushroom | 0.03 | 253 | 12.372.681 | 447,3 | 15,574 | 17,749 | 375,7 |
| Mushroom | 0.02 | 169 | 22.840.275 | 841,6 | 29,470 | 31,796 | 380,8 |
| Mushroom | 0.01 | – | – | > 2.048 | – | 64,504 | – |
| Accidents | 0.9 | 306.165 | 31 | 0,0 | 1,917 | 5,095 | 770,8 |
| Accidents | 0.85 | 289.156 | 71 | 0,0 | 2,375 | 5,883 | 770,0 |
| Accidents | 0.8 | 272.147 | 149 | 0,0 | 2,274 | 5,689 | 820,8 |
| Accidents | 0.75 | 255.138 | 313 | 0,0 | 2,724 | 6,279 | 840,7 |
| Accidents | 0.7 | 238.129 | 529 | 0,0 | 2,764 | 6,064 | 888,9 |
| Accidents | 0.65 | 221.119 | 1.093 | 0,0 | 2,737 | 6,068 | 863,7 |
| Accidents | 0.6 | 204.110 | 2.074 | 0,1 | 3,344 | 6,730 | 888,9 |
| Accidents | 0.5 | 170.092 | 8.057 | 0,2 | 3,801 | 7,156 | 938,1 |
| Accidents | 0.45 | 153.083 | 16.123 | 0,4 | 5,572 | 9,160 | 1.212,5 |
| Accidents | 0.4 | 136.074 | 32.528 | 0,9 | 7,147 | 10,591 | 1.498,8 |
| Accidents | 0.35 | 119.065 | 68.222 | 2,0 | 10,228 | 13,594 | 1.607,3 |
| Accidents | 0.3 | 102.055 | 149.545 | 4,6 | 14,441 | 17,880 | 1.593,6 |
| Accidents | 0.25 | 85.046 | 346.525 | 11,1 | 26,856 | 30,192 | 2.028,7 |
| Accidents | 0.2 | 68.037 | 889.883 | 29,5 | 55,458 | 59,027 | 2.473,0 |
| T10I4D100K | 0.02 | 2.000 | 155 | 0,0 | 4,064 | 6,694 | 573,4 |
| T10I4D100K | 0.015 | 1.500 | 237 | 0,0 | 9,063 | 11,678 | 857,9 |
| T10I4D100K | 0.01 | 1.000 | 385 | 0,0 | 14,771 | 16,953 | 1.097,1 |
| T10I4D100K | 0.008 | 800 | 494 | 0,0 | 17,617 | 20,116 | 1.359,8 |
| T10I4D100K | 0.006 | 600 | 772 | 0,0 | 22,277 | 24,691 | 1.469,1 |
| T10I4D100K | 0.004 | 400 | 2.001 | 0,0 | 32,479 | 34,826 | 1.413,3 |
| T10I4D100K | 0.002 | 200 | 13.255 | 0,3 | 37,653 | 40,311 | 1.641,5 |

Pilot Chess, Mushroom và Accidents ở bảng trên là lần chạy với thang mở rộng (`20261113-152931`, `20261113-153910`, `20261113-153557`).

- Thang ban đầu của Chess, Mushroom và Accidents quá dễ (mức thấp nhất khai thác dưới 4 s), nên đã được mở rộng và chạy lại pilot.
- `mine_write_seconds` của lần cold gồm khoảng 0,5 s JIT. Vì vậy các mức dễ của Chess (0.9–0.6) và Mushroom (0.8–0.2) trông gần bằng nhau, và quy tắc chọn nhảy thẳng từ mức đầu xuống 0.55 hoặc 0.15. Nếu báo cáo cần đường cong mượt ở vùng minsup cao, nên thêm các mức trung gian.

## Kết quả warm

Median 5 lần, trừ Chess 0.3 và Accidents 0.2 ở chế độ write chỉ chạy 3 lần (lần đầu vượt 60 s). Thời gian theo giai đoạn lấy từ chế độ `count`. Cấp phát và GC là của giai đoạn `mine`.

| Tập | minsup | min_count | Mẫu | Output MiB | normalize+prepare s | build_bmc s | mine s | Tổng count s | Tổng write s | Ghi output s | Cấp phát mine MiB | GC mine s | Node BMC | Record NegNodeset quét |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Chess | 0.9 | 2.877 | 622 | 0,0 | 0,004 | 0,006 | 0,000 | 0,010 | 0,010 | ≈0 | 0,6 | 0,000 | 163 | 2.342 |
| Chess | 0.55 | 1.758 | 574.998 | 18,2 | 0,004 | 0,015 | 0,422 | 0,456 | 1,113 | 0,657 | 349,6 | 0,088 | 12.283 | 1.399.797 |
| Chess | 0.5 | 1.598 | 1.272.932 | 41,8 | 0,009 | 0,033 | 0,817 | 0,861 | 2,273 | 1,413 | 720,8 | 0,197 | 15.652 | 2.750.225 |
| Chess | 0.45 | 1.439 | 2.832.777 | 96,4 | 0,004 | 0,015 | 1,747 | 1,776 | 4,960 | 3,184 | 1.493,3 | 0,428 | 18.633 | 5.471.300 |
| Chess | 0.4 | 1.279 | 6.439.702 | 227,1 | 0,004 | 0,019 | 3,570 | 3,588 | 10,658 | 7,070 | 3.136,1 | 0,853 | 19.993 | 10.921.831 |
| Chess | 0.35 | 1.119 | 15.108.722 | 551,7 | 0,004 | 0,019 | 8,023 | 8,047 | 25,343 | 17,295 | 6.756,7 | 1,850 | 25.970 | 22.592.470 |
| Chess | 0.3 | 959 | 37.282.962 | 1.406,1 | 0,010 | 0,037 | 17,864 | 17,934 | 62,327 | 44,393 | 15.015,2 | 3,977 | 30.963 | 46.983.319 |
| Mushroom | 0.8 | 6.733 | 17 | 0,0 | 0,004 | 0,005 | 0,000 | 0,009 | 0,009 | ≈0 | 0,0 | 0,000 | 11 | 32 |
| Mushroom | 0.15 | 1.263 | 99.071 | 3,1 | 0,006 | 0,020 | 0,029 | 0,057 | 0,130 | 0,074 | 43,8 | 0,000 | 9.853 | 470.245 |
| Mushroom | 0.1 | 842 | 600.817 | 20,1 | 0,006 | 0,021 | 0,124 | 0,152 | 0,555 | 0,403 | 150,6 | 0,020 | 13.717 | 1.062.734 |
| Mushroom | 0.07 | 590 | 970.105 | 32,1 | 0,006 | 0,022 | 0,241 | 0,270 | 0,902 | 0,632 | 254,2 | 0,049 | 16.877 | 1.884.831 |
| Mushroom | 0.05 | 421 | 4.137.547 | 145,4 | 0,006 | 0,024 | 0,725 | 0,757 | 5,091 | 4,334 | 794,6 | 0,134 | 22.647 | 3.774.487 |
| Mushroom | 0.03 | 253 | 12.372.681 | 447,3 | 0,007 | 0,034 | 2,546 | 2,629 | 14,863 | 12,234 | 2.123,0 | 0,385 | 25.119 | 7.304.948 |
| Mushroom | 0.02 | 169 | 22.840.275 | 841,6 | 0,006 | 0,026 | 3,882 | 3,914 | 27,992 | 24,078 | 3.747,2 | 0,548 | 25.761 | 10.533.377 |
| Accidents | 0.9 | 306.165 | 31 | 0,0 | 0,628 | 0,408 | 0,000 | 1,053 | 1,296 | * | 0,0 | 0,000 | 20 | 86 |
| Accidents | 0.6 | 204.110 | 2.074 | 0,1 | 0,697 | 1,054 | 0,060 | 1,725 | 1,734 | ≈0 | 46,8 | 0,000 | 41.554 | 856.870 |
| Accidents | 0.45 | 153.083 | 16.123 | 0,4 | 0,648 | 1,450 | 1,259 | 3,456 | 3,463 | ≈0 | 529,6 | 0,247 | 298.404 | 9.439.091 |
| Accidents | 0.35 | 119.065 | 68.222 | 2,0 | 0,657 | 1,663 | 3,928 | 6,256 | 6,327 | * | 1.562,0 | 0,837 | 464.978 | 25.586.753 |
| Accidents | 0.3 | 102.055 | 149.545 | 4,6 | 0,691 | 1,734 | 7,997 | 10,557 | 13,965 | * | 3.063,2 | 1,689 | 528.018 | 47.109.226 |
| Accidents | 0.25 | 85.046 | 346.525 | 11,1 | 0,874 | 2,973 | 22,912 | 25,866 | 22,548 | * | 6.981,1 | 4,543 | 918.161 | 105.062.412 |
| Accidents | 0.2 | 68.037 | 889.883 | 29,5 | 0,947 | 3,764 | 62,771 | 67,824 | 74,338 | * | 16.725,7 | 12,021 | 1.592.785 | 247.407.003 |
| Retail | 0.01 | 882 | 159 | 0,0 | 0,052 | 0,057 | 0,054 | 0,166 | 0,166 | ≈0 | 84,7 | 0,000 | 31.035 | 1.311.508 |
| Retail | 0.006 | 529 | 417 | 0,0 | 0,050 | 0,091 | 0,611 | 0,772 | 0,754 | ≈0 | 475,1 | 0,182 | 81.803 | 7.162.838 |
| Retail | 0.005 | 441 | 580 | 0,0 | 0,054 | 0,095 | 0,918 | 1,083 | 1,160 | * | 816,9 | 0,262 | 106.290 | 11.865.799 |
| Retail | 0.004 | 353 | 831 | 0,0 | 0,092 | 0,134 | 3,141 | 3,392 | 3,579 | * | 1.566,2 | 0,888 | 141.814 | 21.373.050 |
| Retail | 0.003 | 265 | 1.393 | 0,0 | 0,087 | 0,208 | 7,049 | 7,404 | 7,289 | * | 3.705,8 | 2,053 | 198.944 | 44.922.606 |
| Retail | 0.002 | 177 | 2.691 | 0,0 | 0,081 | 0,357 | 18,247 | 18,741 | 11,980 | * | 11.007,4 | 5,564 | 292.503 | 112.439.766 |
| Retail | 0.001 | 89 | 7.589 | 0,1 | 0,069 | 0,401 | 35,432 | 35,952 | 52,205 | * | 26.640,9 | 11,476 | 433.383 | 320.412.112 |
| T10I4D100K | 0.02 | 2.000 | 155 | 0,0 | 0,066 | 0,162 | 2,493 | 2,753 | 2,805 | * | 1.625,7 | 0,691 | 229.252 | 21.241.329 |
| T10I4D100K | 0.015 | 1.500 | 237 | 0,0 | 0,102 | 0,416 | 9,355 | 9,898 | 9,422 | * | 3.259,9 | 2,432 | 355.394 | 45.687.110 |
| T10I4D100K | 0.01 | 1.000 | 385 | 0,0 | 0,077 | 0,559 | 15,655 | 16,383 | 13,475 | * | 6.943,4 | 4,301 | 515.132 | 93.797.908 |
| T10I4D100K | 0.008 | 800 | 494 | 0,0 | 0,116 | 0,595 | 25,030 | 25,661 | 24,604 | * | 8.988,0 | 6,647 | 571.219 | 116.649.144 |
| T10I4D100K | 0.006 | 600 | 772 | 0,0 | 0,099 | 0,732 | 26,421 | 27,268 | 19,728 | * | 10.609,2 | 7,054 | 618.866 | 139.472.678 |
| T10I4D100K | 0.004 | 400 | 2.001 | 0,0 | 0,082 | 0,529 | 21,743 | 22,399 | 22,505 | * | 12.827,3 | 6,311 | 671.294 | 170.059.239 |
| T10I4D100K | 0.002 | 200 | 13.255 | 0,3 | 0,075 | 0,543 | 25,943 | 26,808 | 26,967 | * | 15.615,6 | 7,452 | 703.369 | 204.597.875 |

`collect_nodesets` có median dưới 0,25 s ở mọi cấu hình (lần đo lớn nhất 0,45 s) và không được tách thành cột riêng; `normalize+prepare` là tổng hai giai đoạn. Thời gian đọc file (`read_seconds`, đo một lần): Chess 0,011 s, Mushroom 0,010 s, Retail 0,097 s, T10I4D100K 0,454 s, Accidents 1,438 s.

\* Chênh lệch `write − count` nhỏ hơn độ dao động giữa các lần lặp (có khi âm), nên không dùng được làm chi phí ghi output.

## Kết quả cold (median 3 lần)

| Tập | minsup | Wall s (min–max) | Peak RSS MiB (min–max) | RSS − nền MiB |
|---|---|---:|---:|---:|
| Chess | 0.9 | 2,585 (2,383–2,604) | 327,5 (326,4–330,2) | 63,6 |
| Chess | 0.55 | 3,226 (3,223–3,239) | 370,8 (370,2–371,0) | 106,9 |
| Chess | 0.5 | 3,899 (3,897–3,909) | 390,0 (387,7–390,1) | 126,1 |
| Chess | 0.45 | 5,631 (5,627–5,677) | 396,1 (395,8–396,7) | 132,2 |
| Chess | 0.4 | 9,533 (9,354–9,551) | 471,3 (463,3–471,6) | 207,4 |
| Chess | 0.35 | 18,677 (18,611–18,868) | 531,1 (524,8–534,8) | 267,2 |
| Chess | 0.3 | 41,681 (41,509–42,071) | 541,5 (538,9–544,3) | 277,6 |
| Mushroom | 0.8 | 2,471 (2,456–2,875) | 330,6 (329,9–330,8) | 66,6 |
| Mushroom | 0.15 | 2,694 (2,672–2,703) | 350,2 (348,3–350,9) | 86,3 |
| Mushroom | 0.1 | 3,125 (3,100–3,133) | 341,7 (341,5–342,2) | 77,8 |
| Mushroom | 0.07 | 3,522 (3,490–3,535) | 343,0 (342,0–344,0) | 79,1 |
| Mushroom | 0.05 | 6,073 (5,874–6,097) | 359,5 (357,5–366,1) | 95,6 |
| Mushroom | 0.03 | 12,548 (12,449–12,554) | 379,6 (378,5–384,0) | 115,7 |
| Mushroom | 0.02 | 20,955 (20,847–21,009) | 394,3 (387,2–395,0) | 130,4 |
| Accidents | 0.9 | 4,422 (4,368–4,481) | 732,6 (697,3–743,7) | 468,7 |
| Accidents | 0.6 | 5,297 (5,253–5,320) | 868,8 (864,1–873,8) | 604,9 |
| Accidents | 0.45 | 7,100 (6,988–7,227) | 1.253,4 (1.207,0–1.255,6) | 989,5 |
| Accidents | 0.35 | 10,247 (10,021–10,541) | 1.543,1 (1.227,1–1.562,9) | 1.279,2 |
| Accidents | 0.3 | 13,104 (12,858–13,295) | 1.617,2 (1.603,3–1.688,7) | 1.353,3 |
| Accidents | 0.25 | 24,583 (23,536–25,171) | 2.089,3 (2.002,1–2.098,3) | 1.825,3 |
| Accidents | 0.2 | 49,965 (48,081–51,866) | 2.495,7 (2.441,2–2.562,7) | 2.231,8 |
| Retail | 0.01 | 2,827 (2,820–3,032) | 426,7 (421,3–441,8) | 162,8 |
| Retail | 0.006 | 3,515 (3,457–3,704) | 546,8 (513,8–547,5) | 282,8 |
| Retail | 0.005 | 4,139 (4,126–4,141) | 562,3 (550,1–565,4) | 298,4 |
| Retail | 0.004 | 5,010 (4,987–5,020) | 645,2 (637,7–657,4) | 381,3 |
| Retail | 0.003 | 7,815 (7,619–7,833) | 815,4 (814,6–829,1) | 551,5 |
| Retail | 0.002 | 15,256 (15,251–15,272) | 1.196,0 (1.187,4–1.224,5) | 932,1 |
| Retail | 0.001 | 36,165 (36,132–36,367) | 1.973,3 (1.970,9–1.996,2) | 1.709,3 |
| T10I4D100K | 0.02 | 5,451 (5,443–5,452) | 578,4 (562,9–603,7) | 314,4 |
| T10I4D100K | 0.015 | 8,271 (8,053–8,281) | 803,0 (800,2–803,2) | 539,1 |
| T10I4D100K | 0.01 | 14,385 (14,369–14,599) | 1.178,2 (1.176,7–1.181,3) | 914,3 |
| T10I4D100K | 0.008 | 17,422 (17,214–17,670) | 1.286,4 (1.284,0–1.300,9) | 1.022,4 |
| T10I4D100K | 0.006 | 19,827 (19,605–19,856) | 1.351,5 (1.341,1–1.361,6) | 1.087,6 |
| T10I4D100K | 0.004 | 23,096 (22,897–23,314) | 1.409,6 (1.404,5–1.422,4) | 1.145,6 |
| T10I4D100K | 0.002 | 27,697 (27,491–27,700) | 1.517,9 (1.513,0–1.522,1) | 1.254,0 |

Ở các mức dễ của Chess và Mushroom, wall-clock cold khoảng 2,5–2,6 s, trong khi warm chỉ 0,01 s. Đó là chi phí cố định của khởi động Julia, load module và JIT.

## Scalability

Lấy tiền tố 20/40/60/80/100% giao dịch, giữ minsup tương đối cố định nên min_count co giãn theo N. Warm là median 5 lần ở chế độ `count`; cold là median 3 lần.

| Tập | minsup | Tỷ lệ | Giao dịch | Mẫu | mine s | build_bmc s | normalize+prepare s | Warm count s | Cold wall s | Peak RSS MiB | Node BMC | Record quét |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Accidents | 0.25 | 0,2 | 68.037 | 343.778 | 4,938 | 0,413 | 0,110 | 5,681 | 8,689 | 833,8 | 347.314 | 40.157.694 |
| Accidents | 0.25 | 0,4 | 136.073 | 357.130 | 7,929 | 0,812 | 0,234 | 9,042 | 12,644 | 1.210,7 | 508.377 | 60.376.858 |
| Accidents | 0.25 | 0,6 | 204.110 | 343.270 | 10,102 | 1,184 | 0,369 | 11,722 | 15,236 | 1.392,5 | 591.929 | 73.045.273 |
| Accidents | 0.25 | 0,8 | 272.146 | 346.827 | 14,373 | 1,688 | 0,537 | 16,751 | 20,047 | 1.577,7 | 804.644 | 93.038.930 |
| Accidents | 0.25 | 1,0 | 340.183 | 346.525 | 16,936 | 2,007 | 0,691 | 20,085 | 23,088 | 2.064,5 | 918.161 | 105.062.412 |
| T10I4D100K | 0.004 | 0,2 | 20.000 | 2.065 | 3,397 | 0,062 | 0,015 | 3,487 | 6,538 | 623,2 | 145.762 | 35.647.659 |
| T10I4D100K | 0.004 | 0,4 | 40.000 | 1.990 | 6,987 | 0,146 | 0,026 | 7,219 | 10,036 | 1.148,9 | 281.128 | 69.685.363 |
| T10I4D100K | 0.004 | 0,6 | 60.000 | 2.035 | 11,300 | 0,276 | 0,046 | 11,680 | 14,168 | 1.216,5 | 414.476 | 103.921.738 |
| T10I4D100K | 0.004 | 0,8 | 80.000 | 2.029 | 16,130 | 0,452 | 0,064 | 16,708 | 18,308 | 1.272,3 | 544.211 | 137.139.317 |
| T10I4D100K | 0.004 | 1,0 | 100.000 | 2.001 | 21,279 | 0,509 | 0,078 | 21,934 | 23,016 | 1.424,9 | 671.294 | 170.059.239 |

- Số mẫu gần như không đổi theo kích thước dữ liệu: Accidents khoảng 345 nghìn, T10I4D100K khoảng 2.000. Vì vậy scalability ở đây đo chi phí theo N với cùng một đầu ra.
Ở phần scalability, warm và cold cho giai đoạn `mine` gần nhau (lệch dưới 10% ở mọi tỷ lệ), nên các tỷ lệ dưới đây ít bị ảnh hưởng bởi độ dao động của warm. Tỷ lệ tính theo `mine` của warm, trong ngoặc là cold:

- **T10I4D100K:** từ 20% lên 100% dữ liệu (5 lần), `mine` tăng 6,3 lần (3,4 → 21,3 s), theo cold là 5,2 lần (3,8 → 19,6 s). Số record NegNodeset quét tăng 4,8 lần, node BMC tăng 4,6 lần. Như vậy `mine` tăng gần tuyến tính theo số record quét; chưa đủ cơ sở để nói tăng siêu tuyến tính.
- **Accidents:** cùng 5 lần dữ liệu, `mine` tăng 3,4 lần (4,9 → 16,9 s), theo cold là 3,1 lần (5,3 → 16,6 s). Record quét tăng 2,6 lần.
- Peak RSS tăng 2,3–2,5 lần trên cả hai tập.
- **Hai số đo cho cùng cấu hình Accidents 0.25 ở 100% dữ liệu lệch nhau.** Bảng warm chính cho `mine` median 22,9 s (từng lần 23,5 / 23,7 / 18,2 / 16,4 / 22,9 s), còn bảng scalability cho 16,9 s (20,2 / 17,3 / 16,9 / 16,1 / 16,8 s). Phép đo cold cho 17,2–18,7 s ở bảng chính và 15,9–16,9 s ở scalability. Đây là cùng một tập giao dịch: file con 100% có SHA256 khác file gốc chỉ vì `prefix_subset` bỏ khoảng trắng cuối dòng, nội dung từng dòng giống hệt sau khi bỏ khoảng trắng đó. Vì vậy khoảng lệch này là độ dao động của phép đo warm, không phải khác biệt của dữ liệu.

## Nhận xét điểm nghẽn ban đầu

Mỗi nhận xét dưới đây dựa trên số liệu trong các bảng trên. Phần nguyên nhân là giả thuyết, cần được kiểm chứng khi làm bản Optimized.

### 1. Giai đoạn nào chiếm thời gian

- **Ở minsup thấp, `mine` chiếm gần hết thời gian trên cả 5 tập:** từ 92% ở Accidents 0.2 đến trên 99% ở Chess 0.3 (tỷ lệ `mine` trên tổng thời gian chế độ count).
- **Ở minsup cao, chỉ Accidents có chi phí tiền xử lý đáng kể:**
  - Accidents 0.9: normalize+prepare 0,63 s và build_bmc 0,41 s, trong khi `mine` gần 0. Thêm 1,44 s đọc file.
  - Ở các mức thấp hơn, build_bmc của Accidents tăng tới 3,8 s (Accidents 0.2), vì số node BMC tăng từ 20 lên 1,59 triệu.
- **Giả thuyết trong thiết kế bị số liệu bác bỏ một phần.** Thiết kế kỳ vọng tiền xử lý chiếm phần lớn thời gian ở các tập thưa lớn như Retail. Điều này chỉ đúng ở mức dễ nhất, Retail 0.01: tiền xử lý 0,109 s so với `mine` 0,054 s. Từ Retail 0.006 trở xuống, `mine` chiếm trên 79%.

### 2. Thời gian `mine` bám theo đại lượng nào

Hai nhóm tập dữ liệu cho hai hình thái khác nhau.

- **Tập dày (Chess, Mushroom): `mine` bám theo số mẫu.**
  - Chess 0.45 → 0.3: số mẫu tăng 13,2 lần, `mine` (count) tăng 10,2 lần, record quét tăng 8,6 lần.
  - Chi phí trên mỗi mẫu tương đối ổn định: 0,48–0,73 µs ở Chess (0.55–0.3), 0,17–0,30 µs ở Mushroom (0.15–0.02).
- **Tập thưa (Retail, T10I4D100K) và Accidents: `mine` bám theo số record NegNodeset quét, không theo số mẫu.**
  - Retail 0.001 chỉ có 7.589 mẫu nhưng quét 320 triệu record, khoảng 42.000 record cho mỗi mẫu.
  - Thời gian trên mỗi record quét gần như không đổi khi tính bằng giai đoạn `mine` của phép đo cold: Retail 100–113 ns/record (0.006–0.001), T10I4D100K 111–120 ns/record (cả 7 mức). Ở hai tập này output dưới 0,3 MiB nên `mine` cold gần như chỉ là khai thác. Số đo warm cho cùng tỷ lệ dao động hơn nhiều (median 77–162 ns/record ở Retail; từng lần lên tới khoảng 190), xem [độ tin cậy](#độ-tin-cậy-của-số-đo-warm).
  - Scalability T10I4D100K cũng cho thấy điều này: số mẫu giữ khoảng 2.000 nhưng `mine` tăng theo record quét.

### 3. Chi phí ghi output

- **Tập dày: ghi output chiếm khoảng một nửa đến bốn phần năm thời gian `mine`.** Có hai cách ước lượng, cho kết quả khác nhau:
  - **Theo cold:** `mine` của cold (gồm ghi output) trừ `mine` của warm count. Chess 0.3: 21,3 s trên 39,1 s (54%), khoảng 14 ns/byte. Mushroom 0.02: 14,6 s trên 18,4 s (79%), khoảng 17 ns/byte.
  - **Theo warm:** `mine` của warm write trừ `mine` của warm count. Chess 0.3: 44,4 s trên 62,3 s (71%), khoảng 30 ns/byte. Mushroom 0.02: 24,1 s trên 27,9 s (86%), khoảng 27 ns/byte.
  - Phép đo warm write ở các cấu hình này chậm hơn cold một cách nhất quán (Chess 0.3: 59,1–62,7 s so với 39,1–39,5 s). Vì vậy ước lượng theo warm có thể cao gấp khoảng 2 lần thực tế. Nên dùng ước lượng theo cold làm mốc chính, ước lượng theo warm làm cận trên.
  - Theo cold, tỷ lệ này là 45–54% ở Chess (0.45–0.3) và 75–79% ở Mushroom (0.05–0.02); chi phí khoảng 14 ns/byte ở Chess và 16–18 ns/byte ở Mushroom.
- **Tập thưa: output dưới 0,3 MiB.** Ở đây chi phí ghi nhỏ hơn nhiều so với độ dao động của số đo, nên không ước lượng được bằng `write − count`.

### 4. Cấp phát và GC trong `mine`

- **Cấp phát rất lớn so với số mẫu:**
  - Chess 0.3: 14,7 GiB cấp phát cho 37,3 triệu mẫu, khoảng 420 byte mỗi mẫu, ngay cả ở chế độ count.
  - Retail 0.001: 26,0 GiB cấp phát, khoảng 87 byte cho mỗi record NegNodeset quét. Trên Retail, T10I4D100K và Accidents (bỏ các mức gần như không khai thác), tỷ lệ này nằm trong khoảng 58–103 byte/record.
- **GC chiếm phần đáng kể của `mine`:** 28–32% ở Retail, 26–29% ở T10I4D100K, 21–25% ở Chess, 19–21% ở Accidents và 14–20% ở Mushroom (median chế độ count, bỏ các mức mà `mine` dưới 0,1 s).
- **Giả thuyết về nguồn cấp phát:**
  - Mỗi lần `negative_pair`/`negative_extension` tạo một `Vector{NodeInfo}` mới.
  - Mỗi lần `iszero(ni.bitmap & mask)` tính phép AND trên `BigInt`, có thể tạo `BigInt` tạm.
  - `emit_family!` tạo một vector ID mới cho mỗi mẫu.

  Chưa có profiling để phân bổ chính xác tỷ lệ giữa ba nguồn này.

### 5. Peak RAM

- **Chess và Mushroom ở mức thấp:** peak RSS không vượt 545 MiB, tức dưới 280 MiB trên nền.
- **Accidents, Retail và T10I4D100K cao hơn nhiều:** lần lượt lên tới 2,44 GiB, 1,93 GiB và 1,48 GiB (median ở mức minsup thấp nhất).
- Peak RSS tăng cùng chiều với số node BMC và record quét. Peak RSS vẫn tăng khi output chỉ còn vài KiB, nên phần lớn bộ nhớ đỉnh không đến từ output.

### Hướng cải tiến gợi ý

Đây là các đề xuất dựa trên số liệu, chưa được đo:

1. **Thay bitmap `BigInt` bằng mảng `UInt64` cố định độ rộng** hoặc bitset tự quản lý. Mục tiêu là giảm cấp phát và thời gian trên mỗi record quét (100–120 ns ở tập thưa).
2. **Tái sử dụng buffer cho NegNodeset** thay vì tạo vector mới ở mỗi lần lọc. Mục tiêu là giảm tổng cấp phát và phần GC 14–32% của `mine`.
3. **Ghi output trực tiếp vào buffer byte** thay vì `join` và `println` cho từng mẫu. Mục tiêu là chi phí 14–18 ns/byte theo cold (cận trên 26–30 ns/byte theo warm), chiếm 45–79% thời gian `mine` ở tập dày theo cold.
4. **Tránh tạo vector ID mới cho mỗi mẫu trong `emit_family!`** khi người gọi không cần giữ lại vector (khoảng 420 byte/mẫu ở Chess).

## Độ tin cậy của số đo warm

- **Ở các cấu hình nặng, số đo warm dao động mạnh giữa các lần lặp.** Ví dụ, `mine` count của Retail 0.001 gồm 46,2 / 55,9 / 34,7 / 35,0 / 35,4 s; ở chế độ write là 35,5 / 42,9 / 53,3 / 51,3 / 54,3 s.
- **Phép đo cold ổn định hơn và thường nhanh hơn.** Giai đoạn `mine` trong cold (gồm cả ghi output) cho:
  - Retail 0.001: 32,8–32,9 s.
  - Chess 0.3: 39,1–39,5 s, so với khoảng 60 s của warm write.
  - Mushroom 0.02: 18,3–18,4 s, so với 19,9–28,3 s của warm write.
- **Hệ quả:**
  - Warm không phải là mốc thấp nhất ở các cấu hình trên khoảng 10 s.
  - Một số giá trị `write − count` bị âm, và T10I4D100K có thứ tự không đơn điệu ở phép đo warm: mức 0.006 chậm hơn mức 0.004, trong khi phép đo cold vẫn đơn điệu.
- **Nguyên nhân chưa xác định.** Giả thuyết: heap của process warm lớn dần qua các lần lặp nên GC tốn hơn, và hệ điều hành có thể đưa process sang lõi E. Có thể kiểm chứng bằng cách chạy warm với một process mới cho mỗi cấu hình, hoặc ghim process vào lõi P.
- **Khuyến nghị cho báo cáo:**
  - Dùng số đo warm cho tỷ lệ giữa các giai đoạn, tỷ lệ cấp phát và GC, vì các đại lượng này ít phụ thuộc vào độ dao động.
  - Dùng số đo cold cho thời gian tuyệt đối.
  - Ghi rõ min–max bên cạnh median.

## Nguồn dữ liệu công khai

Tra cứu ngày 13/11/2026:

- **Hugging Face:** API `api/datasets?search=` với các từ khóa `spmf`, `frequent-itemset`, `itemset`, `fimi`, `T10I4D100K`, `accidents` không có tập nào là 5 file benchmark này.
- **Kaggle:** API tìm kiếm không có bản sao nào của 5 file. Gần nhất là `jeffheaton/characteristics-that-favor-freqitemset-algorithms`, nhưng đó là dữ liệu tổng hợp khác hẳn.
- **Kho FIMI** ([fimi.uantwerpen.be/data](https://fimi.uantwerpen.be/data/)), nguồn gốc của các tập này. Mỗi file được tải vào thư mục tạm riêng rồi tính SHA256:

| Tập | File FIMI | SHA256 FIMI | Số dòng | So với manifest |
|---|---|---|---:|---|
| Chess | `chess.dat` | `a12ea887df58a396709430af5bf0a9a32d1f6eba8e7c13dd41f28b98572c5db2` | 3.196 | **khớp** |
| Accidents | `accidents.dat` | `8c2275550966e3cb4b6066f2bb168489a9566c500af559fa3925f1b11d97f0cd` | 340.183 | **khớp** |
| Retail | `retail.dat` | `d967431ba522e32f0fbb243f2ee113ecd4cb374cb0234c1b0858dae1d499a055` | 88.162 | khác: file SPMF bằng file FIMI với mọi ID cộng 1, nếu bỏ qua khoảng trắng cuối dòng |
| T10I4D100K | `T10I4D100K.dat` | `464d7b87aa7fdc0dc432ddad0493515569b2968b0f229ce39399c454a8c62e0c` | 100.000 | khác: cùng quan hệ ID cộng 1 |
| Mushroom | `mushroom.dat` | `6cf94bc482712c3936f0b40c921381ab2b776c3d9941880fecac4d83ca5cbeb5` | 8.124 | khác: đây là một tập dữ liệu khác, không phải bản đổi định dạng |

Quan hệ "ID cộng 1" được kiểm bằng cách cộng 1 vào mọi ID của file FIMI, bỏ khoảng trắng cuối dòng ở cả hai file rồi so từng dòng (`diff` không có khác biệt).

- Manifest đã có `mirror_url` cho Chess và Accidents.
- Retail và T10I4D100K trên FIMI chỉ khác do đổi ID. ID trong FIMI bắt đầu từ 0, trong khi định dạng SPMF và parser của nhóm yêu cầu ID dương. Kết quả khai thác sẽ giống nhau sau khi trừ 1 vào ID, nhưng chưa được chạy kiểm chứng.
- **Mushroom:** đề bài mô tả 8.124 giao dịch, đúng bằng số dòng của `mushroom.dat` trên FIMI, còn nhóm đang dùng `mushrooms.txt` của SPMF với 8.416 dòng. Nhóm cần quyết định giữ bản nào.
- **Điều khoản sử dụng trên FIMI:** retail và accidents được cung cấp "as is", yêu cầu ghi nguồn và gửi bản sao công trình cho Tom Brijs (retail) và Karolien Geurts (accidents). Các tập còn lại không ghi điều khoản.
- **Hugging Face/Kaggle:** nếu môn học bắt buộc link trên một trong hai nơi, nhóm cần tự tạo dataset chứa đúng 5 file, ghi nguồn SPMF/FIMI và tuân thủ các điều khoản trên. Việc upload là hành động công khai, cần cả nhóm đồng ý trước.
