include(joinpath(ROOT, "bench", "validate-pair.jl"))

@testset "Exact Baseline and Optimized output validation" begin
    mktempdir() do dir
        toy = joinpath(ROOT, "data", "toy", "example.txt")
        result = validate_pair(ROOT, toy, "0.4", dir)
        @test result.equal
        @test result.baseline_sha256 == result.optimized_sha256
        @test result.baseline_patterns == result.optimized_patterns == 15
        @test !isfile(joinpath(dir, "baseline.txt"))
        @test !isfile(joinpath(dir, "optimized.txt"))
    end
end

@testset "Output comparison detects byte differences" begin
    mktempdir() do dir
        left, right = joinpath(dir, "left.txt"), joinpath(dir, "right.txt")
        write(left, "1 2 #SUP: 3\n")
        write(right, "1 2 #SUP: 4\n")
        result = compare_outputs(left, right; chunk_size=7)
        @test !result.equal
        @test result.left_sha256 != result.right_sha256
        write(left, "abcdefgh"^4096)
        write(right, "abcdefgh"^4096)
        equal_result = compare_outputs(left, right; chunk_size=7)
        @test equal_result.equal
        @test equal_result.left_sha256 == equal_result.right_sha256
        write(right, "different-at-end")
        final_result = compare_outputs(left, right; chunk_size=7)
        @test !final_result.equal
        @test final_result.left_sha256 != final_result.right_sha256
        @test_throws ArgumentError compare_outputs(left, right; chunk_size=0)
        @test_throws ErrorException compare_outputs(left, right; max_bytes=1)
        staged = joinpath(dir, "jl_staged.tmp")
        write(staged, "x"^2048)
        @test staged_output_bytes(dir, time() - 1) == 2048
        @test staged_output_bytes(dir, time() - 1; max_bytes=1024) == 2048
    end
end

@testset "Streaming pattern validation avoids CLI output files" begin
    mktempdir() do dir
        toy = joinpath(ROOT, "data", "toy", "example.txt")
        streamed = validate_pair_stream(toy, "0.4")
        cli = validate_pair(ROOT, toy, "0.4", dir)
        @test streamed.equal
        @test streamed.baseline_patterns == streamed.optimized_patterns == 15
        @test streamed.baseline_sha256 == cli.baseline_sha256
        @test streamed.optimized_sha256 == cli.optimized_sha256
        @test isempty(readdir(dir))
    end
end

@testset "Pair validator enforces CLI output cap and timeout" begin
    @test hasmethod(validate_pair, Tuple{String,String,String,String})
    @test_throws ArgumentError validate_pair(ROOT, joinpath(ROOT, "data", "toy", "example.txt"), "0.4", tempdir(); max_output_bytes=0)
    @test_throws ErrorException validate_pair(ROOT, joinpath(ROOT, "data", "toy", "example.txt"), "0.4", tempdir(); max_output_bytes=1)
    @test_throws ArgumentError validate_pair(ROOT, joinpath(ROOT, "data", "toy", "example.txt"), "0.4", tempdir(); timeout_seconds=0.0)
end

@testset "Benchmark configs include all scalability cases" begin
    base = TOML.parsefile(joinpath(ROOT, "bench", "config-baseline-20261119.toml"))
    opt = TOML.parsefile(joinpath(ROOT, "bench", "config-optimized-20261119.toml"))
    @test base["variant"] == "baseline"
    @test opt["variant"] == "optimized"
    base["variant"] = "optimized"
    @test base == opt
    @test base["scalability_fractions"] == [0.1, 0.25, 0.5, 0.75, 1.0]
    @test Set(base["scalability_datasets"]) == Set(["Chess", "Mushroom", "Retail", "Accidents", "T10I4D100K"])
    @test Set(keys(base["scalability_minsup"])) == Set(base["scalability_datasets"])
end
