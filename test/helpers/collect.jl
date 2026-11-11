function collect_patterns(db::Vector{Vector{Int}}, minsup::Rational{BigInt})
    emitted = Tuple{Vector{Int},Int}[]
    summary = mine_baseline(db, minsup; emit=(items, support) -> push!(emitted, (items, support)))
    supports = Dict{Tuple{Vararg{Int}},Int}()
    for (items, support) in emitted
        key = Tuple(items)
        haskey(supports, key) && error("Duplicate pattern: $key")
        supports[key] = support
    end
    return (; emitted, supports, summary)
end
