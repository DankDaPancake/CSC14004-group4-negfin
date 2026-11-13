"""Benchmark harness for negFIN: config, checksums, environment capture and CSV output."""
module Bench

using SHA
using TOML

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

function median_of(xs::Vector{Float64})::Float64
    sorted = sort(xs)
    n = length(sorted)
    return isodd(n) ? sorted[(n + 1) ÷ 2] : (sorted[n ÷ 2] + sorted[n ÷ 2 + 1]) / 2
end

end
