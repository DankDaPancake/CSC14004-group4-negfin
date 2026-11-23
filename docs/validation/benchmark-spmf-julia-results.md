# Kết quả cold SPMF–Julia Optimized (22-11-2026)

**Đã đo mới đủ 210/210 lượt chính, 35/35 cấu hình ghép cặp được xác minh; 0 cấu hình thiếu.** Không tái sử dụng thời gian Julia từ campaign Baseline–Optimized. Pilot gồm 18 lượt riêng, không đưa vào median chính.

## Provenance và phương pháp

Campaign local: `results/spmf-julia-cold-20261122-v3/`; fingerprint `0490b0be675929b57d3f47a3e823c8ed1fb91e856b46127efc162077a98dddd4`. Git base `70ad97c47aed5331ff7c900e4cb40d836f088bad`, **working tree chưa commit**; source/config snapshot và hash nằm trong campaign. Không gọi đây là benchmark tại một revision sạch đã commit.

| Hạng mục | Thiết lập |
|---|---|
| Máy | Windows 11 Pro build 26200; Intel Core i5-13600K, 20 logical CPUs; RAM 34,088,599,552 bytes |
| Julia | 1.12.0; `--startup-file=no --threads=1 --project=...`; variant Optimized |
| SPMF | NegFIN, SPMF 2.69; Temurin 25.0.5.1+2; `-XX:ActiveProcessorCount=1 -Xmx4g` |
| Dữ liệu | 5 snapshot SHA-256/count đã kiểm theo `data/benchmark/manifest.toml` |
| Lịch | 7 minsup/dataset, 3 process mới mỗi implementation; lần 1/3 SPMF→Julia, lần 2 Julia→SPMF; chạy tuần tự |
| Timer | Monotonic whole-process wall: startup, JIT, đọc, mining, ghi, exit; không gồm validation |
| Memory | Native Windows `GetProcessMemoryInfo.PeakWorkingSetSize`, MiB = bytes/1,048,576 |
| Guard mỗi process | 1.800 s, output 2 GiB, RSS 8 GiB; poll 0,02 s; cần ít nhất 20 GiB đĩa trống |
| Validation | External sort, 64 MiB encoded payload/chunk (chưa tính Python overhead), fan-in 32, scratch cap 16 GiB |

Cold nghĩa là **process mới**, không xóa filesystem cache. Java heap không tương đương RSS quota; ActiveProcessorCount không khẳng định JVM chỉ có một OS thread. Đây là so sánh end-to-end các implementation/runtime/CLI trên máy này, không phải kết luận tốc độ thuần thuật toán hoặc ngôn ngữ.

## Correctness và ngưỡng support

- Pilot đạt 9/9 điều kiện: toy, fixture rìa ngưỡng, mức dễ nhất của 5 dataset, Chess 0,3 và Mushroom 0,02.
- Lần đầu của mỗi cấu hình chính được canonical hóa theo thứ tự item số, phát hiện duplicate rồi so **từng itemset và support**; missing/extra/support_mismatch đều bằng 0.
- Hai repetition sau khớp count và canonical SHA-256 với lần đầu; cả hai implementation có cùng digest. Không chỉ so pattern count.
- Ngưỡng Julia là `ceil(minsup_decimal × N)` chính xác. Source SPMF 2.69 dùng `Math.ceil(double × N)`: fixture N=100/minsup=0.07 ban đầu cho 8 thay vì 7. Campaign thất bại được giữ riêng. Chính sách CLI `exact-ceil-cli-v1` ghi rõ requested/effective: `0.07`→`0.06999999999999999` cho fixture, vẫn nhắm count 7. Pilot đã so với output tính tay.
- **Cả 35 cấu hình thực dùng nguyên chuỗi minsup yêu cầu**, vì binary ceiling trùng exact ceiling. Mapping và argv được lưu ở từng measurement JSON.

## Bảng kết quả đầy đủ

Mỗi ô thời gian là **median [min–max]**, giây, từ ba lượt mới. RSS là median MiB theo thứ tự SPMF / Julia. Bảng giữ ba chữ số thời gian; CSV giữ độ chính xác gốc.

| Dataset | minsup | min_count | Patterns | SPMF sec [min–max] | Julia sec [min–max] | RSS MiB S/J |
|---|---:|---:|---:|---|---|---:|
| Chess | 0.9 | 2877 | 622 | 0.172 [0.159–0.179] | 2.480 [2.475–2.497] | 80.4 / 332.5 |
| Chess | 0.55 | 1758 | 574,998 | 0.336 [0.331–0.347] | 3.013 [2.994–3.016] | 196.9 / 334.5 |
| Chess | 0.5 | 1598 | 1,272,932 | 0.436 [0.432–0.455] | 3.908 [3.723–4.028] | 198.9 / 335.8 |
| Chess | 0.45 | 1439 | 2,832,777 | 0.623 [0.563–0.655] | 6.056 [5.867–6.127] | 199.6 / 340.8 |
| Chess | 0.4 | 1279 | 6,439,702 | 1.036 [1.035–1.056] | 10.767 [10.150–10.872] | 200.2 / 341.3 |
| Chess | 0.35 | 1119 | 15,108,722 | 1.932 [1.891–1.952] | 22.845 [22.403–23.537] | 205.7 / 344.8 |
| Chess | 0.3 | 959 | 37,282,962 | 5.154 [4.745–5.963] | 53.578 [36.420–57.130] | 204.2 / 349.8 |
| Retail | 0.01 | 882 | 159 | 0.391 [0.389–0.394] | 2.960 [2.810–3.258] | 191.0 / 407.7 |
| Retail | 0.006 | 529 | 417 | 0.546 [0.538–0.554] | 3.127 [3.116–3.255] | 201.7 / 473.8 |
| Retail | 0.005 | 441 | 580 | 0.631 [0.627–0.631] | 3.239 [3.234–3.289] | 205.3 / 511.3 |
| Retail | 0.004 | 353 | 831 | 0.763 [0.751–0.816] | 4.084 [3.644–4.110] | 227.5 / 578.9 |
| Retail | 0.003 | 265 | 1,393 | 1.081 [1.080–1.096] | 5.219 [4.712–5.464] | 240.7 / 781.6 |
| Retail | 0.002 | 177 | 2,691 | 1.653 [1.643–1.675] | 7.147 [6.946–7.290] | 268.7 / 1037.3 |
| Retail | 0.001 | 89 | 7,589 | 3.386 [3.377–3.527] | 11.617 [11.389–11.938] | 369.5 / 2084.4 |
| Mushroom | 0.8 | 6733 | 17 | 0.168 [0.167–0.205] | 2.447 [2.434–2.525] | 93.3 / 332.6 |
| Mushroom | 0.15 | 1263 | 99,071 | 0.233 [0.228–0.234] | 2.610 [2.604–2.614] | 114.0 / 339.6 |
| Mushroom | 0.1 | 842 | 600,817 | 0.423 [0.405–0.431] | 2.936 [2.924–2.943] | 197.7 / 343.8 |
| Mushroom | 0.07 | 590 | 970,105 | 0.459 [0.432–0.548] | 3.253 [3.229–3.443] | 195.8 / 344.0 |
| Mushroom | 0.05 | 421 | 4,137,547 | 0.757 [0.745–0.779] | 5.714 [5.678–5.737] | 201.5 / 346.9 |
| Mushroom | 0.03 | 253 | 12,372,681 | 1.665 [1.636–1.720] | 12.390 [12.131–13.514] | 199.3 / 351.7 |
| Mushroom | 0.02 | 169 | 22,840,275 | 2.897 [2.885–3.105] | 20.069 [19.938–20.283] | 204.4 / 356.9 |
| Accidents | 0.9 | 306165 | 31 | 0.798 [0.764–0.803] | 4.339 [4.320–4.345] | 193.0 / 711.5 |
| Accidents | 0.6 | 204110 | 2,074 | 1.095 [1.087–1.096] | 5.105 [5.056–5.146] | 196.1 / 893.2 |
| Accidents | 0.45 | 153083 | 16,123 | 1.431 [1.395–1.448] | 5.932 [5.904–5.987] | 224.2 / 1100.5 |
| Accidents | 0.35 | 119065 | 68,222 | 1.749 [1.727–1.904] | 6.634 [6.591–6.676] | 256.7 / 1275.8 |
| Accidents | 0.3 | 102055 | 149,545 | 2.139 [2.123–2.144] | 7.362 [7.324–7.496] | 261.0 / 1330.9 |
| Accidents | 0.25 | 85046 | 346,525 | 3.442 [3.325–3.490] | 8.948 [8.912–9.047] | 300.2 / 1720.0 |
| Accidents | 0.2 | 68037 | 889,883 | 6.696 [6.464–6.703] | 12.182 [12.181–12.332] | 352.1 / 2618.8 |
| T10I4D100K | 0.02 | 2000 | 155 | 0.657 [0.654–0.687] | 3.757 [3.754–3.779] | 234.0 / 705.2 |
| T10I4D100K | 0.015 | 1500 | 237 | 0.835 [0.829–0.850] | 4.351 [4.342–4.389] | 250.2 / 891.6 |
| T10I4D100K | 0.01 | 1000 | 385 | 1.228 [1.207–1.230] | 5.371 [5.337–5.438] | 271.3 / 1278.4 |
| T10I4D100K | 0.008 | 800 | 494 | 1.629 [1.569–1.630] | 5.874 [5.848–5.953] | 296.9 / 1400.4 |
| T10I4D100K | 0.006 | 600 | 772 | 1.852 [1.792–1.855] | 7.084 [6.586–7.217] | 313.5 / 1656.4 |
| T10I4D100K | 0.004 | 400 | 2,001 | 2.185 [2.167–2.198] | 8.034 [7.993–8.088] | 326.1 / 1778.4 |
| T10I4D100K | 0.002 | 200 | 13,255 | 2.514 [2.485–2.541] | 9.222 [9.201–9.246] | 341.8 / 1937.3 |

## Hình và diễn giải

Thư mục local `results/spmf-julia-final-20261122/figures/` có **11 hình, mỗi hình PNG/PDF**: runtime–minsup và itemsets–minsup cho 5 dataset, RSS tại mức thứ tư. `captions.md` và `figure-data.csv` đi kèm; toàn bộ figure dùng summary đã được chấp nhận. Đã xem contact sheet 11 hình và xem riêng runtime Chess/RSS để kiểm tra bố cục.

- SPMF có median whole-process wall và peak working set thấp hơn ở **35/35 điểm**; tỉ số median Julia/SPMF từ **1,82 đến 14,60**. Đây không phải mức tăng tốc mining-only; startup/JIT/I/O cùng nằm trong timer.
- Chess và Mushroom sinh tới 37,28 và 22,84 triệu itemset ở mức thấp nhất, vì vậy không nên quy mọi khác biệt cho cấu trúc mining mà chưa profile chi phí ghi/format/duyệt kết quả.
- Retail/T10I4D100K có output ít hơn nhưng RSS Julia tăng mạnh khi hạ support; đây là quan sát, chưa chứng minh nguyên nhân heap/bitmap cụ thể.
- Chess 0,3 Julia có khoảng **36,420–57,130 s**, median 53,578 s. Giữ nguyên cả ba mẫu, không loại mẫu chậm hoặc thay bằng số cũ. Cần thêm lặp/kiểm soát tải máy để suy luận thống kê.
- Scalability Baseline–Optimized ngày 19-11-2026 được giữ riêng ở [Chương 2](../report/chapter2.md); **không có số đo scalability SPMF mới**. Trade-off RSS T10I4D100K của campaign cũ không bị thay thế bằng phép so SPMF mới.

## Gián đoạn, nguồn và khả năng tái lập

Preflight đầu thiếu đĩa; pilot đầu sai threshold binary; v2 gặp race khi Julia rename output tạm. Các bằng chứng đó vẫn ở campaign riêng. Sau sửa monitor, v3 chạy lại pilot. Tác vụ v3 nguyên khối bị dừng ở giới hạn harness 2 giờ sau 40 số đo chính; người dùng duyệt tiếp tục từng cấu hình, giữ nguyên fingerprint và không đo lại slot đã lưu. Cuối cùng có đúng **210 slot chính duy nhất + 18 slot pilot**, tất cả `ok`; không trộn v1/v2 hoặc retry thay số đo.

Chưa thiết lập được mirror **Hugging Face/Kaggle khớp byte/SHA-256**. Các truy vấn tìm kiếm không trả ứng viên phù hợp; đây không phải bằng chứng rằng không tồn tại mirror. Chưa có file HF/Kaggle để tải và xác minh, nên mục này còn thiếu. Giữ nguồn [SPMF catalog](https://www.philippe-fournier-viger.com/spmf/index.php?link=datasets.php) và các mirror đã có trong manifest, không thay bằng dataset cùng tên nhưng khác mã hóa.

JDK archive đã khớp checksum Adoptium API; SPMF jar/source zip lấy từ nguồn chính thức, hash tự tính không phải chữ ký độc lập. Jar SHA-256: `bb371b99b3bfd58fbce6b92e0ea3ccda5f9d1fd173bfe8e40f177672117159ba`. Runtime/input/output lớn không đưa vào Git hoặc ZIP evidence.

Dùng root mới khi đo lại:

```powershell
python -I bench/spmf_campaign.py --config bench/config-spmf-julia-20261122.toml --julia "PATH_TO_JULIA_EXE" --java "PATH_TO_JAVA_EXE" --jar "PATH_TO_SPMF_JAR" --root results/spmf-julia-new --mode preflight
# Cùng argv, đổi mode thành pilot rồi main và thêm --resume.
```

Dùng Python venv có matplotlib 3.10.8/pandas 2.3.3 để tổng hợp, output phải mới:

```powershell
& "tools/spmf-julia-20261122/plot-venv/Scripts/python.exe" -I docs/validation/summarize-spmf-julia.py results/spmf-julia-cold-20261122-v3 --output results/spmf-julia-reanalysis --figures --package
```

Gói chứa measurement/validation JSON, CSV, logs/stats, config/source/provenance, không chứa output itemset đã xóa sau validation. Muốn so lại byte output phải chạy lại miners. SHA-256 và đường dẫn gói: [hướng dẫn bàn giao](benchmark-handoff.md). Chưa gửi gói ra ngoài, chưa commit/push/PR; đề xuất tối ưu và thí nghiệm chiều dài transaction vẫn chờ quyết định của Đăng.

## Kiểm thử cuối sau đo

- `python -I -m unittest discover -s bench/tests -p "test_spmf_*.py" -v`: **38/38 đạt**.
- Python venv, `docs/validation/test_*.py`: **16/16 đạt** (gồm regression từ chối threshold nhất quán nhưng sai so với campaign); `apps/tests/test_*.py`: **11/11 đạt**.
- `julia --startup-file=no --project=. test/runtests.jl`: tất cả testset đạt. Nhóm Julia SPMF opt-in không bật riêng; pilot/campaign Python đã chạy SPMF thật.
- Strict summary thực nghiệm: **Accepted paired points: 35; incomplete: 0**.
- Review độc lập không chạy được vì lỗi isolation worktree của harness; đã tự review và sửa summary từng chỉ so input/threshold giữa các row mà chưa đối chiếu metadata campaign. Regression quan sát FAIL→PASS; summary mới vẫn chấp nhận35/35 điểm và không đổi số liệu/hình. Source đo v3 không bị sửa (chỉ analysis script ngoài fingerprint thay đổi). Bản xác minh sau sửa: `results/spmf-julia-final-verified-20261122/`. Không coi self-review/test là review độc lập; cần review độc lập trước merge.
