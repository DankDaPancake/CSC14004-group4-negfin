# Peak resident set of a process that only loads NegFIN; subtracted as the runtime floor.
using TOML
include(joinpath(dirname(@__DIR__), "src", "NegFIN.jl"))
open(io -> TOML.print(io, Dict("maxrss_bytes" => Int(Sys.maxrss()))), ARGS[1], "w")
