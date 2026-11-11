"""Emit the core and every subset of its equivalent items, with fresh ID vectors."""
function emit_family!(emit::Function, core::Vector{Int}, equivalent::Vector{Int},
                      support::Int, items::Vector{Int})::Int
    chosen = copy(core)
    function walk(position::Int)::Int
        if position > length(equivalent)
            emit(sort!([items[rank] for rank in chosen]), support)
            return 1
        end
        count = walk(position + 1)
        push!(chosen, equivalent[position])
        count += walk(position + 1)
        pop!(chosen)
        return count
    end
    return walk(1)
end

"""Visit jX using the remaining siblings iX, each carrying its own NegNodeset."""
function visit!(ctx::MiningContext, core::Vector{Int}, current::Candidate,
                siblings::Vector{Candidate}, inherited::Vector{Int}, emit::Function)::Int
    equivalent = copy(inherited)
    children = Candidate[]
    for sibling in siblings
        negative = if length(core) == 1
            negative_pair(ctx.nodesets[current.rank], sibling.rank)
        else
            negative_extension(sibling.negative, current.rank)
        end
        support = extended_support(current.support, negative)
        if support == current.support
            push!(equivalent, sibling.rank)
        elseif support >= ctx.prepared.min_count
            push!(children, Candidate(sibling.rank, support, negative))
        end
    end

    count = emit_family!(emit, core, equivalent, current.support, ctx.prepared.items)
    # All children must exist before descending: a child consumes another child's
    # negative records as Q=iX. Promoted items stay in the family, not in children.
    for (position, child) in enumerate(children)
        count += visit!(ctx, [child.rank; core], child, children[position+1:end], equivalent, emit)
    end
    return count
end

"""
    mine_baseline(db, minsup; emit) -> MiningSummary

Mine all nonempty frequent itemsets using negFIN. `minsup` is an exact
`Rational{BigInt}`. The callback receives original positive integer IDs,
sorted ascending, in an independently owned vector, and an integer support.
Transactions are copied and normalized; repeated transactions remain distinct.
"""
function mine_baseline(db::TransactionDB, minsup::Rational{BigInt}; emit::Function)::MiningSummary
    minimum = min_support(minsup, length(db))
    normalized = TransactionDB()
    for transaction in db
        all(>(0), transaction) || throw(ArgumentError("Item IDs must be positive integers"))
        push!(normalized, sort!(unique(transaction)))
    end
    prepared = prepare(normalized, minimum)
    isempty(prepared.items) && return MiningSummary(length(db), minimum, 0, 0)
    nodesets = collect_nodesets(build_bmc(prepared), length(prepared.items))
    context = MiningContext(prepared, nodesets)
    roots = [Candidate(rank, prepared.supports[rank], NodeInfo[]) for rank in eachindex(prepared.items)]
    count = 0
    for (position, root) in enumerate(roots)
        count += visit!(context, [root.rank], root, roots[position+1:end], Int[], emit)
    end
    return MiningSummary(length(db), minimum, length(prepared.items), count)
end
