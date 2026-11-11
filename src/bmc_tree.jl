"""Build the bitmap-coded prefix tree (paper Algorithm 1)."""
function build_bmc(prepared::PreparedDB)::BMCNode
    root = BMCNode(0, 0, BigInt(0), Dict{Int,BMCNode}())
    masks = [item_mask(rank) for rank in eachindex(prepared.items)]
    for transaction in prepared.transactions
        parent = root
        for rank in transaction
            node = get!(parent.children, rank) do
                BMCNode(rank, 0, parent.bitmap | masks[rank], Dict{Int,BMCNode}())
            end
            node.count += 1
            parent = node
        end
    end
    return root
end

"""Collect weighted records without the artificial root."""
function collect_nodesets(root::BMCNode, nitems::Int)::Vector{Vector{NodeInfo}}
    nodesets = [NodeInfo[] for _ in 1:nitems]
    stack = collect(values(root.children))
    while !isempty(stack)
        node = pop!(stack)
        push!(nodesets[node.rank], NodeInfo(node.bitmap, node.count))
        append!(stack, values(node.children))
    end
    return nodesets
end
