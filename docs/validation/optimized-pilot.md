# Pilot Optimized — 14/11/2026

Thí nghiệm, chưa phải benchmark chính thức. Bản optimized giữ BMC-tree BigInt, chuyển bitmap của từng Nodeset sang `Vector{UInt64}` khi thu Nodeset, và kiểm tra bit theo word trong lúc khai thác. Không sửa Baseline; vector bitmap được tạo riêng cho mỗi record và không được thay đổi sau đó. Chi phí chuyển đổi được tính trong phase `collect_nodesets`, gồm cả lúc chạy CLI. Mỗi record dùng `8 × ceil(số frequent item / 64)` byte cho phần word, chưa kể overhead vector; có thể tăng peak RAM, nhất là khi đồng thời giữ cây BigInt.

## Môi trường và phạm vi

Windows, i7-11800H, RAM 16,9 GB, Julia 1.12.0 một luồng; input có SHA256 khớp manifest. Source dựa trên `f5ac6ce`, file `src/optimized.jl` khi đo có Git blob `f10f6f49c44fc9c935d153f85efd46f1863156e4`; các thay đổi khi đo chưa commit. CPU affinity không đặt.

Warm count dùng `bench/compare-pilot.jl`, 3 lượt mỗi variant, xen kẽ thứ tự, `GC.gc()` trước mỗi lượt; đo `mine_baseline`/`mine_optimized` sau toy warmup, input đã đọc và callback chỉ đếm, không ghi file. `bytes` là tổng cấp phát của lời gọi, không phải peak RAM. Pilot có thể vẫn chịu JIT, GC và dao động hệ thống; chưa kiểm soát cache/CPU.

| Dataset; minsup | Baseline median s (min–max) | Optimized median s (min–max) | Tổng cấp phát median MiB: baseline → optimized | Số mẫu |
|---|---:|---:|---:|---:|
| Retail 0,004 | 3,370 (3,303–3,651) | 1,217 (1,103–1,275) | 1.748,3 → 1.013,3 | 831 |
| Chess 0,45 | 1,848 (1,737–1,880) | 0,681 (0,679–0,688) | 1.513,8 → 1.247,1 | 2.832.777 |
| T10I4D100K 0,02 | 4,221 (3,918–4,350) | 1,417 (1,399–1,452) | 1.868,5 → 1.167,8 | 155 |

Cold dùng `bench/compare-cold-pilot.jl`, 3 process độc lập mỗi variant, xen kẽ thứ tự. Wall gồm startup, JIT, đọc, khai thác, ghi và stats; RSS là peak của process con gồm runtime Julia. Hai phạm vi warm/cold không trừ cho nhau.

| Dataset; minsup | Baseline cold median s (min–max) | Optimized cold median s (min–max) | Peak RSS median MiB: baseline → optimized |
|---|---:|---:|---:|
| Retail 0,004 | 7,810 (7,793–7,827) | 5,547 (5,349–5,556) | 676,4 → 553,3 |
| Chess 0,45 | 8,820 (8,789–8,849) | 7,584 (7,572–7,592) | 418,4 → 352,6 |
| T10I4D100K 0,02 | 8,399 (8,394–8,660) | 5,736 (5,735–5,754) | 593,3 → 717,3 |

Các điểm này cho thấy tín hiệu giảm thời gian trong điều kiện pilot, nhưng T10I4D100K tăng peak RSS khoảng 124 MiB. Chưa kết luận nguyên nhân hay hiệu quả trên các ngưỡng khác. Cần kiểm tra thêm Accidents, Mushroom, minsup thấp hơn và nhiều lần đo theo kế hoạch của Hiếu.

## Correctness

- Oracle vét cạn trên cơ sở nhỏ ngẫu nhiên seed `20261114`; trường hợp bitmap rank 1, 64, 65, 130, dữ liệu rỗng, duplicate và giao dịch vượt ranh giới word.
- Cả hai variant được đối chiếu SPMF 2.67a ở 5 snapshot/ngưỡng correctness trong manifest: 70/70 assertion pass; báo cáo máy đọc được ghi riêng số mẫu và chênh lệch của optimized. Đối chiếu thêm optimized với SPMF tại Chess 0,55 (574.998 mẫu), Retail 0,002 (2.691 mẫu) và Retail 0,004 (831 mẫu): missing=0, extra=0, support mismatch=0.
- Đây chưa bao phủ mọi ngưỡng và chưa phải benchmark so sánh chính thức.

## Tái lập

Chạy với đường dẫn Julia và dataset phù hợp; `REPO` là checkout chứa variant:

```text
julia --startup-file=no --project=. bench/compare-pilot.jl REPO INPUT MINSUP
julia --startup-file=no --project=. bench/compare-cold-pilot.jl REPO INPUT MINSUP
```

Log từng lần của pilot trên máy triển khai được giữ tại `results/optimized-pilot-*.log` và `results/optimized-cold-*.log`, không được Git theo dõi. Hãy sao lưu/chia sẻ riêng nếu cần kiểm toán. Chạy benchmark chính thức bằng harness với `variant = "baseline"` hoặc `"optimized"` trong config riêng, cùng checksum và thông số; không trộn dữ liệu khác máy hay khác phạm vi.

Bản sao báo cáo correctness của lần chạy này nằm tại `results/optimized-validation/correctness.toml` trong checkout chính; SHA256 `3ae4998ea3c3b2b9683ed976f987d2e8e3d81e3f5e497c9988c9c52e2117ef37`. File nằm trong `results/` bị Git bỏ qua, cần sao lưu riêng.
