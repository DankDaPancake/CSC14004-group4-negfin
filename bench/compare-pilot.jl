using SHA, TOML
include(joinpath(abspath(ARGS[1]), "src", "NegFIN.jl"))
using .NegFIN
path, minsup = ARGS[2], ARGS[3]
db = open(read_spmf, path)
ratio = parse_minsup(minsup)
emit_count(counter) = (items, support) -> (counter[] += 1)
for miner in (mine_baseline, mine_optimized)
    miner([[1,2], [1]], parse_minsup("0.5"); emit=emit_count(Ref(0)))
end
println("input_sha256=", bytes2hex(open(sha256, path)), " minsup=", minsup,
        " Julia=", VERSION, " threads=", Threads.nthreads())
for rep in 1:3
    for (label, miner) in (isodd(rep) ? (("baseline", mine_baseline), ("optimized", mine_optimized)) :
                                      (("optimized", mine_optimized), ("baseline", mine_baseline)))
        GC.gc()
        n = Ref(0)
        result = @timed miner(db, ratio; emit=emit_count(n))
        println("variant=", label, " rep=", rep, " seconds=", result.time,
                " bytes=", result.bytes, " gc_seconds=", result.gctime,
                " patterns=", result.value.n_patterns, " emitted=", n[])
        flush(stdout)
    end
end
