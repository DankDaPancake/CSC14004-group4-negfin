using SHA
using TOML

"""Compare two CLI output files byte-for-byte and return their SHA256 digests."""
function compare_outputs(left::String, right::String)::NamedTuple
    left_bytes = read(left)
    right_bytes = read(right)
    return (left_sha256=bytes2hex(sha256(left_bytes)),
            right_sha256=bytes2hex(sha256(right_bytes)),
            equal=left_bytes == right_bytes)
end

"""Run both CLI variants on one input and compare exact output and pattern counts."""
function validate_pair(repo::String, input::String, minsup::String, output_dir::String)::NamedTuple
    mkpath(output_dir)
    baseline_output = joinpath(output_dir, "baseline.txt")
    optimized_output = joinpath(output_dir, "optimized.txt")
    baseline_stats = joinpath(output_dir, "baseline.toml")
    optimized_stats = joinpath(output_dir, "optimized.toml")
    julia = `$(Base.julia_cmd()) --startup-file=no --project=$repo`
    cli = joinpath(repo, "run.jl")
    try
        for (variant, output, stats) in (("baseline", baseline_output, baseline_stats),
                                         ("optimized", optimized_output, optimized_stats))
            cmd = `$julia $cli --input $input --output $output --minsup $minsup --variant $variant --stats $stats`
            run(cmd)
        end
        comparison = compare_outputs(baseline_output, optimized_output)
        baseline_patterns = TOML.parsefile(baseline_stats)["n_patterns"]
        optimized_patterns = TOML.parsefile(optimized_stats)["n_patterns"]
        return (baseline_sha256=comparison.left_sha256,
                optimized_sha256=comparison.right_sha256,
                baseline_patterns=baseline_patterns,
                optimized_patterns=optimized_patterns,
                equal=comparison.equal && baseline_patterns == optimized_patterns)
    finally
        for path in (baseline_output, optimized_output, baseline_stats, optimized_stats)
            isfile(path) && rm(path; force=true)
        end
    end
end
