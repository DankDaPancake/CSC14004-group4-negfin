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
