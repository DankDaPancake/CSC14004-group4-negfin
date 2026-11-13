# Warm (in-process, after warm-up), cold (child process, peak RSS) and scalability runs.
# Usage: julia --project=. bench/run.jl --scope warm|cold|scalability --dataset NAME
#        julia --project=. bench/run.jl --all
#        optional: --config PATH --data-dir DIR --results-root DIR
include(joinpath(@__DIR__, "Bench.jl"))
using TOML

const NegFIN = Bench.NegFIN

function parse_args(args::Vector{String})::Dict{String,String}
    options = Dict{String,String}()
    i = 1
    while i <= length(args)
        if args[i] == "--all"
            options["--all"] = "true"
            i += 1
        else
            i < length(args) || error("Missing value for $(args[i])")
            options[args[i]] = args[i+1]
            i += 2
        end
    end
    haskey(options, "--all") || (haskey(options, "--scope") && haskey(options, "--dataset")) ||
        error("Use --all, or --scope warm|cold|scalability with --dataset NAME")
    return options
end

struct Context
    repo::String
    config::Dict{String,Any}
    manifest::Dict{String,Any}
    data_dir::String
    run_dir::String
    run_id::String
    julia::Cmd
end

variant(ctx::Context) = ctx.config["variant"]

function selected_levels(ctx::Context, name::String)::Vector{String}
    levels = get(ctx.config["selected"], name, nothing)
    levels === nothing && error("No [selected].$name in bench/config.toml; run bench/pilot.jl first")
    return levels
end

function scalability_level(ctx::Context, name::String)::String
    level = get(ctx.config["scalability_minsup"], name, nothing)
    level === nothing && error("No [scalability_minsup].$name in bench/config.toml")
    return level
end

function write_rows(ctx::Context, row::Dict{String,Any}, phases::AbstractDict, scope, dataset, fraction, minsup, mode, rep)
    Bench.append_csv(joinpath(ctx.run_dir, "runs.csv"), Bench.RUN_COLUMNS, row)
    for phase in Bench.phase_rows(ctx.run_id, variant(ctx), scope, dataset, fraction, minsup, mode, rep, phases)
        Bench.append_csv(joinpath(ctx.run_dir, "phases.csv"), Bench.PHASE_COLUMNS, phase)
    end
end

function run_warm(ctx::Context, scope::String, dataset::String, fraction::Real, input::String,
                  digest::String, levels::Vector{String})
    tmp = mkpath(joinpath(ctx.run_dir, "tmp"))
    read_stats = @timed open(NegFIN.read_spmf, input)
    db = read_stats.value
    Bench.warmup!(tmp)
    for minsup in levels, mode in (:count, :write)
        repetitions = ctx.config["warm_repetitions"]
        rep = 0
        while rep < repetitions
            rep += 1
            result = Bench.measure_warm(db, minsup, mode, tmp)
            rep == 1 && result["phases_total_seconds"] > ctx.config["warm_long_threshold_seconds"] &&
                (repetitions = ctx.config["warm_long_repetitions"])
            row = Dict{String,Any}("run_id" => ctx.run_id, "variant" => variant(ctx), "scope" => scope,
                "dataset" => dataset, "fraction" => fraction, "input_sha256" => digest,
                "minsup" => minsup, "emit_mode" => string(mode), "repetition" => rep,
                "read_seconds" => read_stats.time, "status" => "ok")
            for key in ("n_transactions", "min_count", "n_frequent_items", "n_patterns",
                        "phases_total_seconds", "bmc_nodes", "negative_records_scanned", "output_bytes")
                haskey(result, key) && (row[key] = result[key])
            end
            write_rows(ctx, row, result["phases"], scope, dataset, fraction, minsup, string(mode), rep)
            println("$scope $dataset f=$fraction minsup=$minsup $mode rep=$rep total=",
                    round(result["phases_total_seconds"]; digits=3), "s patterns=", result["n_patterns"])
            flush(stdout)
        end
    end
end

function run_cold(ctx::Context, scope::String, dataset::String, fraction::Real, input::String,
                  digest::String, levels::Vector{String}, floor::Int)
    tmp = mkpath(joinpath(ctx.run_dir, "tmp"))
    for minsup in levels, rep in 1:ctx.config["cold_repetitions"]
        stats = joinpath(tmp, "$dataset-$fraction-$minsup-$rep.stats.toml")
        result = Bench.run_cold(ctx.julia, ctx.repo, input, joinpath(tmp, "$dataset-cold.txt"), stats, minsup;
            timeout_seconds=ctx.config["cold_timeout_seconds"], max_output_bytes=ctx.config["max_output_bytes"])
        row = Bench.cold_row(ctx.run_id, variant(ctx), scope, dataset, fraction, digest, minsup, rep, result, floor)
        write_rows(ctx, row, get(result, "phases", Dict{String,Any}()), scope, dataset, fraction, minsup, "cli", rep)
        println("$scope $dataset f=$fraction minsup=$minsup cli rep=$rep wall=",
                round(result["process_wall_seconds"]; digits=3), "s maxrss=",
                round(get(result, "maxrss_bytes", 0) / 2^20; digits=1), "MiB status=", result["status"])
        flush(stdout)
    end
end

function dataset_input(ctx::Context, name::String)::Tuple{String,String}
    entry = Bench.manifest_entry(ctx.manifest, name)
    input = joinpath(ctx.data_dir, entry["path"])
    return input, Bench.verify_input(input, entry["sha256"])
end

function run_scope(ctx::Context, scope::String, name::String, floor::Int)
    if scope in ("warm", "cold")
        input, digest = dataset_input(ctx, name)
        levels = selected_levels(ctx, name)
        scope == "warm" ? run_warm(ctx, scope, name, 1.0, input, digest, levels) :
                          run_cold(ctx, scope, name, 1.0, input, digest, levels, floor)
    elseif scope == "scalability"
        full, _ = dataset_input(ctx, name)
        level = [scalability_level(ctx, name)]
        subsets = joinpath(ctx.repo, ctx.config["results_root"], "subsets")
        for fraction in ctx.config["scalability_fractions"]
            path = Bench.subset_path(subsets, name, fraction)
            isfile(path) || Bench.prefix_subset(full, Float64(fraction), path)
            digest = bytes2hex(open(Bench.sha256, path))
            run_warm(ctx, "scalability-warm", name, fraction, path, digest, level)
            run_cold(ctx, "scalability-cold", name, fraction, path, digest, level, floor)
        end
    else
        error("Unknown scope: $scope")
    end
end

function main(args::Vector{String})
    repo = dirname(@__DIR__)
    options = parse_args(args)
    config_path = get(options, "--config", joinpath(repo, "bench", "config.toml"))
    config = Bench.load_config(config_path)
    manifest_path = joinpath(repo, config["manifest"])
    manifest = TOML.parsefile(manifest_path)
    data_dir = get(options, "--data-dir", dirname(manifest_path))
    run_dir = Bench.new_run_dir(joinpath(repo, get(options, "--results-root", config["results_root"])))
    ctx = Context(repo, config, manifest, data_dir, run_dir, basename(run_dir),
                  `$(Base.julia_cmd()) --startup-file=no --project=$repo`)
    Bench.write_env(run_dir, repo, config_path, manifest, data_dir)
    floor = Bench.rss_floor(ctx.julia, repo)
    println("Results -> $run_dir (rss floor ", round(floor / 2^20; digits=1), " MiB)")
    plan = if haskey(options, "--all")
        [[(scope, name) for scope in ("warm", "cold") for name in keys(config["selected"])];
         [("scalability", name) for name in config["scalability_datasets"]]]
    else
        [(options["--scope"], options["--dataset"])]
    end
    for (scope, name) in plan
        run_scope(ctx, scope, name, floor)
        Bench.summarize(run_dir)
    end
    rm(joinpath(run_dir, "tmp"); recursive=true, force=true)
    println("Done: ", joinpath(run_dir, "summary.csv"))
end

main(ARGS)
