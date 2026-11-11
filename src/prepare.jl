"""Order frequent items by (support, original ID), mapping them to 1-based ranks."""
function prepare(db::TransactionDB, min_count::Int)::PreparedDB
    counts = Dict{Int,Int}()
    for transaction in db, item in transaction
        counts[item] = get(counts, item, 0) + 1
    end
    items = sort!([item for (item, count) in counts if count >= min_count];
                  by=item -> (counts[item], item))
    ranks = Dict(item => rank for (rank, item) in enumerate(items))
    transactions = [sort!([ranks[item] for item in transaction if haskey(ranks, item)]; rev=true)
                    for transaction in db]
    return PreparedDB(transactions, items, [counts[item] for item in items], min_count, length(db))
end

function item_mask(rank::Int)::BigInt
    rank > 0 || throw(ArgumentError("Item rank must be positive"))
    return BigInt(1) << (rank - 1)
end
