# Walk a dataset's minsup ladder with one cold run per level and propose 5-7 levels.
# Usage: julia --project=. bench/pilot.jl --dataset NAME [--config PATH] [--data-dir DIR] [--results-root DIR]
include(joinpath(@__DIR__, "Bench.jl"))
using TOML

function parse_args(args::Vector{String})::Dict{String,String}
    options = Dict{String,String}()
    for i in 1:2:length(args)
        i < length(args) || error("Missing value for $(args[i])")
        options[args[i]] = args[i+1]
    end
    haskey(options, "--dataset") || error("--dataset NAME is required")
    return options
end

function pilot(args::Vector{String})
    repo = dirname(@__DIR__)
    options = parse_args(args)
    config_path = get(options, "--config", joinpath(repo, "bench", "config.toml"))
    config = Bench.load_config(config_path)
    manifest_path = joinpath(repo, config["manifest"])
    manifest = TOML.parsefile(manifest_path)
    data_dir = get(options, "--data-dir", dirname(manifest_path))
    name = options["--dataset"]
    entry = Bench.manifest_entry(manifest, name)
    input = joinpath(data_dir, entry["path"])
    digest = Bench.verify_input(input, entry["sha256"])
    haskey(config["ladders"], name) || error("No [ladders].$name in $config_path")
    run_dir = Bench.new_run_dir(joinpath(repo, get(options, "--results-root", config["results_root"])))
    run_id = basename(run_dir)
    Bench.write_env(run_dir, repo, config_path, manifest, data_dir)
    julia = `$(Base.julia_cmd()) --startup-file=no --project=$repo`
    floor = Bench.rss_floor(julia, repo)
    tmp = mkpath(joinpath(run_dir, "tmp"))
    ok = Tuple{String,Float64}[]
    println("Pilot $name -> $run_dir")
    println(rpad("minsup", 8), rpad("min_count", 11), rpad("patterns", 12), rpad("out_MiB", 10),
            rpad("mine_write_s", 14), rpad("wall_s", 9), rpad("maxrss_MiB", 12), "status")
    for minsup in config["ladders"][name]
        stats = joinpath(tmp, "$name-$minsup.stats.toml")
        result = Bench.run_cold(julia, repo, input, joinpath(tmp, "$name-$minsup.txt"), stats, minsup;
            timeout_seconds=config["pilot_timeout_seconds"], max_output_bytes=config["max_output_bytes"])
        row = Bench.cold_row(run_id, config["variant"], "pilot", name, 1.0, digest, minsup, 1, result, floor)
        Bench.append_csv(joinpath(run_dir, "pilot.csv"), Bench.RUN_COLUMNS, row)
        phases = get(result, "phases", Dict{String,Any}())
        for phase in Bench.phase_rows(run_id, config["variant"], "pilot", name, 1.0, minsup, "cli", 1, phases)
            Bench.append_csv(joinpath(run_dir, "phases.csv"), Bench.PHASE_COLUMNS, phase)
        end
        mib(x) = x === nothing ? "-" : string(round(x / 2^20; digits=1))
        secs(x) = x === nothing ? "-" : string(round(x; digits=3))
        println(rpad(minsup, 8), rpad(string(get(result, "min_count", "-")), 11),
                rpad(string(get(result, "n_patterns", "-")), 12), rpad(mib(get(result, "output_bytes", nothing)), 10),
                rpad(secs(get(result, "mine_write_seconds", nothing)), 14), rpad(secs(result["process_wall_seconds"]), 9),
                rpad(mib(get(result, "maxrss_bytes", nothing)), 12), result["status"])
        flush(stdout)
        result["status"] == "ok" || break
        push!(ok, (minsup, result["mine_write_seconds"]))
    end
    chosen = Bench.select_levels(ok)
    println("rss_floor_MiB = ", round(floor / 2^20; digits=1))
    println("proposed $name = ", repr(chosen))
    length(chosen) < 5 && println("WARNING: fewer than 5 usable levels; add intermediate levels to [ladders].$name")
    open(io -> TOML.print(io, Dict("dataset" => name, "proposed" => chosen)), joinpath(run_dir, "proposed.toml"), "w")
end

pilot(ARGS)
