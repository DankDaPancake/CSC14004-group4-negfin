const TransactionDB = Vector{Vector{Int}}

struct PreparedDB
    transactions::TransactionDB
    items::Vector{Int}
    supports::Vector{Int}
    min_count::Int
    n_transactions::Int
end

mutable struct BMCNode
    rank::Int
    count::Int
    bitmap::BigInt
    children::Dict{Int,BMCNode}
end

struct NodeInfo
    bitmap::BigInt
    count::Int
end
