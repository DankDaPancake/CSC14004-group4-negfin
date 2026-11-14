using Test
using Random
using TOML
using SHA

const ROOT = dirname(@__DIR__)
if isfile(joinpath(ROOT, "src", "NegFIN.jl"))
    include(joinpath(ROOT, "src", "NegFIN.jl"))
    using .NegFIN
end

const LOCAL_GROUPS = ["io", "tree", "negnodesets", "mining", "optimized", "phases", "cli", "differential", "reference", "bench"]
groups = isempty(ARGS) ? filter(g -> isfile(joinpath(@__DIR__, "test_$g.jl")), LOCAL_GROUPS) : ARGS
for group in groups
    group in [LOCAL_GROUPS; "spmf"] || error("Unknown test group: $group")
    include(joinpath(@__DIR__, "test_$group.jl"))
end
