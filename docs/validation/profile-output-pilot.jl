using Profile, SHA
include(joinpath(abspath(ARGS[1]), "src", "NegFIN.jl"))
using .NegFIN

dataset, minsup = ARGS[2], ARGS[3]
println("Julia: ", VERSION, "; threads: ", Threads.nthreads())
println("Input SHA256: ", bytes2hex(open(sha256, dataset)), "; minsup: ", minsup)
db = open(read_spmf, dataset)
ratio = parse_minsup(minsup)

function run_once(db, ratio, path; profiling=false)
    GC.gc()
    summary = Ref{MiningSummary}()
    elapsed = open(path, "w") do io
        emit = (items, support) -> write_itemset(io, items, support)
        if profiling
            Profile.clear()
            @elapsed Profile.@profile summary[] = mine_baseline(db, ratio; emit=emit)
        else
            @elapsed summary[] = mine_baseline(db, ratio; emit=emit)
        end
    end
    return (; elapsed, patterns=summary[].n_patterns, output_bytes=filesize(path),
            sha256=bytes2hex(open(sha256, path)))
end

mktempdir() do dir
    warm_path = joinpath(dir, "warm.txt")
    run_once([[1, 2], [1]], parse_minsup("0.5"), warm_path)
    plain = run_once(db, ratio, joinpath(dir, "plain.txt"))
    sampled = run_once(db, ratio, joinpath(dir, "sampled.txt"); profiling=true)
    println("Plain: ", plain)
    println("Sampled: ", sampled)
    println("Counts, output bytes and SHA256 agree: ",
            (plain.patterns, plain.output_bytes, plain.sha256) ==
            (sampled.patterns, sampled.output_bytes, sampled.sha256))
    Profile.print(format=:flat, sortedby=:count, mincount=10, C=false)
end
