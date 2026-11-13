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
            negative_pair(ctx.nodesets[current.rank], sibling.rank; scanned=ctx.scanned)
        else
            negative_extension(sibling.negative, current.rank; scanned=ctx.scanned)
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

"""Run `work`; with a hook, time it and report `extra(result)` alongside."""
function run_phase(work::Function, on_phase, phase::Symbol, extra::Function=_ -> (;))
    on_phase === nothing && return work()
    stats = @timed work()
    on_phase(phase, (; seconds=stats.time, bytes=Int(stats.bytes), gc_seconds=stats.gctime,
                       extra(stats.value)...))
    return stats.value
end

"""
    mine_baseline(db, minsup; emit, on_phase=nothing) -> MiningSummary

Mine all nonempty frequent itemsets using negFIN. `minsup` is an exact
`Rational{BigInt}`. The callback receives original positive integer IDs,
sorted ascending, in an independently owned vector, and an integer support.
Transactions are copied and normalized; repeated transactions remain distinct.

When given, `on_phase(phase, metrics)` is called after each of `:normalize`,
`:prepare`, `:build_bmc`, `:collect_nodesets` and `:mine` (only the first two
when no item is frequent). `metrics` has `seconds`, `bytes` (total allocated,
not peak) and `gc_seconds`, plus phase-specific counters.
"""
function mine_baseline(db::TransactionDB, minsup::Rational{BigInt}; emit::Function,
                       on_phase=nothing)::MiningSummary
    minimum = min_support(minsup, length(db))
    normalized = run_phase(on_phase, :normalize) do
        copies = TransactionDB()
        for transaction in db
            all(>(0), transaction) || throw(ArgumentError("Item IDs must be positive integers"))
            push!(copies, sort!(unique(transaction)))
        end
        copies
    end
    prepared = run_phase(() -> prepare(normalized, minimum), on_phase, :prepare,
                         p -> (; n_frequent_items=length(p.items)))
    isempty(prepared.items) && return MiningSummary(length(db), minimum, 0, 0)
    tree = run_phase(() -> build_bmc(prepared), on_phase, :build_bmc)
    nodesets = run_phase(() -> collect_nodesets(tree, length(prepared.items)), on_phase,
                         :collect_nodesets, n -> (; bmc_nodes=sum(length, n)))
    context = MiningContext(prepared, nodesets)
    roots = [Candidate(rank, prepared.supports[rank], NodeInfo[]) for rank in eachindex(prepared.items)]
    patterns = run_phase(on_phase, :mine,
                         c -> (; negative_records_scanned=context.scanned[], n_patterns=c)) do
        emitted = 0
        for (position, root) in enumerate(roots)
            emitted += visit!(context, [root.rank], root, roots[position+1:end], Int[], emit)
        end
        emitted
    end
    return MiningSummary(length(db), minimum, length(prepared.items), patterns)
end
