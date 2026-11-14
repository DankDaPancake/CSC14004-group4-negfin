# Compare CLI variants in separate processes; includes startup, JIT and output.
using SHA
repo, input, minsup = abspath(ARGS[1]), abspath(ARGS[2]), ARGS[3]
include(joinpath(repo, "bench", "Bench.jl"))
julia = `$(Base.julia_cmd()) --startup-file=no --project=$repo`
println("input_sha256=", bytes2hex(open(sha256, input)), " minsup=", minsup,
        " Julia=", VERSION, " threads=", Threads.nthreads())
mktempdir() do dir
    for rep in 1:3
        variants = isodd(rep) ? (:baseline, :optimized) : (:optimized, :baseline)
        for variant in variants
            result = Bench.run_cold(julia, repo, input, joinpath(dir, "output.txt"),
                joinpath(dir, "stats.toml"), minsup; timeout_seconds=300,
                max_output_bytes=2^31, variant)
            println("variant=", variant, " rep=", rep, " status=", result["status"],
                    " seconds=", result["process_wall_seconds"],
                    " maxrss_bytes=", get(result, "maxrss_bytes", "missing"),
                    " patterns=", get(result, "n_patterns", "missing"))
            flush(stdout)
            result["status"] == "ok" || error("Cold run did not finish: $(result["status"])")
        end
    end
end
