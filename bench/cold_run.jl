# Cold entry point: same as run.jl, then records this process's peak resident set.
# Usage: julia --project=. bench/cold_run.jl --maxrss FILE.toml <run.jl arguments...>
using TOML
position = findfirst(==("--maxrss"), ARGS)
position === nothing && error("--maxrss FILE is required")
maxrss_path = ARGS[position+1]
cli_args = [ARGS[1:position-1]; ARGS[position+2:end]]
include(joinpath(dirname(@__DIR__), "src", "NegFIN.jl"))
status = NegFIN.main(cli_args)
open(io -> TOML.print(io, Dict("maxrss_bytes" => Int(Sys.maxrss()), "exit_code" => status)), maxrss_path, "w")
exit(status)
