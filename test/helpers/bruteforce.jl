"""Independent oracle; enumerate item subsets, then count containing transactions."""
function bruteforce(db::Vector{Vector{Int}}, min_count::Int)::Dict{Tuple{Vararg{Int}},Int}
    result = Dict{Tuple{Vararg{Int}},Int}()
    universe = sort!(unique([item for transaction in db for item in transaction]))
    length(universe) <= 20 || throw(ArgumentError("Exhaustive test oracle is only for small databases"))
    for mask in 1:(Int(1) << length(universe))-1
        items = [item for (position, item) in enumerate(universe) if mask & (1 << (position-1)) != 0]
        support = count(transaction -> all(item -> item in transaction, items), db)
        support >= min_count && (result[Tuple(items)] = support)
    end
    return result
end
