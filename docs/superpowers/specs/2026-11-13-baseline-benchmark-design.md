# Thiết kế benchmark negFIN Baseline

Ngày: 13/11/2026. Người phụ trách benchmark: Hiếu. Hook trong `src/` cần Đăng review.

## Mục đích

Tạo số liệu Chương 2 cho Baseline: runtime theo minsup, thời gian và cấp phát theo từng giai đoạn, peak RAM, output size và scalability trên 5 tập SPMF trong `data/benchmark/manifest.toml`. Số liệu này cũng là mốc đối chứng cho bản Optimized, nên cách đo phải dùng lại được nguyên vẹn cho `--variant optimized` sau này.

Mỗi con số phải gắn với phạm vi đo, cấu hình máy, phiên bản Julia, commit và checksum dữ liệu.

## Mục tiêu, ngoài phạm vi, điều cần tránh

Mục tiêu:

- Hook đo theo giai đoạn trong `mine_baseline`, không đổi output hay hành vi khi không dùng hook.
- Harness tái lập được: pilot chọn minsup, đo warm trong cùng process, đo cold toàn process kèm peak RAM, thí nghiệm scalability.
- 5–7 mức minsup cho mỗi tập trong 5 tập; scalability trên Accidents và T10I4D100K.
- Tra cứu nguồn công khai Hugging Face/Kaggle cho 5 snapshot, đối chiếu checksum với manifest và đề xuất nguồn ổn định.

Ngoài phạm vi đợt này:

- Bản Optimized, biểu đồ cho báo cáo, so tốc độ với SPMF.
- Thí nghiệm độ dài giao dịch (cần dữ liệu tổng hợp; để đợt sau).
- Online Retail, Splice-junction: thuộc phần ứng dụng của Tiến.

Điều cần tránh (sai dù chạy được):

- Trộn phạm vi đo: so thời gian warm với cold, hoặc gọi tổng cấp phát là peak RAM.
- So thời gian Julia với SPMF trong cùng bảng như kết luận nhanh/chậm.
- Hook làm thay đổi tập itemset, support hoặc thứ tự gọi `emit`.
- Commit dataset, output itemset hay thư mục `results/`.

## Ràng buộc

- Julia >= 1.9, chỉ Base và stdlib (`Project.toml` hiện có `Random`, `SHA`, `TOML`, `Test`). Không thêm package bên thứ ba; CSV ghi thủ công.
- Giữ nguyên CLI và các khóa stats hiện có (`test/test_cli.jl` kiểm tra `read_seconds`, `mine_write_seconds`, `total_seconds`, `n_patterns`, `min_count`).
- Nhánh riêng từ `origin/main`, PR vào `main`, chạy `julia --startup-file=no --project=. test/runtests.jl` trước khi mở PR (AGENTS.md).
- Máy đo hiện tại: Intel Core i5-13600K (14 core: 6P + 8E, 20 luồng), 31,75 GiB RAM, Windows 11 Pro 10.0.26200 x64. Máy chưa có Julia trong PATH; phải cài Julia 1.12.0 portable ngoài repo trước khi đo, giống cách ghi trong `docs/implementation-record.md`.
- 5 file dữ liệu đã tải về `data/benchmark/` và khớp SHA256 trong manifest (13/11/2026).

## Các hướng đã cân nhắc

1. **Script riêng gọi lại các hàm nội bộ** (`prepare`, `build_bmc`, `collect_nodesets`, `visit!`). Không đụng `src/`, nhưng script phải chép thứ tự bước của `mine_baseline` và có thể lệch khi Đăng sửa code.
2. **Hook trong `src/`** — được chọn. Số liệu đo đúng đường chạy thật và dùng lại được cho Optimized; đổi lại phải sửa code thuật toán và cần review.

Trong hướng 2 có hai cách gắn hook:

- **A. Callback tùy chọn `on_phase`** — được chọn. Không đo gì khi `on_phase === nothing`; API và test cũ giữ nguyên.
- B. Luôn đo và trả trong `MiningSummary`. Đơn giản hơn nhưng phải sửa struct/constructor đang dùng trong test, và API luôn chịu chi phí đo.

## Thiết kế

### 1. Hook theo giai đoạn (`src/mine.jl`)

```julia
mine_baseline(db, minsup; emit, on_phase=nothing)
```

Khi `on_phase !== nothing`, mỗi giai đoạn được bọc bằng `@timed` và callback được gọi một lần sau giai đoạn đó, đúng thứ tự:

| Giai đoạn | Phạm vi | Trường thêm |
|---|---|---|
| `:normalize` | copy, kiểm tra ID dương, `sort!(unique(...))` từng giao dịch | — |
| `:prepare` | `prepare(normalized, minimum)` | `n_frequent_items` |
| `:build_bmc` | `build_bmc(prepared)` | — |
| `:collect_nodesets` | `collect_nodesets(...)` | `bmc_nodes` |
| `:mine` | toàn bộ vòng `visit!` trên các root, gồm thời gian của `emit` | `negative_records_scanned`, `n_patterns` |

Mọi lần gọi nhận `on_phase(phase::Symbol, metrics::NamedTuple)` với ít nhất `seconds`, `bytes` (tổng byte cấp phát trong giai đoạn, không phải peak) và `gc_seconds`.

- `bmc_nodes`: số node BMC không tính root, bằng `sum(length, nodesets)`.
- `negative_records_scanned`: tổng độ dài vector đầu vào của mọi lần gọi `negative_pair` và `negative_extension`. Đây là chỉ báo khối lượng lọc NegNodeset.
- Nếu không còn item phổ biến (`isempty(prepared.items)`), chỉ gọi `:normalize` và `:prepare`, rồi trả về như hiện nay.

Bộ đếm `negative_records_scanned` nằm trong `MiningContext` (`Base.RefValue{Int}`) và luôn được cộng, kể cả khi không có hook. Đây là lựa chọn của người thiết kế, khác với điều đã nói trong trao đổi là "chỉ tính khi có hook": mỗi lần cộng chỉ là một phép cộng số nguyên, đặt cạnh một lần lọc vốn đã cấp phát vector mới, nên giữ một đường code duy nhất đơn giản hơn.

Điều kiện chấp nhận (lựa chọn của người thiết kế): đo toàn bộ lời gọi `mine_baseline` không hook, emit chế độ `count`, trên Chess ở minsup 0.7 (mức mining cỡ giây, tránh nhiễu mức mili giây ở 0.9). Commit trước và sau thay đổi, cùng process đã warm-up, 15 lần mỗi bên xen kẽ trước/sau. Median sau không được chậm hơn median trước quá 3%. Nếu vượt, chuyển sang chỉ đếm khi có hook. Nếu 0.7 không chạy xong dưới 60 s, dùng mức gần nhất trong thang pilot có median 1–10 s.

### 2. Stats của CLI (`src/cli.jl`)

Khi có `--stats`, CLI truyền `on_phase` và ghi thêm, không đổi khóa cũ:

```toml
bmc_nodes = 12345
negative_records_scanned = 678901

[phases.normalize]
seconds = 0.01
bytes = 1048576
gc_seconds = 0.0
# ... tương tự cho prepare, build_bmc, collect_nodesets, mine
```

Không có `--stats` thì không truyền hook. Cập nhật `docs/baseline-contract.md` mục Đo lường: `phases.mine` gồm thời gian ghi output qua `emit`, nhưng không gồm rename file.

### 3. Hai phạm vi đo

| Phạm vi | Đo gì | Cách đo |
|---|---|---|
| **Warm, cùng process** | thời gian, byte cấp phát, GC theo từng giai đoạn; mining thuần và chi phí ghi | gọi `mine_baseline` với `on_phase`, sau warm-up |
| **Cold, toàn process** | wall-clock toàn process (gồm startup/JIT/I/O), peak RSS | process con chạy CLI, process cha đo thời gian |

Warm, mỗi cấu hình (tập, tỷ lệ dữ liệu, minsup):

- Warm-up: đọc và khai thác `data/toy/example.txt` ở cả hai chế độ emit để JIT biên dịch đủ method (cùng kiểu đối số).
- Đọc input một lần bằng `read_spmf`, đo riêng làm `read_seconds`.
- Hai chế độ emit:
  - `count`: emit chỉ tăng bộ đếm. `phases.mine` là thời gian mining thuần (vẫn gồm tạo vector ID trong `emit_family!`).
  - `write`: emit gọi `write_itemset` vào file thật trong `results/bench/<run-id>/tmp/`, giống CLI. Hiệu `mine(write) - mine(count)` là ước lượng chi phí định dạng và ghi output.
- `GC.gc()` trước mỗi lần đo. 5 lần đo mỗi chế độ; nếu lần đo đầu > 60 s thì chỉ đo 3 lần. Báo median, min, max.
- Số itemset và tổng byte output ghi lại từ chế độ `write`; xóa file output sau mỗi lần để tiết kiệm đĩa.

Cold, mỗi cấu hình:

- `bench/cold_run.jl` là entry point riêng: gọi `NegFIN.main(args)` y như `run.jl`, sau đó ghi `Sys.maxrss()` (peak resident set của toàn process, gồm runtime Julia) ra TOML cạnh stats.
- Process cha đo wall-clock từ lúc khởi chạy đến khi process con kết thúc, có timeout.
- Đo thêm "nền RSS": process chỉ load module rồi ghi `Sys.maxrss()`. Báo peak RSS thô và peak RSS trừ nền, ghi rõ đây là ước lượng.
- 3 lần mỗi cấu hình, báo median, min, max.

### 4. Chọn minsup (pilot)

Pilot trên Chess và Retail trước, sau đó áp dụng cùng quy tắc cho Mushroom, Accidents, T10I4D100K.

- Mỗi tập có một thang ứng viên giảm dần, bắt đầu từ minsup trong manifest (khởi điểm, chỉnh được trong `bench/config.toml`):
  - Chess: 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50
  - Retail: 0.010, 0.008, 0.006, 0.005, 0.004, 0.003, 0.002, 0.001
  - Mushroom: 0.80, 0.70, 0.60, 0.50, 0.40, 0.30, 0.20
  - Accidents: 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.50
  - T10I4D100K: 0.020, 0.015, 0.010, 0.008, 0.006, 0.004, 0.002
- Mỗi mức chạy cold một lần với timeout `T_max = 120 s` cho wall-clock process (chỉnh trong config). Dừng thang khi gặp timeout, khi output vượt `max_output_bytes = 2 GiB`, hoặc khi hết thang.
- Ghi mỗi mức: min_count, số itemset, byte output, wall-clock, peak RSS, `mine_write_seconds` và `phases.*` từ stats của process con, trạng thái (ok/timeout/output_cap).
- Quy tắc chọn (lựa chọn của người thiết kế): trải mức theo `mine_write_seconds` trong stats, không theo wall-clock, vì wall-clock cold gồm vài giây startup/JIT cố định (`run.jl` dùng `include`, không precompile) làm các mức dễ trông như nhau. Lấy 5–7 mức đã chạy `ok`, gồm mức có `mine_write_seconds` nhỏ nhất và lớn nhất, các mức ở giữa trải đều theo log(`mine_write_seconds`). Các mức có `mine_write_seconds` < 0,05 s chỉ giữ lại một mức (mức thấp nhất trong nhóm đó). Nếu có ít hơn 5 mức `ok`, chèn thêm mức trung gian vào config và chạy pilot lại phần thiếu.
- `mine_write_seconds` của lần cold vẫn chứa JIT cho đường khai thác; chỉ dùng để xếp hạng mức, không đưa vào bảng kết quả.
- Lưu lựa chọn cuối vào `bench/config.toml` (commit), kèm bảng pilot làm bằng chứng trong tài liệu kết quả.

### 5. Scalability

- Tập: Accidents và T10I4D100K.
- Tỷ lệ: 20%, 40%, 60%, 80%, 100% giao dịch, lấy **tiền tố** (n dòng dữ liệu đầu tiên), không ngẫu nhiên, nên tái lập được mà không cần seed.
- `bench/make_subsets.jl` tạo file con trong `results/bench/subsets/` và ghi SHA256 của từng file con vào kết quả. Không commit file con.
- Minsup tương đối cố định cho mỗi tập: mức có runtime warm ở tập đầy đủ gần 10–60 s nhất trong thang đã chọn. min_count tự co giãn theo N.
- Đo cả warm và cold như mục 3.

### 6. Ghi kết quả

Mỗi lần chạy harness tạo `results/bench/<YYYYMMDD-HHMMSS>/` (đã gitignore), chứa:

- `env.toml`: Julia `VERSION`, `Sys.CPU_NAME`, `Sys.CPU_THREADS`, `Threads.nthreads()`, `Sys.total_memory()`, hệ điều hành, tên CPU từ hệ thống, commit `git rev-parse HEAD` và trạng thái sạch/bẩn của working tree, SHA256 của 5 file dữ liệu, thời điểm chạy, nội dung `bench/config.toml` đã dùng.
- `runs.csv`: một dòng mỗi lần đo. Cột: `run_id, variant, scope (warm|cold|pilot), dataset, fraction, input_sha256, n_transactions, minsup, min_count, n_frequent_items, n_patterns, emit_mode (count|write|cli), repetition, read_seconds, phases_total_seconds, bmc_nodes, negative_records_scanned, output_bytes, process_wall_seconds, maxrss_bytes, rss_floor_bytes, status`. Cột không áp dụng để trống.
- `phases.csv`: dạng dài, một dòng mỗi giai đoạn của mỗi lần đo: `run_id, variant, scope, dataset, fraction, minsup, emit_mode, repetition, phase, seconds, bytes, gc_seconds`.
- `summary.csv`: median/min/max theo (variant, scope, dataset, fraction, minsup, emit_mode), và theo phase cho dữ liệu `phases.csv`.

Lựa chọn của người thiết kế cho tương thích với Optimized: harness ghi cột `variant` (hiện luôn là `baseline`) và lưu giai đoạn ở dạng dài, nên không bị gắn chặt vào 5 tên giai đoạn của Baseline. Hợp đồng chung cho mọi variant chỉ là: `mine_baseline`/hàm tương ứng nhận `on_phase`, gọi với `NamedTuple` có `seconds`, `bytes`, `gc_seconds`, và có một giai đoạn tên `:mine`. Optimized có thể có tên giai đoạn khác; so sánh giữa hai variant dùng tổng thời gian, `:mine`, peak RSS và tổng byte cấp phát. Đăng quyết định tên giai đoạn của Optimized khi thiết kế bản đó.

Một tài liệu kết quả tay viết, `docs/validation/benchmark-baseline.md`, tóm tắt bảng chính, ghi phạm vi đo và nhận xét điểm nghẽn ban đầu. Commit tài liệu này cùng `summary.csv` dạng nhỏ nếu nhóm muốn; không commit `runs.csv` nếu lớn.

### 7. Lệnh chạy (dự kiến)

```powershell
julia --startup-file=no --project=. bench/pilot.jl --dataset Chess
julia --startup-file=no --project=. bench/run.jl --scope warm --dataset Chess
julia --startup-file=no --project=. bench/run.jl --scope cold --dataset Chess
julia --startup-file=no --project=. bench/run.jl --scope scalability --dataset Accidents
julia --startup-file=no --project=. bench/run.jl --all
```

Mọi harness kiểm tra SHA256 input theo manifest trước khi đo và dừng với lỗi nếu không khớp.

### 8. Kiểm thử

- Nhóm test mới `phases` trong `test/test_phases.jl`, thêm vào `LOCAL_GROUPS`:
  - Có hook và không hook cho cùng tập itemset/support và cùng thứ tự `emit` trên toy, ví dụ promotion và một CSDL ngẫu nhiên có seed cố định.
  - Thứ tự và tập tên giai đoạn đúng; các trường không âm; `bmc_nodes == sum(length, collect_nodesets(...))`; `n_patterns` trong `:mine` bằng số lần emit.
  - Trường hợp không có item phổ biến chỉ gọi `:normalize`, `:prepare`.
- `test_cli.jl`: stats có bảng `phases` đủ 5 giai đoạn, giữ các khóa cũ.
- Smoke test harness trên toy (warm 1 lần, cold 1 lần, pilot 1 mức) với thư mục kết quả tạm; chạy trong bộ local nếu tổng thời gian dưới vài giây, ngược lại thành nhóm opt-in `bench`.

### 9. Nguồn Hugging Face/Kaggle

Tìm kiếm ngày 13/11/2026 chưa thấy repo công khai có đúng 5 snapshot với checksum khớp manifest.

- Kiểm tra lại có hệ thống trên Hugging Face (`api/datasets?search=`) và Kaggle cho từng tên file; tải, tính SHA256, ghi kết quả khớp/không khớp vào tài liệu kết quả.
- Phạm vi đợt này chỉ là tra cứu, đối chiếu checksum và đề xuất. Nếu không có bản khớp, đề xuất nhóm tự tạo dataset repo công khai trên Hugging Face chứa đúng 5 file và README ghi nguồn SPMF/FIMI, sau khi kiểm tra điều khoản phân phối lại. Việc upload là hành động công khai, cần nhóm đồng ý trước và không nằm trong điều kiện hoàn thành đợt này.
- Thêm trường `mirror_url` cho từng mục trong manifest khi có link ổn định; test SPMF hiện chỉ đọc các trường đã biết nên không bị ảnh hưởng.

### 10. Nhận xét điểm nghẽn

Tài liệu kết quả trả lời bằng số liệu:

- Giai đoạn nào chiếm phần lớn thời gian warm ở từng mức minsup (thường kỳ vọng `:mine` ở minsup thấp, `:normalize`/`:prepare`/BMC ở minsup cao hoặc tập thưa lớn như Retail).
- `negative_records_scanned` và số itemset tăng theo minsup như thế nào, có giải thích được runtime `:mine` hay không.
- Tỷ lệ chi phí ghi output (`write - count`) trên tổng.
- Tỷ lệ byte cấp phát/GC trong `:mine`, gợi ý cho Optimized (bitmap BigInt, vector NegNodeset mới mỗi lần lọc).

Kỳ vọng trong ngoặc là giả thuyết, không được ghi thành kết luận nếu số liệu không ủng hộ.

## Thứ tự triển khai và nhánh

1. Cài Julia 1.12.0 portable ngoài repo; chạy bộ test local hiện có để xác nhận môi trường.
2. `feature/phase-metrics`: hook, bộ đếm, stats CLI, test, cập nhật contract. PR riêng, Đăng review.
3. `test/benchmark-harness` (tạo từ nhánh 2 nếu chưa merge, ghi rõ trong PR): `bench/`, config, smoke test.
4. Chạy pilot Chess, Retail → chốt thang; pilot 3 tập còn lại.
5. Chạy warm, cold, scalability đầy đủ; viết `docs/validation/benchmark-baseline.md`.
6. Tra cứu và đối chiếu nguồn HF/Kaggle; đề xuất mirror nếu cần.

## Phần để người triển khai tự quyết

- Tên file và cấu trúc bên trong `bench/`, miễn là các lệnh ở mục 7 làm được việc tương ứng.
- Cách ghi CSV (escape, định dạng số), cách xử lý timeout process con trên Windows và Linux.
- Có đặt CPU affinity vào P-core hay không. Mặc định chỉ ghi nhận máy có lõi lai P/E, không ép affinity; nếu đặt, ghi vào `env.toml`.
- Tinh chỉnh thang minsup ứng viên khi pilot cho thấy mức khởi điểm quá chậm hoặc quá nhanh.
