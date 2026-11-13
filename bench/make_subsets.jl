# Write prefix subsets for the scalability datasets and print their SHA256.
# Usage: julia --project=. bench/make_subsets.jl [--config PATH] [--data-dir DIR]
include(joinpath(@__DIR__, "Bench.jl"))
using SHA
using TOML

function make_subsets(args::Vector{String})
    repo = dirname(@__DIR__)
    options = Dict(args[i] => args[i+1] for i in 1:2:length(args)-1)
    config = Bench.load_config(get(options, "--config", joinpath(repo, "bench", "config.toml")))
    manifest_path = joinpath(repo, config["manifest"])
    manifest = TOML.parsefile(manifest_path)
    data_dir = get(options, "--data-dir", dirname(manifest_path))
    out_dir = joinpath(repo, config["results_root"], "subsets")
    for name in config["scalability_datasets"]
        entry = Bench.manifest_entry(manifest, name)
        input = joinpath(data_dir, entry["path"])
        Bench.verify_input(input, entry["sha256"])
        for fraction in config["scalability_fractions"]
            path = Bench.subset_path(out_dir, name, fraction)
            n = Bench.prefix_subset(input, Float64(fraction), path)
            println(name, " ", fraction, " n=", n, " sha256=", bytes2hex(open(sha256, path)))
        end
    end
end

make_subsets(ARGS)
