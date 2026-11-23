# SPMF–Julia Cold Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a reproducible, newly measured SPMF NegFIN versus Julia Optimized comparison and evidence-backed Chapter 2/handoff.

**Architecture:** Python standard-library tooling launches both real CLIs sequentially, measures whole-process wall time and Windows native peak working set, and saves append-only provenance/logs. A separate bounded-memory canonical validator compares outputs outside timing; reporting consumes only verified, complete three-repetition groups from the new campaign.

**Tech Stack:** Python 3.12.10 standard library (tomllib, unittest, ctypes, subprocess, heapq), Julia 1.12.0, compatible Java/SPMF to be located and verified; existing report figure tooling where available.

**Spec:** `docs/superpowers/specs/2026-11-22-spmf-julia-cold-benchmark-design.md` (user approved 2026-11-22).

## Global Constraints

- Work on `test/spmf-julia-cold-benchmark`, based on `origin/main` at `70ad97c`; no algorithm changes or direct main writes.
- No commits, pushes, PR creation, external handoff or runtime downloads without authorization. Keep changes local for review.
- Exactly five manifest snapshots and seven `[selected]` minsups each; Julia Optimized only for new comparison: 35 × 3 × 2 = 210 main attempts, plus separate pilots.
- Julia one thread; JVM `-XX:ActiveProcessorCount=1 -Xmx4g`; record flags, do not describe Java heap as an equivalent RSS cap.
- New process cold, not cleared filesystem caches. Whole-process monotonic wall includes startup/JIT/read/write/exit, excludes validation/reporting.
- Timeout 1,800 s/process, output 2 GiB/process, monitored RSS 8 GiB/process; record monitor interval/overshoot caveat and check final values.
- Validation payload budget 64 MiB/chunk, merge fan-in 32, scratch cap 16 GiB; check at least 20 GiB free before large runs and validation. Limits are configuration, not silently changed mid-campaign.
- Pilot confirms `ceil(N × minsup)` and exact patterns/support before main; no unresolved threshold or output mismatches on published points.
- Raw, logs, env, datasets, jars, runtime and large output stay outside Git. New campaign owns only its new files; preserve old packages.
- Run Julia suite before proposing PR and report failures/skips honestly. Load dataviz before chart code.

## Review Focus

1. A child exits before the first poll: retain a valid Windows process handle and collect its true peak RSS and exit status (Task 2).
2. A duplicate itemset has different support and sits across merge chunks: reject the itemset rather than treating two distinct lines as valid (Task 1).
3. Same minsup text yields a different Java floating-point ceiling: fail preflight/pilot, preserve argv, do not publish a mismatched point (Task 3).
4. Resume sees a partial CSV line, stale output or changed source: fail safely without reusing/overwriting evidence (Task 3).
5. Three rows exist but include errors, mixed provenance or repeated repetition numbers: reject aggregate completeness, never manufacture a median (Task 4).

## File structure

- Create `bench/spmf_validate.py`: strict record parsing, bounded external sorting/merge, duplicate detection, canonical digest and exact comparison.
- Create `bench/spmf_process.py`: child process lifetime, logs, monotonic wall, Windows working-set metrics and resource guards.
- Create `bench/spmf_campaign.py`: preflight, frozen manifest/config/source provenance, pilot, paired main scheduling, CSV evidence, resume and validation lifecycle; CLI entry point.
- Create `bench/config-spmf-julia-20261122.toml`: explicit settings and exact selected levels copied from existing frozen config.
- Create `bench/tests/test_spmf_validate.py`, `test_spmf_process.py`, `test_spmf_campaign.py`: import adjacent modules explicitly by file location or controlled absolute sys.path; no dependency install.
- Create `docs/validation/summarize-spmf-julia.py` and `test_summarize_spmf_julia.py`: strict grouping, small summary CSV/JSON, report figures and local ZIP checksums.
- Create `docs/validation/benchmark-spmf-julia-results.md`: new comparison methods, provenance, results/failed-point ledger, source verification and reproduction.
- Modify `docs/report/chapter2.md`, `docs/validation/benchmark-handoff.md`; add report PNG/PDF under `docs/report/figures/` only after measured data exist.

---

### Task 1: Bounded-memory exact output validation

**Files:** `bench/spmf_validate.py`, `bench/tests/test_spmf_validate.py`.

**Interfaces:**
- `parse_record(line: str, *, min_count: int, n_transactions: int) -> tuple[tuple[int, ...], int] | None`: comments/blank -> None; strict positive distinct items, support within [min_count, N].
- `canonicalize(source: Path, destination: Path, scratch: Path, *, min_count: int, n_transactions: int, chunk_bytes: int = 67108864, fan_in: int = 32, scratch_cap_bytes: int = 17179869184) -> dict`: create canonical sorted stream; return count, canonical_sha256 and source_sha256. Destination must be fresh; reject duplicate itemset independently of support.
- `compare_canonical(left: Path, right: Path) -> dict`: return counts of missing, extra and support_mismatch, exact equality flag; streaming, never load complete file.

- [ ] Write unittest cases for order-independent equality, missing/extra/support mismatch, invalid/empty/repeated items, invalid support, truncated record, duplicate itemset with differing support across chunks, many merge passes with fan_in=2, scratch cap and existing destination protection. Example: outputs `2 1 #SUP: 3\n4 #SUP: 2\n` and `4 #SUP: 2\n1 2 #SUP: 3\n` canonicalize identically for min_count=2,N=4.
- [ ] Run `python -I -m unittest discover -s bench/tests -p test_spmf_validate.py -v`; confirm failure because implementation is absent.
- [ ] Implement parser and external merge. Sort by numeric item tuple; compare duplicate keys even when support differs. Track live scratch bytes before writes, remove only owned intermediates; preserve source on failure. Hash canonical output in a final linear pass; source hash can stream in pre/post-validation outside timing.
- [ ] Run same tests; require all pass, including deliberately tiny chunks that force merge boundaries.
- [ ] Record task completion locally; no commit unless user requests it.

### Task 2: Reliable process measurement and limits

**Files:** `bench/spmf_process.py`, `bench/tests/test_spmf_process.py`.

**Interfaces:**
- `run_process(argv: list[str], directory: Path, *, timeout_seconds: float, output_cap_bytes: int, rss_cap_bytes: int, poll_seconds: float = 0.02, env: dict[str, str] | None = None) -> dict`: dedicated fresh directory contains `output.txt` (and Julia `jl_*` staged siblings), `stdout.log`, `stderr.log`; return status, exit_code, process_wall_seconds, maxrss_bytes, output_bytes, timestamps, argv and RSS method.
- `available_disk_bytes(path: Path) -> int`; `require_disk(path: Path, minimum: int) -> None` raises explicit disk-limit exception.

- [ ] Write child-process tests using `sys.executable -I -c`: success/output, nonzero exit/log retention, prompt exit/peak RSS, timeout, output cap while running and at final exit, memory cap, missing executable, no stale directory reuse and paths with spaces. Windows metrics test allocates/touches 32 MiB then exits immediately; peak must not be blank or runner RSS.
- [ ] Run `python -I -m unittest discover -s bench/tests -p test_spmf_process.py -v`; confirm missing implementation failure.
- [ ] Implement Windows `CreateProcessW` or subprocess with explicitly retained duplicated process handle, `GetProcessMemoryInfo(PROCESS_MEMORY_COUNTERS)`, and `WaitForSingleObject`/exit collection before closing handles. Include PROCESS_QUERY_INFORMATION/VM_READ rights and ctypes signatures; fail explicitly on unsupported OS. Timer ends at observed process exit before output scans/validation. Monitor output plus Julia staged files only in this fresh directory. On cap/timeout terminate child and wait; close resources on every path. Record final peak/output and status even for a child finishing between polls.
- [ ] Run process tests; verify time includes child startup/runtime and excludes deliberately delayed post-validation; no miner/test process left running.
- [ ] Record completion without committing.

### Task 3: Frozen paired campaign, preflight, pilot and resume

**Files:** `bench/spmf_campaign.py`, `bench/config-spmf-julia-20261122.toml`, `bench/tests/test_spmf_campaign.py`; consume Tasks 1–2.

**Interfaces:**
- `load_campaign(config: Path, repo: Path) -> dict`: validate 35 exact levels, positive limits, manifest paths and config schema.
- `expected_min_count(minsup: str, n_transactions: int) -> int`: exact Fraction decimal ceiling.
- `build_command(variant: str, *, julia: Path, java: Path, jar: Path, repo: Path, input_path: Path, output_path: Path, minsup: str, stats_path: Path) -> list[str]`: Julia run.jl `--variant optimized --stats ...`, SPMF `run NegFIN ...`; explicit JVM flags and Julia startup/project/threads.
- `schedule(config: dict) -> list[dict]`: 210 slots, each `(dataset,minsup,repetition,variant)` unique; alternate order by repetition.
- CLI: `python -I bench/spmf_campaign.py --config FILE --julia EXE --java EXE --jar FILE --root NEW_DIRECTORY --mode preflight|pilot|main [--resume]`.

- [ ] Write tests for exact manifest/config checksums, BOM/comments/input counts, all 210 unique slots, alternating order, fixture fractional ceilings, command quoting via argv lists, missing runtime/version/hash, corrupted CSV tail, changed source/config on resume, old trial exclusion and stale outputs. Include float-boundary detection using synthetic N/minsup known to differ between rational and binary ceiling; main must require pilot evidence tied to provenance.
- [ ] Run `python -I -m unittest discover -s bench/tests -p test_spmf_campaign.py -v`; confirm failure before implementation.
- [ ] Implement config with exact existing `[selected]`, limits and seed/order policy. Preflight captures source/config/manifest hashes, git commit/dirty/diff, full runtime versions, CPU/RAM/OS, thread settings, jar and input SHA/count. Python runs from trusted repo via `-I`. Locate local Java/jar first using targeted paths; request download permission if absent, never guess runtime readiness.
- [ ] Implement separate pilot directories: toy/boundary fixtures, easiest level each dataset then large Chess/Mushroom points under limits. Save full comparison and threshold evidence, independently of timing samples. Inspect SPMF jar/source/log or fixture behavior to establish threshold semantics; unresolved mismatch blocks affected main points and full campaign launch. Any mapping of SPMF CLI ratio requires explicit evidence/config, not silent nextafter changes.
- [ ] Implement main/resume with frozen evidence and fresh attempt directories. Append measured CSV row before validation; maintain separate validation ledger. Compare first repetition's paired canonical files exactly for all 35 conditions; each later repetition must match validated count/digest for its variant. Do not delete canonical reference until condition complete; clean only large owned output after saving evidence. Scratch/disk checks at each phase, classify errors distinctly. Resume never substitutes failed trials or cross-campaign values.
- [ ] Run campaign tests plus Tasks 1–2 suites; require all pass. Run `julia --startup-file=no --project=. test/runtests.jl` with discovered absolute Julia path; retain output and report actual outcome.
- [ ] Record completion locally; no commit.

### Task 4: Summary, report figures and evidence package

**Files:** `docs/validation/summarize-spmf-julia.py`, `docs/validation/test_summarize_spmf_julia.py`, `docs/validation/benchmark-spmf-julia-results.md`, later report figures; consume Task 3 CSV/environment/validation schema.

**Interfaces:**
- `summarize(campaign_root: Path) -> tuple[list[dict], list[dict]]`: successful groups and incomplete/failed ledger; require repetitions {1,2,3}, matching provenance, valid first-pair exact comparison, valid digest/counts.
- CLI: `python -I docs/validation/summarize-spmf-julia.py CAMPAIGN --output NEW_DIRECTORY [--package]`. Never mine numbers from prose or insert old Julia times.

- [ ] Write tests: known median/min/max, zeros not invented for failures, duplicate repetition, mixed source/config, missing first-pair validation, pattern-count mismatch, failed/partial campaign and old warm/scale records all rejected or reported incomplete. ZIP test recomputes each manifest entry and archive integrity.
- [ ] Run `python -I -m unittest discover -s docs/validation -p test_summarize_spmf_julia.py -v`; confirm missing implementation failure.
- [ ] Implement strict summaries with runtime seconds/RSS MiB and source identifiers; maintain raw precision. Package CSV/log/env/config/source snapshot or hashes, argv, comparisons and README with file SHA256. Do not include datasets/runtimes/itemset outputs; verify ZIP by fresh extraction and every checksum.
- [ ] Load dataviz before figure code; inspect available report figure dependencies. Export runtime–minsup per dataset (SPMF/Optimized median with min–max), itemsets–minsup, peak RSS at fourth selected level. Reuse old Baseline–Optimized scalability only with explicit provenance. Create PNG/PDF through available verified renderer; if missing a dependency, report/obtain authorization rather than fake an image. Test plot input selection/units/labels and no points for invalid samples.
- [ ] Run summary/package tests and existing relevant renderer tests; require passing output before use.
- [ ] Record completion locally; no commit.

### Task 5: Execute evidence gates and finalize Chapter 2

**Files:** new local campaign under ignored `results/`; modify `docs/report/chapter2.md`, `docs/validation/benchmark-handoff.md`, new results appendix and figures.

- [ ] Run preflight with actual absolute runtime paths. If Java/jar absent, stop execution at a precise blocker and obtain download approval. Do not run jars before version/hash/source are recorded. Check current free disk and no simultaneous mining workload.
- [ ] Run pilot under frozen caps, inspect all comparisons and Java threshold evidence; mark progress in this plan. Do not launch main on unresolved mismatch or change caps silently.
- [ ] Run 210 main slots sequentially as a background command, logs outside Git; use harness completion notification/wait tool, never leave a running command unacknowledged. Resume only with matching provenance. Report accepted/incomplete counts, not assumed successes.
- [ ] Recompute summaries and verify every published point; create final figures/package and inspect actual outputs. Any visual requested for viewing is shown with host HTML preview/render; PNG files used for report remain directly linked.
- [ ] Verify public Hugging Face/Kaggle candidate snapshots against manifest SHA256 using isolated new download directories and Python `-I`; report remaining missing snapshots honestly. Do not download huge unrelated mirrors or include private names/project metadata in external queries.
- [ ] Update Chapter 2 with new methods, runtime/RSS/results, dense/sparse/output-volume discussion and limitations; retain old source identifiers and T10I4D100K trade-off. Label proposed optimizations and transaction-length experiment as decisions still pending Đăng, not approved work. Do not modify generated IEEE TeX/PDF unless separately requested.
- [ ] Prepare captions, local handoff README and SHA package for Tiến; link files and list incomplete configurations. Do not send externally or create PR without authorization.
- [ ] Run full new Python tests, existing application/renderer tests where relevant, and Julia suite; inspect `git diff --check`, `git status` and tracked-file list for raw/dataset/runtime leakage. Summarize exact pass/fail/skip, reproducibility commands and local file paths. Review code inline if independent reviewer remains unavailable; do not claim an independent review happened.

## Approval and execution status

- Design approved by user: 2026-11-22, message “duyệt”.
- This implementation plan awaits user review/execution-method choice before code implementation.
- Recommended execution: **Native**, because process/validator/campaign/reporting interfaces are tightly coupled and isolated agent worktrees are currently failing. No implementation subagents or runtime downloads have been authorized by this plan itself.
