# Baseline and Optimized Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an auditable, same-machine Baseline-vs-Optimized benchmark with reproducible data, five-dataset scalability, Chapter 2 reporting, and a checksummed handoff archive.

**Architecture:** Use the repository's `bench/run.jl` and `Bench.jl` for warm, cold, RSS, output-size, and CSV capture, with identical per-variant configs. Use a small exact-output pilot as the go/no-go gate, then run full measurements and build the report/archive from raw results without committing datasets or generated run data.

**Tech Stack:** Julia >= 1.9, TOML, CSV outputs from repository benchmark harness, Python plotting scripts already in `docs/validation`, SHA256.

**Spec:** `docs/superpowers/specs/2026-11-19-baseline-optimized-benchmark-design.md`

## Global Constraints

- Keep Baseline negFIN and CLI/SPMF format per `docs/baseline-contract.md`; do not add an FIM dependency.
- Use the same machine, dataset snapshots, minsup levels, and measurement scope for both variants.
- Verify all five dataset SHA256 values against `data/benchmark/manifest.toml` before measurements.
- Record commit, working-tree state, Julia version, OS, CPU, memory, Julia threads, config, and input checksums.
- Do not count timeout, output-cap, or error runs as completed measurements; retain and disclose their statuses.
- Report cold wall time as including startup/JIT/I/O, warm mining separately, peak RSS separately from total allocations, and output size from CLI output.
- Run scalability at exactly 10%, 25%, 50%, 75%, and 100% for all five datasets; pay particular attention to T10I4D100K peak RSS.
- Do not commit benchmark datasets, runtime, large itemset outputs, raw generated result directories, or secrets.
- Do not merge the PR; target `main` and report tests not run or failed.

## Review Focus

- Dataset missing or checksum mismatch: the run must stop before measurements; validate each manifest entry and dataset file.
- Baseline/Optimized output differences: the pilot gate must compare full normalized CLI output, not only counts.
- Scalability subsets differing between variants: both must use the same five fractions and matching subset SHA256 values.
- T10I4D100K resource growth: pilot all fractions with careful limits and log any RSS concern before full run.
- Incomplete/limited runs: summary and report must preserve timeout/output-cap/error state and avoid presenting them as successful data.

---

### Task 1: Prepare isolated benchmark branch, verify source data, and freeze configs

**Files:**
- Create: `bench/config-baseline-20261119.toml`
- Create: `bench/config-optimized-20261119.toml`
- Create: `results/handoff/benchmark-baseline-optimized-20261119/README.md` (local, ignored output; not committed)
- Test: `data/benchmark/manifest.toml` entries against local files (no test file)

**Interfaces:**
- Consumes: `origin/main`, `bench/config.toml`, `data/benchmark/manifest.toml`.
- Produces: two configs identical except `variant`; each sets `scalability_fractions = [0.1, 0.25, 0.5, 0.75, 1.0]` and `scalability_datasets` to all five manifest dataset names.

- [ ] **Step 1: Create a purpose branch from latest `origin/main`**

Run: `git status --short --branch; git fetch origin main; git switch -c test/baseline-optimized-benchmark origin/main`
Expected: clean worktree before switching and new branch based on fetched `origin/main`; stop if there are local changes or branch already exists and inspect rather than overwrite.

- [ ] **Step 2: Verify the five dataset files against manifest SHA256**

Run a PowerShell SHA256 check for `chess.txt`, `mushrooms.txt`, `retail.txt`, `accidents.txt`, and `T10I4D100K.txt` against their manifest values.
Expected: all five hashes match; record transaction counts/source URLs. If any file is missing or differs, stop and resolve the snapshot before measurement.

- [ ] **Step 3: Create paired frozen configs**

Copy `bench/config.toml` into two config files; set variants to `baseline` and `optimized`, set fractions to `[0.1, 0.25, 0.5, 0.75, 1.0]`, and set scalability datasets to `Chess`, `Mushroom`, `Retail`, `Accidents`, `T10I4D100K`. Keep selected minsup, timeout, output cap, repetitions, and ladder values equal.
Expected: TOML configs parse and diff only in `variant`.

- [ ] **Step 4: Capture initial machine/source metadata and run commands**

Create the local handoff README with branch/commit, Julia version, OS, CPU model/threads, total memory, benchmark configs, manifest hash, data hashes, and exact planned commands. Never include personal machine account identifiers.
Expected: metadata is complete, and `bench/` configs are the immutable run inputs.

### Task 2: Implement exact-output pilot gate and five-dataset scalability config validation

**Files:**
- Create: `bench/validate-pair.jl`
- Create: `test/test_bench_pair.jl`
- Modify: `test/runtests.jl`

**Interfaces:**
- Produces: `validate_pair(repo::String, input::String, minsup::String, output_dir::String) -> NamedTuple` with `baseline_sha256`, `optimized_sha256`, `baseline_patterns`, `optimized_patterns`, and `equal`; execute the CLI for both variants and compare exact output bytes.
- Test fixture: `data/toy/example.txt`, output files in a temporary directory.

- [ ] **Step 1: Add failing tests for exact output comparison and mismatch detection**

Test `validate_pair` on the toy fixture at minsup `0.4`: hashes and pattern counts match and `equal == true`. Test comparison helper with distinct fixture outputs: `equal == false`.
Expected: tests fail because the helper is not yet implemented.

- [ ] **Step 2: Run the focused test to confirm failure**

Run: `julia --startup-file=no --project=. test/runtests.jl`
Expected: the newly added pair-validation tests fail for the missing implementation; record output.

- [ ] **Step 3: Implement CLI pair validator**

Implement `validate_pair` in `bench/validate-pair.jl` using `bench/cold_run.jl`'s CLI options, distinct temp output paths for variants, output SHA256, and stats pattern counts. Ensure temp files are removed in `finally` and child exit errors fail validation.
Expected: no output is silently normalized; exact byte equality is required.

- [ ] **Step 4: Include focused test and validate all configs**

Include the test file from `test/runtests.jl`; add tests that both configs contain the five datasets and exact fractions. Run full suite.
Run: `julia --startup-file=no --project=. test/runtests.jl`
Expected: all tests pass; both config files parse with identical measurement settings.

### Task 3: Run checksum-gated pilot and approve full-run estimates

**Files:**
- Create: `results/handoff/benchmark-baseline-optimized-20261119/pilot/` (local, ignored output)
- Update: local handoff `README.md`

**Interfaces:**
- Consumes: Task 1 configs and Task 2 `validate_pair`.
- Produces: pilot logs, exact-output comparison results, per-variant timings/RSS/output sizes, go/no-go runtime estimates.

- [ ] **Step 1: Run exact-output correctness pilot on toy and a small real-dataset subset**

Run `bench/validate-pair.jl` against toy and 10% subsets for all five datasets at the selected scalability minsup; verify each subset SHA256 and both variants' exact output equality.
Expected: all outputs match. Stop on any mismatch or abnormal exit.

- [ ] **Step 2: Run paired warm/cold pilot, especially T10I4D100K fractions**

Run the harness with both configs for one repetition on the five datasets at representative selected minsup and all five scalability fractions; capture process stdout/stderr and per-run status. Keep output/time limits identical.
Expected: pilot data records timing, peak RSS, output bytes, and statuses. Do not promote pilot rows into full-run data.

- [ ] **Step 3: Estimate full-run duration and resource headroom**

Use pilot per-case duration and configured repetition counts to estimate total wall time; flag T10I4D100K RSS growth and any near-limit output/time cases. If estimates exceed available practical runtime or memory, present findings and request scope/limit adjustment before full run.
Expected: a documented go/no-go decision with no silent scope reduction.

### Task 4: Execute full paired warm, cold, and scalability measurements

**Files:**
- Create: `results/handoff/benchmark-baseline-optimized-20261119/full-run/` (local, ignored output)
- Update: local handoff `README.md`

**Interfaces:**
- Consumes: approved pilot gate and frozen configs.
- Produces: `runs.csv`, `phases.csv`, `summary.csv`, `env.toml`, raw stdout/stderr logs, subset data and subset SHA256 listing, plus a run ledger of failures.

- [ ] **Step 1: Execute full warm and cold scopes for all five datasets and selected minsup levels**

For each variant config, run the harness `--scope warm --dataset NAME` and `--scope cold --dataset NAME` for all five datasets. Use identical settings; record command, start/end time, exit status, and stdout/stderr per invocation.
Expected: each planned case is present; non-ok cases are retained and not treated as successful measurements.

- [ ] **Step 2: Execute full scalability scopes at all five fractions for all five datasets**

Run `--scope scalability --dataset NAME` for every manifest dataset under both variants. Verify generated subset transaction count and SHA256 match across variants before comparing metrics.
Expected: 25 fractions/dataset cases per variant have matching input hashes; T10I4D100K RSS and failures are explicitly surfaced.

- [ ] **Step 3: Reconcile run ledger and regenerate summaries**

Re-run summary generation on raw CSVs; reconcile planned versus actual cases, statuses, output bytes, and missing phases. Preserve failed-run logs.
Expected: no failure is dropped and summary rows include successful observations only while failure counts are reported separately.

### Task 5: Write Chapter 2 results, charts, and interpretation

**Files:**
- Create: `docs/report/chapter2.md`
- Create: `docs/validation/benchmark-baseline-optimized-results.md`
- Modify: `docs/validation/plot-benchmark.py` (only if current script cannot plot the paired results)
- Create: `docs/validation/figures/baseline-optimized-runtime.png`
- Create: `docs/validation/figures/baseline-optimized-rss.png`
- Create: `docs/validation/figures/baseline-optimized-scalability.png`

**Interfaces:**
- Consumes: validated full-run CSVs and environment metadata.
- Produces: Vietnamese report tables/plots and reproducible plot command; every chart source/metric/scope is identified.

- [ ] **Step 1: Derive comparison tables from raw runs**

Generate medians/ranges by variant, dataset, minsup, emit mode and scope; include counts of successful, timeout, output-cap, and error runs plus output size. Keep warm and cold scope definitions separate.
Expected: reported values can be traced to raw rows; no failed run contributes to successful medians.

- [ ] **Step 2: Generate runtime, peak RSS, and scalability charts**

Use existing plotting style and add only the needed plots. Include all five fractions and dataset labels; do not plot allocation totals as peak RAM.
Expected: plots are legible, units and variant labels are explicit, and each file can be regenerated from raw result files.

- [ ] **Step 3: Write Chapter 2 discussion and improvement suggestions**

Explain the method, machine/environment, dataset snapshot checksums, warm/cold/RSS/output-size definitions, limits, failed runs, measured speedups/memory tradeoffs, and scalability behavior. Highlight T10I4D100K memory behavior; label hypotheses as hypotheses. Add a discussion handoff section with questions for Đăng without claiming external coordination occurred.
Expected: every conclusion is supported by the shown data and limitations are plainly stated.

### Task 6: Build and verify reproducibility handoff archive

**Files:**
- Create: `results/handoff/benchmark-baseline-optimized-20261119.zip` (local, ignored output)
- Create: `results/handoff/benchmark-baseline-optimized-20261119/SHA256SUMS.txt` (local, ignored output)
- Modify: `docs/validation/benchmark-handoff.md`

**Interfaces:**
- Archive contains README, configs, manifest, source/commit metadata, raw CSVs, logs, subset checksums, report/plot sources and exact commands; it does not contain source datasets or large pattern outputs.
- Public doc records archive SHA256 and contents; archive remains a separately delivered local artifact.

- [ ] **Step 1: Assemble archive content and file-level checksums**

Copy only the reproducibility materials and raw results into the handoff directory; write `SHA256SUMS.txt` for included files.
Expected: no dataset, runtime, secret, or large itemset output is included.

- [ ] **Step 2: Create archive and verify integrity**

Create ZIP, test archive integrity, extract into a fresh temporary directory, and validate all SHA256 entries. Calculate ZIP SHA256 with `Get-FileHash -Algorithm SHA256`.
Expected: archive tests cleanly and every listed digest matches; record final archive digest.

- [ ] **Step 3: Update benchmark handoff documentation**

Update `docs/validation/benchmark-handoff.md` with new archive location/availability, SHA256, scope, commit, machine/Julia metadata, data verification, and known limitations. State clearly if local ZIP is not attached to the PR.
Expected: documentation does not imply ignored local files are present in a clone.

### Task 7: Final verification and PR preparation

**Files:**
- All tracked files from Tasks 1–6.

**Interfaces:**
- Produces: reviewed branch and PR targeting `main`; no merge.

- [ ] **Step 1: Run full repository tests and validate report artifacts**

Run: `julia --startup-file=no --project=. test/runtests.jl`
Run applicable Python tests: `python -I -m unittest discover -s docs/validation -p 'test_*.py'`.
Expected: tests pass; verify generated chart files and report links exist. Report unavailable runtimes/tests honestly.

- [ ] **Step 2: Review git diff and ensure generated/private data are excluded**

Run: `git status --short; git diff --check; git diff --stat`
Expected: only intended configs, code/tests, documentation and appropriate plots are tracked; no benchmark input files, raw outputs, logs containing private information, or archive accidentally committed.

- [ ] **Step 3: Commit changes and open a PR to `main`**

Commit each meaningful deliverable with descriptive messages ending in `Co-Authored-By: Claude Code <noreply@anthropic.com>`. Create PR with purpose, changes, benchmark scope, test output, dataset checksum verification, and link/availability of the separate ZIP; end PR body with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
Expected: PR exists and targets `main`; do not merge it.
