count_scanned!(::Nothing, ::Int) = nothing
count_scanned!(scanned::Base.RefValue{Int}, n::Int) = (scanned[] += n; nothing)

"""The pair iP loses records of P in which added item i is absent."""
function negative_pair(nodes::Vector{NodeInfo}, added_rank::Int; scanned=nothing)::Vector{NodeInfo}
    count_scanned!(scanned, length(nodes))
    mask = item_mask(added_rank)
    return [ni for ni in nodes if iszero(ni.bitmap & mask)]
end

"""For R=ijX, select records of sibling Q=iX that contain j (Property 7)."""
function negative_extension(sibling_negative::Vector{NodeInfo}, current_rank::Int; scanned=nothing)::Vector{NodeInfo}
    count_scanned!(scanned, length(sibling_negative))
    mask = item_mask(current_rank)
    return [ni for ni in sibling_negative if !iszero(ni.bitmap & mask)]
end

function extended_support(parent_support::Int, negative::Vector{NodeInfo})::Int
    return parent_support - sum(ni.count for ni in negative; init=0)
end
