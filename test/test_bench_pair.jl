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
        result = compare_outputs(left, right)
        @test !result.equal
        @test result.left_sha256 != result.right_sha256
    end
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
