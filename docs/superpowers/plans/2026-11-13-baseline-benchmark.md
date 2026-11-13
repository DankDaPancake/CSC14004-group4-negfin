# Baseline Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm hook đo theo giai đoạn vào negFIN Baseline, xây harness benchmark (pilot, warm, cold, scalability) và tạo số liệu Chương 2 cho 5 tập SPMF.

**Architecture:** `mine_baseline` nhận callback tùy chọn `on_phase`, bọc 5 giai đoạn bằng `@timed`; CLI ghi bảng `[phases]` vào stats. Harness trong `bench/` là thư viện nhỏ `bench/Bench.jl` (đọc config, kiểm checksum, ghi CSV, chạy warm/cold) cùng các entry script mỏng. Kết quả ghi vào `results/bench/<run-id>/` (gitignored).

**Tech Stack:** Julia 1.12.0 (tương thích >= 1.9), chỉ Base + stdlib (`TOML`, `SHA`, `Random`, `Test`, `Statistics` không dùng — tự tính median).

**Spec:** `docs/superpowers/specs/2026-11-13-baseline-benchmark-design.md`

## Global Constraints

- Julia >= 1.9; không thêm package ngoài stdlib, không thêm dependency vào `Project.toml`.
- Giữ nguyên CLI và khóa stats cũ: `variant`, `julia_version`, `n_transactions`, `min_count`, `n_frequent_items`, `n_patterns`, `read_seconds`, `mine_write_seconds`, `total_seconds`.
- Hook không được đổi tập itemset, support hoặc thứ tự gọi `emit`.
- `bytes` là tổng byte cấp phát, không phải peak; peak RAM chỉ đến từ `Sys.maxrss()` của process cold.
- Không commit dataset, output itemset, `results/`, file con scalability hay Julia runtime.
- Julia dùng để chạy: `D:\.tools\julia-1.12.0\bin\julia.exe` (portable, ngoài repo). Trong các lệnh dưới đây `julia` là đường dẫn đó.
- Mọi lệnh test: `julia --startup-file=no --project=. test/runtests.jl [group]`.
- Nhánh: Task 1–2 trên `feature/phase-metrics` (từ `origin/main`); Task 3–6 trên `test/benchmark-harness` tạo từ `feature/phase-metrics`.
- Commit kết thúc bằng `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. Không còn item phổ biến (minsup cao, DB rỗng, chỉ metadata): hook chỉ gọi `:normalize`, `:prepare`; CLI vẫn ghi `[phases]` với 2 giai đoạn đó và không lỗi. → Task 1 (API), Task 2 (CLI empty input).
2. Input sai checksum hoặc thiếu file: harness dừng trước khi đo, báo tên tập và đường dẫn, không ghi dòng kết quả. → Task 3.
3. Process cold quá thời gian: process con bị kill, dòng kết quả có `status=timeout`, pilot dừng thang, không treo harness. → Task 4.
4. Output vượt `max_output_bytes`: pilot đánh dấu `output_cap` và dừng thang; file output lớn bị xóa. → Task 4.
5. Bộ đếm luôn bật làm chậm đường không hook: kiểm bằng phép đo trước/sau trên Chess 0.7 (spec mục 1). → Task 1 Step 7.

---

### Task 0: Môi trường Julia

**Files:** không có thay đổi trong repo.

- [ ] **Step 1: Xác nhận Julia portable**

Run: `D:\.tools\julia-1.12.0\bin\julia.exe --version`
Expected: `julia version 1.12.0`

- [ ] **Step 2: Chạy bộ test local hiện có trên `main`**

Run: `julia --startup-file=no --project=. test/runtests.jl`
Expected: các testset local PASS (I/O 27, BMC 21, NegNodeset 10, mining 18, CLI 32, differential 1004, reference 8).

---

### Task 1: Hook `on_phase` và bộ đếm trong `mine_baseline`

**Files:**
- Modify: `src/types.jl` (`MiningContext`)
- Modify: `src/negnodesets.jl` (`negative_pair`, `negative_extension`)
- Modify: `src/mine.jl` (`visit!`, `mine_baseline`)
- Create: `test/test_phases.jl`
- Modify: `test/runtests.jl` (`LOCAL_GROUPS`)

**Interfaces:**
- Produces:
  - `mine_baseline(db::TransactionDB, minsup::Rational{BigInt}; emit::Function, on_phase=nothing)::MiningSummary`
  - `on_phase(phase::Symbol, metrics::NamedTuple)` được gọi theo thứ tự `:normalize, :prepare, :build_bmc, :collect_nodesets, :mine`. Mọi `metrics` có `seconds::Float64`, `bytes::Int`, `gc_seconds::Float64`. Thêm: `:prepare` → `n_frequent_items::Int`; `:collect_nodesets` → `bmc_nodes::Int`; `:mine` → `negative_records_scanned::Int`, `n_patterns::Int`.
  - `MiningContext(prepared, nodesets, scanned::Base.RefValue{Int})`; constructor 2 đối số giữ lại, tạo `Ref(0)`.
  - `negative_pair(nodes, added_rank; scanned=nothing)` và `negative_extension(sibling_negative, current_rank; scanned=nothing)`: nếu `scanned isa Base.RefValue{Int}` thì cộng `length(input)` trước khi lọc. Chữ ký 2 đối số cũ không đổi (test NegNodeset dùng).

- [ ] **Step 1: Viết test thất bại `test/test_phases.jl`**

```julia
if !isdefined(Main, :collect_patterns)
    include(joinpath(@__DIR__, "helpers", "collect.jl"))
end

function mine_with_phases(db, minsup)
    emitted = Tuple{Vector{Int},Int}[]
    phases = Pair{Symbol,NamedTuple}[]
    summary = mine_baseline(db, minsup;
        emit=(items, support) -> push!(emitted, (items, support)),
        on_phase=(phase, metrics) -> push!(phases, phase => metrics))
    return (; emitted, phases, summary)
end

@testset "Phase metrics hook" begin
    toy = [[1,3,4], [2,3,5], [1,2,3,5], [2,5], [1,2,3,5]]
    rng = MersenneTwister(20261113)
    random_db = [sort!(unique(rand(rng, 1:12, rand(rng, 1:12)))) for _ in 1:40]
    cases = [(toy, big(2)//big(5)), ([[1,2,3], [1,2,3], [3]], big(2)//big(3)),
             (random_db, big(1)//big(5))]
    for (db, minsup) in cases
        plain = collect_patterns(db, minsup)
        hooked = mine_with_phases(db, minsup)
        @test hooked.emitted == plain.emitted          # same itemsets, supports and order
        @test first.(hooked.phases) == [:normalize, :prepare, :build_bmc, :collect_nodesets, :mine]
        @test all(m.seconds >= 0 && m.bytes >= 0 && m.gc_seconds >= 0 for m in last.(hooked.phases))
        metrics = Dict(hooked.phases)
        @test metrics[:prepare].n_frequent_items == hooked.summary.n_frequent_items
        @test metrics[:mine].n_patterns == length(hooked.emitted) == hooked.summary.n_patterns
        @test metrics[:mine].negative_records_scanned >= 0
        prepared = NegFIN.prepare([sort!(unique(t)) for t in db], hooked.summary.min_count)
        nodesets = NegFIN.collect_nodesets(NegFIN.build_bmc(prepared), length(prepared.items))
        @test metrics[:collect_nodesets].bmc_nodes == sum(length, nodesets)
    end
    @test Dict(mine_with_phases(toy, big(2)//big(5)).phases)[:mine].negative_records_scanned > 0
    for (db, minsup) in [([[1], [2]], big(1)//big(1)), (Vector{Int}[], big(1)//big(2))]
        empty = mine_with_phases(db, minsup)
        @test first.(empty.phases) == [:normalize, :prepare]
        @test isempty(empty.emitted)
    end
end
```

Thêm `"phases"` vào `LOCAL_GROUPS` trong `test/runtests.jl`, sau `"mining"`.

- [ ] **Step 2: Chạy test, xác nhận thất bại**

Run: `julia --startup-file=no --project=. test/runtests.jl phases`
Expected: FAIL/ERROR với `MethodError` hoặc "got unsupported keyword argument \"on_phase\"".

- [ ] **Step 3: Thêm bộ đếm vào `MiningContext` và các hàm lọc**

Trường mới `scanned::Base.RefValue{Int}` trong `src/types.jl`; constructor ngoài `MiningContext(prepared, nodesets) = MiningContext(prepared, nodesets, Ref(0))`. Keyword `scanned=nothing` cho hai hàm lọc trong `src/negnodesets.jl`. `visit!` truyền `scanned=ctx.scanned`.

- [ ] **Step 4: Thêm `on_phase` vào `mine_baseline`**

Mỗi giai đoạn: nếu `on_phase === nothing` chạy thẳng; ngược lại dùng `stats = @timed <expr>` rồi gọi `on_phase(phase, (seconds=stats.time, bytes=Int(stats.bytes), gc_seconds=stats.gctime, ...))`. Dùng một helper cục bộ `run_phase(f, phase, extra)` để tránh lặp; `extra` là hàm nhận kết quả và trả `NamedTuple` trường thêm. `bmc_nodes = sum(length, nodesets)`. Giai đoạn `:mine` là toàn bộ vòng `for (position, root) in enumerate(roots)`. Nếu `isempty(prepared.items)` trả về sau khi báo `:prepare`.

- [ ] **Step 5: Chạy test phases và toàn bộ bộ local**

Run: `julia --startup-file=no --project=. test/runtests.jl`
Expected: tất cả PASS, gồm testset "Phase metrics hook".

- [ ] **Step 6: Commit**

```powershell
git add src/types.jl src/negnodesets.jl src/mine.jl test/test_phases.jl test/runtests.jl
git commit -m "feat: report per-phase metrics from mine_baseline"
```

- [ ] **Step 7: Kiểm chi phí bộ đếm luôn bật**

Script tạm ngoài repo `D:\.tools\overhead.jl REPO`: `include` `REPO/src/NegFIN.jl`, đọc `data/benchmark/chess.txt`, warm-up 1 lần, đo 5 lần `@elapsed mine_baseline(db, parse_minsup("0.7"); emit=(i,s)->nothing)` (không hook), in từng giá trị. Bản trước: `git worktree add D:\.tools\wt-before origin/main`. Hai bản không load chung một process được (trùng tên module), nên chạy 3 cặp process xen kẽ before → after → before → … (tổng 15 lần đo mỗi bên), so median của 15 giá trị gộp.

Expected: median after ≤ 1.03 × median before. Ghi số vào mô tả PR. Nếu Chess 0.7 > 60 s/lần, chuyển sang mức có median 1–10 s và ghi lại. Nếu vượt 3%: đổi `visit!` để chỉ truyền `scanned` khi có hook (`MiningContext.scanned` thành `Union{Nothing,Base.RefValue{Int}}`), chạy lại Step 5, commit `perf: count scanned records only when hooked`. Xóa worktree tạm sau khi đo.

---

### Task 2: Ghi `[phases]` trong stats của CLI

**Files:**
- Modify: `src/cli.jl` (`main`)
- Modify: `test/test_cli.jl`
- Modify: `docs/baseline-contract.md` (mục Đo lường)

**Interfaces:**
- Consumes: `mine_baseline(...; on_phase)` từ Task 1.
- Produces: stats TOML có thêm `bmc_nodes::Int`, `negative_records_scanned::Int` (chỉ khi có `:collect_nodesets`/`:mine`) và bảng `phases.<name>` với `seconds`, `bytes`, `gc_seconds`. Task 4 đọc các khóa này.

- [ ] **Step 1: Thêm assertion thất bại trong `test/test_cli.jl`**

Sau `@test all(report[key] >= 0 ...)`:

```julia
@test sort(collect(keys(report["phases"]))) == sort(["normalize", "prepare", "build_bmc", "collect_nodesets", "mine"])
@test all(report["phases"][p][k] >= 0 for p in keys(report["phases"]) for k in ("seconds", "bytes", "gc_seconds"))
@test report["bmc_nodes"] > 0
@test report["negative_records_scanned"] >= 0
```

Ở trường hợp `empty_input`, thêm `--stats` vào một đường dẫn mới `empty_stats` và kiểm:

```julia
empty_report = TOML.parsefile(empty_stats)
@test sort(collect(keys(empty_report["phases"]))) == ["normalize", "prepare"]
@test !haskey(empty_report, "bmc_nodes")
```

- [ ] **Step 2: Chạy test CLI, xác nhận thất bại**

Run: `julia --startup-file=no --project=. test/runtests.jl cli`
Expected: FAIL tại `report["phases"]` (KeyError).

- [ ] **Step 3: Truyền `on_phase` trong `main` khi có `--stats`**

Thu `Dict{String,Any}` phases; `on_phase = options.stats === nothing ? nothing : (phase, m) -> ...`. Đưa `seconds/bytes/gc_seconds` vào `phases[string(phase)]`; `bmc_nodes` và `negative_records_scanned` lên cấp gốc của report. Giữ nguyên mọi khóa cũ.

- [ ] **Step 4: Cập nhật `docs/baseline-contract.md` mục Đo lường**

Thêm đoạn: `[phases]` chỉ có khi dùng `--stats`; giai đoạn và phạm vi theo bảng trong spec mục 1; `phases.mine` gồm thời gian ghi output qua `emit` nhưng không gồm rename; `bytes` là tổng cấp phát, không phải peak; khi không còn item phổ biến chỉ có `normalize`, `prepare`.

- [ ] **Step 5: Chạy toàn bộ bộ local**

Run: `julia --startup-file=no --project=. test/runtests.jl`
Expected: tất cả PASS.

- [ ] **Step 6: Commit, push, mở PR**

```powershell
git add src/cli.jl test/test_cli.jl docs/baseline-contract.md
git commit -m "feat: write phase metrics to CLI stats"
git push -u origin feature/phase-metrics
```

Mở PR vào `main`: mục đích, thay đổi, kết quả test, số đo overhead Task 1 Step 7; ghi cần Đăng review.

---

### Task 3: Thư viện harness, config, kiểm checksum, môi trường

**Files:**
- Create: `bench/Bench.jl`
- Create: `bench/config.toml`
- Create: `test/test_bench.jl`
- Modify: `test/runtests.jl` (`LOCAL_GROUPS` thêm `"bench"`)

**Interfaces:**
- Consumes: module `NegFIN` (include `src/NegFIN.jl`), `data/benchmark/manifest.toml`.
- Produces (module `Bench`):
  - `load_config(path::String)::Dict{String,Any}`
  - `manifest_entry(manifest::Dict, name::String)::Dict{String,Any}` — lỗi `ArgumentError` nếu không có tên.
  - `verify_input(path::String, sha256::String)::String` — trả digest; `error("Checksum mismatch for $path: ...")` nếu sai, `error("Missing input $path ...")` nếu thiếu.
  - `new_run_dir(root::String)::String` — tạo `root/YYYYMMDD-HHMMSS` (thêm hậu tố `-2`, `-3` nếu trùng).
  - `write_env(dir::String, repo::String, config_path::String, manifest::Dict, data_dir::String)::Nothing` — ghi `env.toml` theo spec mục 6.
  - `RUN_COLUMNS::Vector{String}`, `PHASE_COLUMNS::Vector{String}` — đúng thứ tự cột spec mục 6.
  - `append_csv(path::String, columns::Vector{String}, row::Dict{String,Any})::Nothing` — ghi header nếu file chưa có; ô thiếu để trống; chuỗi chứa `,` hoặc `"` được quote.
  - `median_of(xs::Vector{Float64})::Float64`

- [ ] **Step 1: Viết `bench/config.toml`**

```toml
variant = "baseline"
manifest = "data/benchmark/manifest.toml"
results_root = "results/bench"
pilot_timeout_seconds = 120
max_output_bytes = 2147483648
warm_repetitions = 5
warm_long_repetitions = 3
warm_long_threshold_seconds = 60
cold_repetitions = 3
cold_timeout_seconds = 1800
scalability_fractions = [0.2, 0.4, 0.6, 0.8, 1.0]
scalability_datasets = ["Accidents", "T10I4D100K"]

[ladders]
Chess = ["0.9", "0.85", "0.8", "0.75", "0.7", "0.65", "0.6", "0.55", "0.5"]
Retail = ["0.01", "0.008", "0.006", "0.005", "0.004", "0.003", "0.002", "0.001"]
Mushroom = ["0.8", "0.7", "0.6", "0.5", "0.4", "0.3", "0.2"]
Accidents = ["0.9", "0.85", "0.8", "0.75", "0.7", "0.65", "0.6", "0.5"]
T10I4D100K = ["0.02", "0.015", "0.01", "0.008", "0.006", "0.004", "0.002"]

# Filled after pilot (Task 6): 5-7 levels per dataset, and one level per scalability dataset.
[selected]

[scalability_minsup]
```

- [ ] **Step 2: Viết test thất bại `test/test_bench.jl`**

```julia
include(joinpath(ROOT, "bench", "Bench.jl"))

@testset "Benchmark harness library" begin
    mktempdir() do dir
        good = joinpath(dir, "toy.txt")
        cp(joinpath(ROOT, "data", "toy", "example.txt"), good)
        digest = bytes2hex(open(sha256, good))
        @test Bench.verify_input(good, digest) == digest
        @test_throws ErrorException Bench.verify_input(good, "0"^64)
        @test_throws ErrorException Bench.verify_input(joinpath(dir, "missing.txt"), digest)
        manifest = TOML.parsefile(joinpath(ROOT, "data", "benchmark", "manifest.toml"))
        @test Bench.manifest_entry(manifest, "Chess")["path"] == "chess.txt"
        @test_throws ArgumentError Bench.manifest_entry(manifest, "Nope")
        config = Bench.load_config(joinpath(ROOT, "bench", "config.toml"))
        @test Set(keys(config["ladders"])) == Set(["Chess", "Retail", "Mushroom", "Accidents", "T10I4D100K"])
        a = Bench.new_run_dir(dir); b = Bench.new_run_dir(dir)
        @test isdir(a) && isdir(b) && a != b
        csv = joinpath(dir, "runs.csv")
        Bench.append_csv(csv, ["x", "y", "z"], Dict{String,Any}("x" => 1, "z" => "a,b"))
        Bench.append_csv(csv, ["x", "y", "z"], Dict{String,Any}("y" => 2.5))
        @test readlines(csv) == ["x,y,z", "1,,\"a,b\"", ",2.5,"]
        @test Bench.median_of([3.0, 1.0, 2.0]) == 2.0
        @test Bench.median_of([4.0, 1.0, 2.0, 3.0]) == 2.5
        @test "variant" in Bench.RUN_COLUMNS && "phase" in Bench.PHASE_COLUMNS
        Bench.write_env(a, ROOT, joinpath(ROOT, "bench", "config.toml"), manifest, joinpath(ROOT, "data", "benchmark"))
        env = TOML.parsefile(joinpath(a, "env.toml"))
        @test env["julia_version"] == string(VERSION)
        @test haskey(env, "git_commit") && haskey(env, "git_dirty") && haskey(env, "config")
        @test haskey(env, "cpu_threads") && haskey(env, "total_memory_bytes")
    end
end
```

- [ ] **Step 3: Chạy, xác nhận thất bại**

Run: `julia --startup-file=no --project=. test/runtests.jl bench`
Expected: ERROR, không tìm thấy `bench/Bench.jl`.

- [ ] **Step 4: Viết `bench/Bench.jl`**

Module `Bench` dùng `TOML`, `SHA` và `Libc.strftime` cho tên thư mục/thời điểm (tránh thêm `Dates` vào `Project.toml`). `write_env` lấy git qua `read(\`git -C $repo rev-parse HEAD\`, String)` và `git status --porcelain`, ghi `cpu_name = Sys.CPU_NAME`, `cpu_model = first(Sys.cpu_info()).model`, `cpu_threads`, `julia_threads = Threads.nthreads()`, `total_memory_bytes`, `os = string(Sys.KERNEL, " ", Sys.MACHINE)`, `windows_version` (chỉ trên Windows, từ `cmd /c ver`), `started_at`, SHA256 từng file có trong `data_dir` theo manifest (thiếu thì ghi `missing`), và `config` là dict config đã đọc.

- [ ] **Step 5: Chạy toàn bộ bộ local**

Run: `julia --startup-file=no --project=. test/runtests.jl`
Expected: tất cả PASS, gồm "Benchmark harness library".

- [ ] **Step 6: Commit**

```powershell
git switch -c test/benchmark-harness feature/phase-metrics
git add bench/Bench.jl bench/config.toml test/test_bench.jl test/runtests.jl
git commit -m "test: add benchmark harness library and config"
```

---

### Task 4: Đo cold và pilot

**Files:**
- Create: `bench/cold_run.jl`
- Create: `bench/rss_floor.jl`
- Create: `bench/pilot.jl`
- Modify: `bench/Bench.jl`
- Modify: `test/test_bench.jl`

**Interfaces:**
- Consumes: Task 3 (`Bench.*`), stats TOML từ Task 2.
- Produces:
  - `bench/cold_run.jl ARGS...`: gọi `NegFIN.main(cli_args)` với `cli_args = ARGS` trừ cặp `--maxrss FILE`; sau đó ghi `maxrss_bytes = Sys.maxrss()` và `status` vào FILE (TOML); `exit` bằng mã của `main`.
  - `bench/rss_floor.jl FILE`: include `src/NegFIN.jl`, ghi `maxrss_bytes = Sys.maxrss()` vào FILE.
  - `Bench.run_cold(julia::Cmd, repo, input, output, stats, minsup; timeout_seconds, max_output_bytes)::Dict{String,Any}` — trả `status` (`ok|timeout|output_cap|error`), `process_wall_seconds`, `maxrss_bytes`, `output_bytes`, và mọi khóa của stats (gồm `phases`) nếu có. Kill process con khi quá timeout; nếu file output tạm (theo dõi thư mục của output) vượt `max_output_bytes` khi đang chạy thì kill và trả `output_cap`. Xóa output sau khi lấy kích thước.
  - `Bench.rss_floor(julia::Cmd, repo)::Int`
  - `Bench.cold_row(run_id, scope, dataset, fraction, digest, minsup, rep, result, floor)::Dict{String,Any}` và `Bench.phase_rows(...)::Vector{Dict{String,Any}}` — ánh xạ sang `RUN_COLUMNS`/`PHASE_COLUMNS` với `emit_mode="cli"`, `variant` từ config.
  - `bench/pilot.jl --dataset NAME [--config PATH] [--data-dir DIR] [--results-root DIR]`: kiểm checksum, chạy thang theo spec mục 4, ghi `pilot.csv` (cột `RUN_COLUMNS`, `scope="pilot"`) và `phases.csv`, in đề xuất 5–7 mức theo `Bench.select_levels`.
  - `Bench.select_levels(levels::Vector{Tuple{String,Float64}}; min_count=5, max_count=7, floor_seconds=0.05)::Vector{String}` — đầu vào là (minsup, mine_write_seconds) của các mức `ok` theo thứ tự thang; áp dụng quy tắc spec mục 4.

- [ ] **Step 1: Thêm test thất bại vào `test/test_bench.jl`**

```julia
@testset "Pilot level selection" begin
    levels = [("0.9", 0.001), ("0.85", 0.01), ("0.8", 0.04), ("0.75", 0.2), ("0.7", 1.0),
              ("0.65", 4.0), ("0.6", 15.0), ("0.55", 50.0), ("0.5", 110.0)]
    chosen = Bench.select_levels(levels)
    @test 5 <= length(chosen) <= 7
    @test "0.5" in chosen                       # slowest ok level kept
    @test count(in(["0.9", "0.85", "0.8"]), chosen) == 1   # only one level under 0.05 s
    @test "0.8" in chosen                       # the lowest minsup among fast levels
    @test chosen == sort(chosen; by=x -> -parse(Float64, x))
    @test Bench.select_levels(levels[1:4]) == ["0.8", "0.75"]   # fewer than 5: return all usable
end

@testset "Cold run smoke" begin
    mktempdir() do dir
        julia = `$(Base.julia_cmd()) --startup-file=no --project=$ROOT`
        input = joinpath(ROOT, "data", "toy", "example.txt")
        result = Bench.run_cold(julia, ROOT, input, joinpath(dir, "out.txt"), joinpath(dir, "stats.toml"), "0.4";
                                timeout_seconds=300, max_output_bytes=10^9)
        @test result["status"] == "ok"
        @test result["n_patterns"] == 15
        @test result["maxrss_bytes"] > 0 && result["process_wall_seconds"] > 0
        @test result["output_bytes"] > 0 && !isfile(joinpath(dir, "out.txt"))
        @test haskey(result["phases"], "mine")
        @test Bench.rss_floor(julia, ROOT) > 0
        capped = Bench.run_cold(julia, ROOT, input, joinpath(dir, "out2.txt"), joinpath(dir, "s2.toml"), "0.4";
                                timeout_seconds=300, max_output_bytes=10)
        @test capped["status"] == "output_cap"
        slow = Bench.run_cold(julia, ROOT, input, joinpath(dir, "out3.txt"), joinpath(dir, "s3.toml"), "0.4";
                              timeout_seconds=0.001, max_output_bytes=10^9)
        @test slow["status"] == "timeout"
    end
end
```

Ghi chú `output_cap` trên toy: output toy nhỏ, nên kiểm cap cũng phải áp dụng sau khi process kết thúc (`output_bytes > max_output_bytes` ⇒ `output_cap`), không chỉ khi đang chạy.

- [ ] **Step 2: Chạy, xác nhận thất bại**

Run: `julia --startup-file=no --project=. test/runtests.jl bench`
Expected: FAIL với `UndefVarError: select_levels`/`run_cold`.

- [ ] **Step 3: Viết `bench/cold_run.jl`, `bench/rss_floor.jl` và các hàm cold trong `Bench.jl`**

`run_cold`: `process = run(pipeline(cmd; stdout=devnull, stderr=errfile); wait=false)`, vòng `sleep(0.2)` kiểm `process_exited`, thời gian và kích thước output; quá hạn thì `kill(process)` rồi `wait`. Output CLI ghi qua file tạm rồi rename, nên trong lúc chạy kiểm tổng kích thước các file mới trong thư mục output.

- [ ] **Step 4: Viết `Bench.select_levels`**

Thuật toán:
1. Gộp các mức có giây < `floor_seconds` thành một mức: giữ mức cuối cùng (minsup nhỏ nhất) trong nhóm đó.
2. Nếu còn ≤ `max_count` mức: trả hết (kể cả khi < `min_count`; pilot sẽ cảnh báo cần chèn mức).
3. Nếu nhiều hơn: luôn giữ mức đầu và mức cuối; với `k = max_count - 2` mức giữa, chọn mức có log(giây) gần nhất với từng điểm chia đều giữa log(đầu) và log(cuối), không chọn trùng.
4. Trả theo thứ tự thang (minsup giảm dần).

- [ ] **Step 5: Viết `bench/pilot.jl`**

Dừng thang ở mức đầu tiên có `status != "ok"`. In bảng (minsup, min_count, n_patterns, output_bytes, mine_write_seconds, process_wall_seconds, maxrss_bytes, status) và đề xuất `select_levels`; nếu < 5 mức thì in cảnh báo "add intermediate levels to [ladders].NAME".

- [ ] **Step 6: Chạy toàn bộ bộ local**

Run: `julia --startup-file=no --project=. test/runtests.jl`
Expected: tất cả PASS. Nếu nhóm `bench` vượt ~60 s, chuyển nó thành opt-in: bỏ `"bench"` khỏi `LOCAL_GROUPS`, cho phép `test/runtests.jl bench` như `spmf`, ghi trong README.

- [ ] **Step 7: Commit**

```powershell
git add bench test/test_bench.jl test/runtests.jl
git commit -m "test: add cold process runner and minsup pilot"
```

---

### Task 5: Đo warm, scalability và tổng hợp

**Files:**
- Create: `bench/run.jl`
- Create: `bench/make_subsets.jl`
- Modify: `bench/Bench.jl`
- Modify: `test/test_bench.jl`

**Interfaces:**
- Consumes: Task 3, Task 4, `mine_baseline(...; on_phase)`.
- Produces:
  - `Bench.measure_warm(db::Vector{Vector{Int}}, minsup::String, emit_mode::Symbol, tmpdir::String)::Dict{String,Any}` — `emit_mode` là `:count` hoặc `:write`; gọi `GC.gc()` trước; trả `phases` (Dict phase ⇒ (seconds, bytes, gc_seconds)), `phases_total_seconds`, `n_patterns`, `n_frequent_items`, `min_count`, `bmc_nodes`, `negative_records_scanned`, `output_bytes` (chỉ `:write`; xóa file sau đo).
  - `Bench.warmup!(tmpdir)` — chạy toy ở cả hai chế độ.
  - `Bench.prefix_subset(input::String, fraction::Float64, output::String)::Int` — ghi `round(Int, fraction * n)` dòng dữ liệu đầu (dòng dữ liệu = dòng mà `read_spmf` không bỏ qua), trả số giao dịch đã ghi.
  - `Bench.summarize(run_dir::String)::Nothing` — đọc `runs.csv`, `phases.csv`, ghi `summary.csv` với median/min/max theo (variant, scope, dataset, fraction, minsup, emit_mode) cho `phases_total_seconds`, `process_wall_seconds`, `maxrss_bytes`; và theo thêm `phase` cho `seconds`, `bytes`, `gc_seconds`.
  - `bench/make_subsets.jl [--config PATH]`: tạo `results/bench/subsets/<Dataset>-<pct>.txt` cho mọi tập trong `scalability_datasets`, in SHA256 từng file.
  - `bench/run.jl --scope warm|cold|scalability --dataset NAME | --all [--config PATH] [--data-dir DIR] [--results-root DIR]`: dùng `[selected]` (warm/cold) hoặc `[scalability_minsup]` + `scalability_fractions` (scalability, cả warm và cold). Lỗi rõ ràng nếu config chưa có mức cho tập đó. Ghi `env.toml`, `runs.csv`, `phases.csv`, rồi `summarize`.

- [ ] **Step 1: Thêm test thất bại**

```julia
@testset "Warm measurement and subsets" begin
    mktempdir() do dir
        db = open(read_spmf, joinpath(ROOT, "data", "toy", "example.txt"))
        Bench.warmup!(dir)
        counted = Bench.measure_warm(db, "0.4", :count, dir)
        written = Bench.measure_warm(db, "0.4", :write, dir)
        @test counted["n_patterns"] == written["n_patterns"] == 15
        @test written["output_bytes"] == filesize(joinpath(ROOT, "data", "toy", "example.expected.txt"))
        @test !haskey(counted, "output_bytes") || counted["output_bytes"] == 0
        @test Set(keys(counted["phases"])) == Set(["normalize", "prepare", "build_bmc", "collect_nodesets", "mine"])
        @test isempty(filter(f -> endswith(f, ".txt"), readdir(dir)))
        sub = joinpath(dir, "sub.txt")
        @test Bench.prefix_subset(joinpath(ROOT, "data", "toy", "example.txt"), 0.6, sub) == 3
        @test open(read_spmf, sub) == open(read_spmf, joinpath(ROOT, "data", "toy", "example.txt"))[1:3]
    end
end
```

Kiểm `example.expected.txt` có cùng định dạng/byte như `write_itemset` (một dòng `items #SUP: n\n`); nếu file expected khác thứ tự nhưng cùng tổng byte thì assertion vẫn đúng. Nếu khác ký tự xuống dòng, đổi assertion thành so `sum(length(line)+1 for line in readlines(...))`.

- [ ] **Step 2: Chạy, xác nhận thất bại**

Run: `julia --startup-file=no --project=. test/runtests.jl bench`
Expected: FAIL với `UndefVarError: warmup!`.

- [ ] **Step 3: Viết `measure_warm`, `warmup!`, `prefix_subset`, `summarize`**

`measure_warm` dùng `on_phase` gom vào Dict; chế độ `:write` mở file trong `tmpdir`, emit gọi `NegFIN.write_itemset`. `read_seconds` đo ở `run.jl` một lần mỗi (tập, fraction), không trong `measure_warm`.

- [ ] **Step 4: Viết `bench/make_subsets.jl` và `bench/run.jl`**

Warm: đọc input (đo `read_seconds`), `warmup!`, rồi với mỗi minsup và mỗi chế độ: đo lần 1; số lần lặp = `warm_repetitions`, hoặc `warm_long_repetitions` nếu lần 1 > `warm_long_threshold_seconds` (lần 1 tính là một lần). Cold: `rss_floor` một lần mỗi run, mỗi cấu hình `cold_repetitions` lần với `cold_timeout_seconds`. Mọi dòng có `run_id` = tên thư mục run.

- [ ] **Step 5: Chạy toàn bộ bộ local và smoke trên toy**

Run: `julia --startup-file=no --project=. test/runtests.jl`
Expected: tất cả PASS.

- [ ] **Step 6: Commit**

```powershell
git add bench test/test_bench.jl
git commit -m "test: add warm, cold and scalability benchmark runner"
```

---

### Task 6: Chạy benchmark, chọn minsup, viết kết quả

**Files:**
- Modify: `bench/config.toml` (`[selected]`, `[scalability_minsup]`, có thể `[ladders]`)
- Create: `docs/validation/benchmark-baseline.md`
- Modify: `README.md` (mục benchmark: lệnh chạy, link tài liệu kết quả)

**Interfaces:**
- Consumes: `bench/pilot.jl`, `bench/run.jl`, `bench/make_subsets.jl`.

- [ ] **Step 1: Pilot Chess và Retail**

Run:
```powershell
julia --startup-file=no --project=. bench/pilot.jl --dataset Chess
julia --startup-file=no --project=. bench/pilot.jl --dataset Retail
```
Expected: mỗi lệnh in bảng thang và đề xuất mức; `pilot.csv` trong `results/bench/<run-id>/`. Nếu cảnh báo < 5 mức, thêm mức trung gian vào `[ladders]` và chạy lại.

- [ ] **Step 2: Pilot Mushroom, Accidents, T10I4D100K**

Run: `bench/pilot.jl --dataset <Name>` cho từng tập. Cùng tiêu chí như Step 1.

- [ ] **Step 3: Chốt mức vào config**

Ghi `[selected]` (5–7 mức mỗi tập theo đề xuất pilot) và `[scalability_minsup]` (Accidents, T10I4D100K: mức có warm `:mine` ở tập đầy đủ gần 10–60 s nhất; dùng `mine_write_seconds` pilot làm ước lượng ban đầu, kiểm lại bằng warm ở Step 4). Commit `bench/config.toml`: `test: select benchmark minsup levels from pilot`.

- [ ] **Step 4: Chạy warm, cold, scalability đầy đủ**

Run:
```powershell
julia --startup-file=no --project=. bench/make_subsets.jl
julia --startup-file=no --project=. bench/run.jl --all
```
Chạy khi máy rảnh, cắm điện, không chạy tác vụ nặng khác. Ghi lại thời gian bắt đầu/kết thúc. Expected: `runs.csv`, `phases.csv`, `summary.csv`, `env.toml` trong thư mục run; không có dòng `status=error`.

- [ ] **Step 5: Viết `docs/validation/benchmark-baseline.md`**

Gồm: cấu hình máy/phiên bản/commit (từ `env.toml`), lệnh chạy, checksum dữ liệu, bảng pilot từng tập, bảng chính (minsup, min_count, n_patterns, output MiB, warm median từng giai đoạn, write−count, byte cấp phát, GC, cold wall, peak RSS thô và trừ nền), bảng scalability, nhận xét điểm nghẽn trả lời 4 câu hỏi spec mục 10. Ghi phạm vi đo ở đầu mỗi bảng. Ghi rõ giả thuyết nào số liệu không ủng hộ.

- [ ] **Step 6: Cập nhật README, chạy bộ local, commit, push, mở PR**

Run: `julia --startup-file=no --project=. test/runtests.jl`
Expected: tất cả PASS.

```powershell
git add bench/config.toml docs/validation/benchmark-baseline.md README.md
git commit -m "docs: record baseline benchmark results"
git push -u origin test/benchmark-harness
```

PR vào `main`, ghi phụ thuộc `feature/phase-metrics` nếu chưa merge.

---

### Task 7: Nguồn Hugging Face/Kaggle

**Files:**
- Modify: `docs/validation/benchmark-baseline.md` (mục nguồn dữ liệu)
- Modify: `data/benchmark/manifest.toml` (thêm `mirror_url` chỉ khi có bản khớp checksum)

- [ ] **Step 1: Tra cứu**

Với từng tên file (`chess.txt`, `mushrooms.txt`, `retail.txt`, `accidents.txt`, `T10I4D100K.txt`) và tên tập: tìm qua `https://huggingface.co/api/datasets?search=<term>` và tìm kiếm Kaggle. Ghi lại từng ứng viên: URL, giấy phép ghi trên trang.

- [ ] **Step 2: Đối chiếu checksum**

Tải từng ứng viên vào thư mục tạm riêng ngoài repo (mỗi ứng viên một thư mục trống), tính SHA256, so với manifest. Không thực thi gì từ file tải về.

- [ ] **Step 3: Ghi kết quả và đề xuất**

Bảng ứng viên (URL, file, SHA256, khớp/không, khác biệt nếu không khớp như số dòng). Thêm `mirror_url` vào manifest cho tập có bản khớp. Nếu thiếu, ghi đề xuất tạo dataset Hugging Face của nhóm (cần nhóm đồng ý, kiểm điều khoản phân phối). Chạy `test/runtests.jl` (manifest vẫn parse được), commit `docs: record public mirrors for benchmark datasets`, push lên nhánh PR của Task 6.
