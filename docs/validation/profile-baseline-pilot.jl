using Profile, SHA
include(joinpath(abspath(ARGS[1]), "src", "NegFIN.jl"))
using .NegFIN

dataset, minsup = ARGS[2], ARGS[3]
println("Julia: ", VERSION, "; threads: ", Threads.nthreads())
println("Input SHA256: ", bytes2hex(open(sha256, dataset)), "; minsup: ", minsup)
db = open(read_spmf, dataset)
ratio = parse_minsup(minsup)
mine_baseline([[1, 2], [1]], parse_minsup("0.5"); emit=(items, support)->nothing)

function run_once(db, ratio; profiling=false)
    count, digest = Ref(0), Ref(UInt(0))
    emit = (items, support) -> begin
        count[] += 1
        digest[] ⊻= hash((Tuple(items), support))
    end
    GC.gc()
    if profiling
        Profile.clear()
        elapsed = @elapsed Profile.@profile summary = mine_baseline(db, ratio; emit=emit)
    else
        elapsed = @elapsed summary = mine_baseline(db, ratio; emit=emit)
    end
    return (; elapsed, patterns=summary.n_patterns, count=count[], digest=digest[])
end

run_once([[1, 2], [1]], parse_minsup("0.5"))
plain = run_once(db, ratio)
sampled = run_once(db, ratio; profiling=true)
println("Plain: ", plain)
println("Sampled: ", sampled)
println("Pattern count and digest agree: ", (plain.patterns, plain.count, plain.digest) ==
        (sampled.patterns, sampled.count, sampled.digest))
Profile.print(format=:flat, sortedby=:count, mincount=10, C=false)
