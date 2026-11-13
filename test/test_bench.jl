isdefined(Main, :Bench) || include(joinpath(ROOT, "bench", "Bench.jl"))

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

@testset "Pilot level selection" begin
    levels = [("0.9", 0.001), ("0.85", 0.01), ("0.8", 0.04), ("0.75", 0.2), ("0.7", 1.0),
              ("0.65", 4.0), ("0.6", 15.0), ("0.55", 50.0), ("0.5", 110.0)]
    chosen = Bench.select_levels(levels)
    @test 5 <= length(chosen) <= 7
    @test "0.5" in chosen                                   # slowest ok level kept
    @test count(in(["0.9", "0.85", "0.8"]), chosen) == 1    # one level under 0.05 s
    @test "0.8" in chosen                                   # lowest minsup among fast levels
    @test chosen == sort(chosen; by=x -> -parse(Float64, x))
    @test Bench.select_levels(levels[1:4]) == ["0.8", "0.75"]
end

@testset "Warm measurement and subsets" begin
    mktempdir() do dir
        toy = joinpath(ROOT, "data", "toy", "example.txt")
        db = open(read_spmf, toy)
        Bench.warmup!(dir)
        counted = Bench.measure_warm(db, "0.4", :count, dir)
        written = Bench.measure_warm(db, "0.4", :write, dir)
        @test counted["n_patterns"] == written["n_patterns"] == 15
        @test written["output_bytes"] == sum(ncodeunits(line) + 1 for line in readlines(joinpath(ROOT, "data", "toy", "example.expected.txt")))
        @test get(counted, "output_bytes", 0) == 0
        @test Set(keys(counted["phases"])) == Set(["normalize", "prepare", "build_bmc", "collect_nodesets", "mine"])
        @test counted["phases_total_seconds"] > 0
        @test isempty(filter(f -> endswith(f, ".txt"), readdir(dir)))
        sub = joinpath(dir, "sub.txt")
        @test Bench.prefix_subset(toy, 0.6, sub) == 3
        @test open(read_spmf, sub) == open(read_spmf, toy)[1:3]
        run_dir = mkpath(joinpath(dir, "run"))
        for rep in 1:3
            row = Dict{String,Any}("run_id" => "r", "variant" => "baseline", "scope" => "warm",
                "dataset" => "Toy", "fraction" => 1.0, "minsup" => "0.4", "emit_mode" => "count",
                "repetition" => rep, "phases_total_seconds" => Float64(rep), "status" => "ok")
            Bench.append_csv(joinpath(run_dir, "runs.csv"), Bench.RUN_COLUMNS, row)
            for phase in Bench.phase_rows("r", "baseline", "warm", "Toy", 1.0, "0.4", "count", rep,
                    Dict("mine" => Dict("seconds" => 2.0 * rep, "bytes" => 10 * rep, "gc_seconds" => 0.0)))
                Bench.append_csv(joinpath(run_dir, "phases.csv"), Bench.PHASE_COLUMNS, phase)
            end
        end
        Bench.summarize(run_dir)
        summary = readlines(joinpath(run_dir, "summary.csv"))
        @test any(l -> occursin("Toy", l) && occursin("phases_total_seconds", l) && occursin(",2.0,1.0,3.0", l), summary)
        @test any(l -> occursin("Toy", l) && occursin("mine", l) && occursin("seconds,4.0,2.0,6.0", l), summary)
    end
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
        @test isempty(filter(f -> startswith(f, "out"), readdir(dir)))
    end
end
