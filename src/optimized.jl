"""Copy a nonnegative bitmap into fixed-width, little-endian 64-bit words."""
function word_bitmap(bitmap::BigInt, nbits::Int)::Vector{UInt64}
    bitmap >= 0 && nbits >= 0 || throw(ArgumentError("Bitmap and width must be nonnegative"))
    words = zeros(UInt64, cld(nbits, 64))
    mask = (BigInt(1) << 64) - 1
    for i in eachindex(words)
        words[i] = UInt64((bitmap >> (64 * (i - 1))) & mask)
    end
    return words
end

function word_has(words::Vector{UInt64}, rank::Int)::Bool
    rank > 0 || throw(ArgumentError("Item rank must be positive"))
    index = ((rank - 1) >>> 6) + 1
    return index <= length(words) && !iszero(words[index] & (UInt64(1) << ((rank - 1) & 63)))
end

struct WordNodeInfo
    bitmap::Vector{UInt64}
    count::Int
end

struct WordCandidate
    rank::Int
    support::Int
    negative::Vector{WordNodeInfo}
end

function visit_word!(prepared::PreparedDB, nodesets::Vector{Vector{WordNodeInfo}}, scanned::Base.RefValue{Int},
                     core::Vector{Int}, current::WordCandidate, siblings::Vector{WordCandidate},
                     inherited::Vector{Int}, emit::Function)::Int
    equivalent = copy(inherited)
    children = WordCandidate[]
    for sibling in siblings
        source = length(core) == 1 ? nodesets[current.rank] : sibling.negative
        scanned[] += length(source)
        rank = length(core) == 1 ? sibling.rank : current.rank
        if length(core) == 1
            negative = [node for node in source if !word_has(node.bitmap, rank)]
        else
            negative = [node for node in source if word_has(node.bitmap, rank)]
        end
        support = current.support - sum(node.count for node in negative; init=0)
        if support == current.support
            push!(equivalent, sibling.rank)
        elseif support >= prepared.min_count
            push!(children, WordCandidate(sibling.rank, support, negative))
        end
    end
    count = emit_family!(emit, core, equivalent, current.support, prepared.items)
    for (position, child) in enumerate(children)
        count += visit_word!(prepared, nodesets, scanned, [child.rank; core], child,
                             children[position+1:end], equivalent, emit)
    end
    return count
end

"""Mine using word-vector bitmap tests for NegNodeset; BMC construction remains Baseline."""
function mine_optimized(db::TransactionDB, minsup::Rational{BigInt}; emit::Function, on_phase=nothing)::MiningSummary
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
    nodesets = run_phase(on_phase, :collect_nodesets, n -> (; bmc_nodes=sum(length, n))) do
        originals = collect_nodesets(tree, length(prepared.items))
        [[WordNodeInfo(word_bitmap(node.bitmap, length(prepared.items)), node.count) for node in nodes]
         for nodes in originals]
    end
    scanned = Ref(0)
    roots = [WordCandidate(rank, prepared.supports[rank], WordNodeInfo[]) for rank in eachindex(prepared.items)]
    patterns = run_phase(on_phase, :mine, c -> (; negative_records_scanned=scanned[], n_patterns=c)) do
        sum((visit_word!(prepared, nodesets, scanned, [root.rank], root,
                         roots[position+1:end], Int[], emit) for (position, root) in enumerate(roots)); init=0)
    end
    return MiningSummary(length(db), minimum, length(prepared.items), patterns)
end
