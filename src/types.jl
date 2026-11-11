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

struct Candidate
    rank::Int
    support::Int
    negative::Vector{NodeInfo}
end

struct MiningContext
    prepared::PreparedDB
    nodesets::Vector{Vector{NodeInfo}}
end

struct MiningSummary
    n_transactions::Int
    min_count::Int
    n_frequent_items::Int
    n_patterns::Int
end
