"""Read positive integer transactions; normalize items, retaining repeated transactions."""
function read_spmf(io::IO)::TransactionDB
    transactions = TransactionDB()
    for (number, raw) in enumerate(eachline(io))
        line = strip(number == 1 ? replace(raw, '\ufeff' => "") : raw)
        isempty(line) && continue
        first(line) in ('#', '%', '@') && continue
        items = Int[]
        for token in split(line)
            item = tryparse(Int, token)
            if item === nothing || item <= 0
                throw(ArgumentError("Invalid positive integer '$token' on line $number"))
            end
            push!(items, item)
        end
        push!(transactions, sort!(unique!(items)))
    end
    return transactions
end

"""Parse a decimal support ratio exactly, without a floating-point round trip."""
function parse_minsup(text::AbstractString)::Rational{BigInt}
    value = strip(text)
    occursin(r"^[0-9]+(?:\.[0-9]+)?$", value) ||
        throw(ArgumentError("minsup must be a decimal ratio in (0, 1], e.g. 0.4"))
    parts = split(value, '.')
    fraction = length(parts) == 2 ? parts[2] : ""
    ratio = parse(BigInt, parts[1] * fraction) // (BigInt(10)^length(fraction))
    0 < ratio <= 1 || throw(ArgumentError("minsup must be in (0, 1]"))
    return ratio
end

function min_support(r::Rational{BigInt}, n::Int)::Int
    n >= 0 || throw(ArgumentError("Transaction count must be nonnegative"))
    0 < r <= 1 || throw(ArgumentError("minsup must be in (0, 1]"))
    return Int(cld(numerator(r) * n, denominator(r)))
end

function write_itemset(io::IO, items::Vector{Int}, support::Int)::Nothing
    println(io, join(items, ' '), " #SUP: ", support)
    return nothing
end
