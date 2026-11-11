if !isdefined(Main, :read_patterns)
    include(joinpath(@__DIR__, "helpers", "spmf.jl"))
end

@testset "SPMF NegFIN correctness on full benchmark databases" begin
    jar = get(ENV, "SPMF_JAR", "")
    manifest_path = get(ENV, "FIM_BENCHMARK_MANIFEST", "")
    java = get(ENV, "JAVA_EXE", "java")
    isfile(jar) || error("Set SPMF_JAR to a downloaded spmf.jar")
    isfile(manifest_path) || error("Set FIM_BENCHMARK_MANIFEST to data/benchmark/manifest.toml")
    datasets = TOML.parsefile(manifest_path)["datasets"]
    @test Set(entry["name"] for entry in datasets) == Set(["Chess", "Mushroom", "Retail", "Accidents", "T10I4D100K"])
    @test length(datasets) == 5
    directory = joinpath(ROOT, "results", "spmf")
    mkpath(directory)
    version_text = read(`$java -jar $jar version`, String)
    version_match = match(r"SPMF version ([^\s]+)", version_text)
    version_match === nothing && error("Cannot determine SPMF version")
    report = Dict{String,Any}(
        "verified_at_unix" => time(), "julia_version" => string(VERSION),
        "java_version" => strip(read(`$java --version`, String)),
        "spmf_version" => version_match.captures[1],
        "spmf_jar_sha256" => bytes2hex(open(sha256, jar)),
        "measurement_note" => "Correctness runs, not a controlled performance comparison. Julia timings exclude process startup; SPMF timings include it.",
        "datasets" => Dict{String,Any}[])
    @testset "Failed reference run cannot reuse stale output" begin
        mktempdir() do dir
            stale = joinpath(dir, "old.txt")
            write(stale, "1 #SUP: 99\n")
            @test_throws ErrorException run_spmf(java, jar, joinpath(dir,"missing.txt"), stale, "0.4")
            @test read(stale, String) == "1 #SUP: 99\n"
        end
    end
    # Exercise the exact same reference runner on the hand-checked fixture first.
    toy_output = joinpath(directory, "toy.spmf.txt")
    run_spmf(java, jar, joinpath(ROOT,"data","toy","example.txt"), toy_output, "0.4")
    @test open(read_patterns, toy_output) == open(read_patterns, joinpath(ROOT,"data","toy","example.expected.txt"))
    for entry in datasets
        @testset "$(entry["name"])" begin
            name = entry["name"]
            input = normpath(joinpath(dirname(abspath(manifest_path)), entry["path"]))
            isfile(input) || error("Download $(entry["source_url"]) to $input")
            digest = bytes2hex(open(sha256, input))
            @test digest == entry["sha256"]
            transactions = open(read_spmf, input)
            @test length(transactions) == entry["expected_transactions"]
            n = length(transactions)
            transactions = nothing
            actual_path = joinpath(directory, "$name.julia.txt")
            reference_path = joinpath(directory, "$name.spmf.txt")
            started = time_ns()
            status = NegFIN.main(["--input",input,"--output",actual_path,"--minsup",entry["minsup"]])
            actual_seconds = (time_ns() - started) / 1e9
            @test status == 0
            status == 0 || error("Baseline failed for $name")
            reference_seconds = run_spmf(java, jar, input, reference_path, entry["minsup"])
            actual = open(read_patterns, actual_path)
            reference = open(read_patterns, reference_path)
            differences = compare_patterns(actual, reference)
            @test !isempty(actual)
            @test length(actual) == length(reference)
            @test differences == (; missing=0, extra=0, support_mismatch=0)
            row = Dict{String,Any}(
                "name"=>name, "source_url"=>entry["source_url"], "input_sha256"=>digest,
                "scope"=>"full", "n_transactions"=>n, "minsup"=>entry["minsup"],
                "min_count"=>min_support(parse_minsup(entry["minsup"]), n),
                "julia_patterns"=>length(actual), "spmf_patterns"=>length(reference),
                "missing"=>differences.missing, "extra"=>differences.extra,
                "support_mismatch"=>differences.support_mismatch,
                "julia_pipeline_seconds"=>actual_seconds, "spmf_process_seconds"=>reference_seconds)
            push!(report["datasets"], row)
            println("$name: full N=$n, patterns=$(length(actual)), missing=$(differences.missing), extra=$(differences.extra), support_mismatch=$(differences.support_mismatch)")
            flush(stdout)
            open(joinpath(ROOT,"results","correctness.toml"), "w") do io
                TOML.print(io, report)
            end
        end
    end
end
