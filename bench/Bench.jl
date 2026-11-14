"""Benchmark harness for negFIN: config, checksums, environment capture and CSV output."""
module Bench

using SHA
using TOML

# Reuse the caller's NegFIN (as in test/runtests.jl) so types match; otherwise load it here.
if isdefined(Main, :NegFIN)
    const NegFIN = Main.NegFIN
else
    include(joinpath(dirname(@__DIR__), "src", "NegFIN.jl"))
end

# Kept wide so Baseline and Optimized rows share one schema; phases go to PHASE_COLUMNS.
const RUN_COLUMNS = ["run_id", "variant", "scope", "dataset", "fraction", "input_sha256",
    "n_transactions", "minsup", "min_count", "n_frequent_items", "n_patterns", "emit_mode",
    "repetition", "read_seconds", "phases_total_seconds", "mine_write_seconds", "bmc_nodes",
    "negative_records_scanned", "output_bytes", "process_wall_seconds", "maxrss_bytes",
    "rss_floor_bytes", "status"]
const PHASE_COLUMNS = ["run_id", "variant", "scope", "dataset", "fraction", "minsup",
    "emit_mode", "repetition", "phase", "seconds", "bytes", "gc_seconds"]

load_config(path::String)::Dict{String,Any} = TOML.parsefile(path)

function manifest_entry(manifest::Dict, name::String)::Dict{String,Any}
    for entry in manifest["datasets"]
        entry["name"] == name && return entry
    end
    throw(ArgumentError("Dataset not in manifest: $name"))
end

"""Return the SHA256 of `path`, failing before any measurement if it is absent or differs."""
function verify_input(path::String, expected::String)::String
    isfile(path) || error("Missing input $path; download it as described in README.md")
    digest = bytes2hex(open(sha256, path))
    digest == lowercase(expected) || error("Checksum mismatch for $path: expected $expected, got $digest")
    return digest
end

function new_run_dir(root::String)::String
    stamp = Libc.strftime("%Y%m%d-%H%M%S", time())
    path = joinpath(root, stamp)
    suffix = 1
    while ispath(path)
        suffix += 1
        path = joinpath(root, "$stamp-$suffix")
    end
    mkpath(path)
    return path
end

function command_output(cmd::Cmd)::String
    try
        return strip(read(cmd, String))
    catch
        return "unknown"
    end
end

function write_env(dir::String, repo::String, config_path::String, manifest::Dict, data_dir::String)::Nothing
    datasets = Dict{String,Any}()
    for entry in manifest["datasets"]
        path = joinpath(data_dir, entry["path"])
        datasets[entry["name"]] = isfile(path) ? bytes2hex(open(sha256, path)) : "missing"
    end
    env = Dict{String,Any}(
        "julia_version" => string(VERSION),
        "cpu_name" => Sys.CPU_NAME,
        "cpu_model" => strip(first(Sys.cpu_info()).model),
        "cpu_threads" => Sys.CPU_THREADS,
        "julia_threads" => Threads.nthreads(),
        "total_memory_bytes" => Int(Sys.total_memory()),
        "os" => string(Sys.KERNEL, " ", Sys.MACHINE),
        "git_commit" => command_output(`git -C $repo rev-parse HEAD`),
        "git_dirty" => !isempty(command_output(`git -C $repo status --porcelain`)),
        "started_at" => Libc.strftime("%Y-%m-%dT%H:%M:%S", time()),
        "dataset_sha256" => datasets,
        "config" => load_config(config_path))
    Sys.iswindows() && (env["windows_version"] = string(Sys.windows_version()))
    open(io -> TOML.print(io, env), joinpath(dir, "env.toml"), "w")
    return nothing
end

function csv_cell(value)::String
    value === nothing && return ""
    text = string(value)
    return occursin(r"[,\"\n]", text) ? "\"" * replace(text, "\"" => "\"\"") * "\"" : text
end

"""Append one row, writing the header first if the file is new; missing cells stay empty."""
function append_csv(path::String, columns::Vector{String}, row::Dict{String,Any})::Nothing
    fresh = !isfile(path)
    open(path, "a") do io
        fresh && println(io, join(columns, ','))
        println(io, join((csv_cell(get(row, column, nothing)) for column in columns), ','))
    end
    return nothing
end

"""
Choose 5-7 levels from `(minsup, seconds)` pairs in ladder order: levels under
`floor_seconds` collapse to the last of them, the fastest and slowest survivors
are kept, and the rest are the closest to evenly spaced points in log(seconds).
"""
function select_levels(levels::Vector{Tuple{String,Float64}}; min_count::Int=5, max_count::Int=7,
                       floor_seconds::Float64=0.05)::Vector{String}
    fast = filter(level -> level[2] < floor_seconds, levels)
    usable = [isempty(fast) ? Tuple{String,Float64}[] : [last(fast)];
              filter(level -> level[2] >= floor_seconds, levels)]
    length(usable) <= max_count && return first.(usable)
    logs = [log(max(level[2], eps())) for level in usable]
    picked = Set([1, length(usable)])
    for k in 1:max_count-2
        target = logs[1] + (logs[end] - logs[1]) * k / (max_count - 1)
        candidates = [i for i in 2:length(usable)-1 if !(i in picked)]
        push!(picked, candidates[argmin([abs(logs[i] - target) for i in candidates])])
    end
    return [usable[i][1] for i in sort!(collect(picked))]
end

"""
Bytes the CLI has written for `output` since `since`: the output itself plus its
staged `mktemp` sibling (`jl_*`). Stats and other harness files do not count.
"""
function staged_bytes(output::String, since::Float64)::Int
    dir = dirname(abspath(output))
    total = 0
    for name in readdir(dir)
        path = joinpath(dir, name)
        (path == abspath(output) || startswith(name, "jl_")) || continue
        isfile(path) && mtime(path) >= since && (total += filesize(path))
    end
    return total
end

"""
Run the CLI in a child process and return status, wall time, peak RSS, output size
and stats. The output is deleted afterwards; the stats file is kept.
"""
function run_cold(julia::Cmd, repo::String, input::String, output::String, stats::String, minsup::String;
                  timeout_seconds::Real, max_output_bytes::Integer, variant::Symbol=:baseline)::Dict{String,Any}
    variant in (:baseline, :optimized) || throw(ArgumentError("Unknown variant: $variant"))
    out_dir = dirname(abspath(output))
    mkpath(out_dir)
    maxrss_path = stats * ".maxrss.toml"
    errlog = stats * ".stderr.txt"
    for path in (output, stats, maxrss_path)
        isfile(path) && rm(path)
    end
    cmd = `$julia $(joinpath(repo, "bench", "cold_run.jl")) --maxrss $maxrss_path --input $input --output $output --minsup $minsup --variant $(string(variant)) --stats $stats`
    started_at = time()
    started = time_ns()
    process = run(pipeline(cmd; stdout=devnull, stderr=errlog); wait=false)
    status = "ok"
    while !process_exited(process)
        elapsed = (time_ns() - started) / 1e9
        if elapsed > timeout_seconds
            status = "timeout"
        elseif staged_bytes(output, started_at) > max_output_bytes
            status = "output_cap"
        end
        if status != "ok"
            kill(process)
            break
        end
        sleep(0.2)
    end
    wait(process)
    wall = (time_ns() - started) / 1e9
    output_bytes = isfile(output) ? filesize(output) : 0
    result = Dict{String,Any}("process_wall_seconds" => wall, "output_bytes" => output_bytes)
    if status == "ok"
        if process.exitcode != 0
            status = "error"
        elseif output_bytes > max_output_bytes
            status = "output_cap"
        end
    end
    merge!(result, child_reports(stats, maxrss_path; status, exitcode=process.exitcode))
    isfile(output) && rm(output)
    # A killed child can leave its staged temp file behind.
    for name in readdir(out_dir)
        path = joinpath(out_dir, name)
        isfile(path) && mtime(path) >= started_at && startswith(name, "jl_") && rm(path)
    end
    result["status"] = status
    return result
end

"""
Stats and peak RSS written by a cold child. A killed child may have left either
file half-written, so nothing it reported is trusted.
"""
function child_reports(stats::String, maxrss_path::String; killed::Bool=false,
                       status::String="ok", exitcode::Int=0)::Dict{String,Any}
    reports = Dict{String,Any}()
    (killed || status != "ok" || exitcode != 0) && return reports
    isfile(stats) && merge!(reports, TOML.parsefile(stats))
    isfile(maxrss_path) && (reports["maxrss_bytes"] = TOML.parsefile(maxrss_path)["maxrss_bytes"])
    return reports
end

function rss_floor(julia::Cmd, repo::String)::Int
    path = tempname() * ".toml"
    run(`$julia $(joinpath(repo, "bench", "rss_floor.jl")) $path`)
    value = TOML.parsefile(path)["maxrss_bytes"]
    rm(path)
    return value
end

"""Map a cold or pilot result to a `RUN_COLUMNS` row."""
function cold_row(run_id, variant, scope, dataset, fraction, digest, minsup, repetition,
                  result::Dict{String,Any}, floor)::Dict{String,Any}
    row = Dict{String,Any}("run_id" => run_id, "variant" => variant, "scope" => scope,
        "dataset" => dataset, "fraction" => fraction, "input_sha256" => digest,
        "minsup" => minsup, "emit_mode" => "cli", "repetition" => repetition,
        "rss_floor_bytes" => floor)
    for key in ("n_transactions", "min_count", "n_frequent_items", "n_patterns", "read_seconds",
                "mine_write_seconds", "bmc_nodes", "negative_records_scanned", "output_bytes",
                "process_wall_seconds", "maxrss_bytes", "status")
        haskey(result, key) && (row[key] = result[key])
    end
    phases = get(result, "phases", Dict{String,Any}())
    isempty(phases) || (row["phases_total_seconds"] = sum(p["seconds"] for p in values(phases)))
    return row
end

"""Long-form phase rows for one measurement; `phases` maps name => seconds/bytes/gc_seconds."""
function phase_rows(run_id, variant, scope, dataset, fraction, minsup, emit_mode, repetition,
                    phases::AbstractDict)::Vector{Dict{String,Any}}
    return [Dict{String,Any}("run_id" => run_id, "variant" => variant, "scope" => scope,
                "dataset" => dataset, "fraction" => fraction, "minsup" => minsup,
                "emit_mode" => emit_mode, "repetition" => repetition, "phase" => name,
                "seconds" => m["seconds"], "bytes" => m["bytes"], "gc_seconds" => m["gc_seconds"])
            for (name, m) in sort!(collect(phases); by=first)]
end

"""
Mine `db` once in this process with the phase hook. `:count` only counts patterns;
`:write` formats them into a file under `tmpdir` like the CLI, then deletes it.
"""
function measure_warm(db::Vector{Vector{Int}}, minsup::String, emit_mode::Symbol, tmpdir::String; variant::Symbol=:baseline)::Dict{String,Any}
    emit_mode in (:count, :write) || throw(ArgumentError("emit_mode must be :count or :write"))
    variant in (:baseline, :optimized) || throw(ArgumentError("Unknown variant: $variant"))
    miner = variant == :baseline ? NegFIN.mine_baseline : NegFIN.mine_optimized
    phases = Dict{String,Any}()
    counters = Dict{String,Any}()
    on_phase = (phase, metrics) -> begin
        phases[string(phase)] = Dict{String,Any}("seconds" => metrics.seconds,
            "bytes" => metrics.bytes, "gc_seconds" => metrics.gc_seconds)
        for key in (:n_frequent_items, :bmc_nodes, :negative_records_scanned)
            haskey(metrics, key) && (counters[string(key)] = metrics[key])
        end
    end
    ratio = NegFIN.parse_minsup(minsup)
    GC.gc()
    result = Dict{String,Any}()
    if emit_mode == :count
        emitted = Ref(0)
        summary = miner(db, ratio; on_phase, emit=(items, support) -> (emitted[] += 1))
    else
        path, io = mktemp(tmpdir)
        try
            summary = miner(db, ratio; on_phase,
                emit=(items, support) -> NegFIN.write_itemset(io, items, support))
            close(io)
            result["output_bytes"] = filesize(path)
        finally
            isopen(io) && close(io)
            rm(path; force=true)
        end
    end
    merge!(result, counters)
    result["phases"] = phases
    result["phases_total_seconds"] = sum(p["seconds"] for p in values(phases))
    result["n_patterns"] = summary.n_patterns
    result["n_frequent_items"] = summary.n_frequent_items
    result["min_count"] = summary.min_count
    result["n_transactions"] = summary.n_transactions
    return result
end

"""Compile the measured code paths on the toy database before timing anything."""
function warmup!(tmpdir::String; variant::Symbol=:baseline)::Nothing
    db = open(NegFIN.read_spmf, joinpath(dirname(@__DIR__), "data", "toy", "example.txt"))
    for mode in (:count, :write)
        measure_warm(db, "0.4", mode, tmpdir; variant)
    end
    return nothing
end

"""Write the first `round(fraction * n)` data lines (those `read_spmf` keeps) of `input`."""
function prefix_subset(input::String, fraction::Float64, output::String)::Int
    lines = String[]
    for (number, raw) in enumerate(eachline(input))
        line = strip(number == 1 ? replace(raw, '﻿' => "") : raw)
        (isempty(line) || first(line) in ('#', '%', '@')) && continue
        push!(lines, line)
    end
    keep = round(Int, fraction * length(lines))
    mkpath(dirname(abspath(output)))
    open(output, "w") do io
        foreach(line -> println(io, line), lines[1:keep])
    end
    return keep
end

subset_path(dir::String, dataset::String, fraction::Real)::String =
    joinpath(dir, "$dataset-$(round(Int, 100 * fraction)).txt")

function read_csv(path::String)::Vector{Dict{String,String}}
    isfile(path) || return Dict{String,String}[]
    rows = readlines(path)
    header = split(rows[1], ',')
    parse_line(line) = [replace(m.match, r"^\"|\"$" => "", "\"\"" => "\"")
                        for m in eachmatch(r"\"(?:[^\"]|\"\")*\"|[^,]*", line) if m.offset == 1 ||
                            line[prevind(line, m.offset)] == ',']
    return [Dict(String(k) => v for (k, v) in zip(header, parse_line(line))) for line in rows[2:end]]
end

"""Median/min/max per configuration for runs.csv metrics and per phase for phases.csv."""
function summarize(run_dir::String)::Nothing
    keys_run = ["variant", "scope", "dataset", "fraction", "minsup", "emit_mode"]
    columns = [keys_run; "phase"; "metric"; "median"; "min"; "max"; "n"]
    path = joinpath(run_dir, "summary.csv")
    isfile(path) && rm(path)
    groups = Dict{Vector{String},Vector{Float64}}()
    for row in read_csv(joinpath(run_dir, "runs.csv"))
        get(row, "status", "ok") == "ok" || continue
        for metric in ("phases_total_seconds", "process_wall_seconds", "maxrss_bytes")
            value = tryparse(Float64, get(row, metric, ""))
            value === nothing && continue
            push!(get!(groups, [[row[k] for k in keys_run]; ""; metric], Float64[]), value)
        end
    end
    for row in read_csv(joinpath(run_dir, "phases.csv"))
        for metric in ("seconds", "bytes", "gc_seconds")
            value = tryparse(Float64, get(row, metric, ""))
            value === nothing && continue
            push!(get!(groups, [[row[k] for k in keys_run]; row["phase"]; metric], Float64[]), value)
        end
    end
    for key in sort!(collect(keys(groups)))
        values = groups[key]
        row = Dict{String,Any}(zip(columns, key))
        row["median"] = median_of(values)
        row["min"] = minimum(values)
        row["max"] = maximum(values)
        row["n"] = length(values)
        append_csv(path, columns, row)
    end
    return nothing
end

function median_of(xs::Vector{Float64})::Float64
    sorted = sort(xs)
    n = length(sorted)
    return isodd(n) ? sorted[(n + 1) ÷ 2] : (sorted[n ÷ 2] + sorted[n ÷ 2 + 1]) / 2
end

end
