# Run from the repository root with Julia 1.12.0 and one thread.
using Random, SHA
include(joinpath(@__DIR__, "..", "src", "NegFIN.jl"))
using .NegFIN

const WIDTHS = (5, 10, 20, 40)
const ITEM_COUNT = 512
const TRANSACTION_COUNT = 10_000
const SEED = 20261125
const MINSUP = "0.008"

function synthetic_transactions()
    rng = MersenneTwister(SEED)
    return [randperm(rng, ITEM_COUNT)[1:maximum(WIDTHS)] for _ in 1:TRANSACTION_COUNT]
end

function patterns(miner, db, threshold)
    found = Dict{Tuple,Int}()
    summary = miner(db, threshold; emit=(items, support) -> begin
        key = Tuple(items)
        haskey(found, key) && error("Duplicate pattern: $key")
        found[key] = support
    end)
    length(found) == summary.n_patterns || error("Pattern count mismatch")
    return found
end

function measure(miner, db, threshold)
    GC.gc()
    nodes = Ref(0)
    scans = Ref(0)
    sink = (_, _) -> nothing
    result = @timed miner(db, threshold; emit=sink, on_phase=(phase, metrics) -> begin
        phase == :collect_nodesets && (nodes[] = metrics.bmc_nodes)
        phase == :mine && (scans[] = metrics.negative_records_scanned)
    end)
    return (seconds=result.time, bytes=result.bytes, nodes=nodes[], scans=scans[],
            frequent=result.value.n_frequent_items, patterns=result.value.n_patterns)
end

function main()
    longest = synthetic_transactions()
    threshold = parse_minsup(MINSUP)
    println(stderr, "Julia=", VERSION, " threads=", Threads.nthreads(), " cpu=", first(Sys.cpu_info()).model,
            " os=", Sys.KERNEL, " seed=", SEED, " universe=", ITEM_COUNT,
            " n=", TRANSACTION_COUNT, " minsup=", MINSUP, " min_count=", min_support(threshold, TRANSACTION_COUNT))
    println("width,sha256,variant,rep,seconds,allocated_bytes,bmc_nodes,records_scanned,frequent_items,patterns")
    for width in WIDTHS
        db = [row[1:width] for row in longest]
        digest = bytes2hex(sha256(join((join(row, ' ') for row in db), '\n') * "\n"))
        baseline = patterns(mine_baseline, db, threshold)
        baseline == patterns(mine_optimized, db, threshold) || error("Output mismatch at width $width")
        # Warm the count-only path as well as the correctness path before measuring.
        measure(mine_baseline, db, threshold)
        measure(mine_optimized, db, threshold)
        for rep in 1:3
            variants = (("baseline", mine_baseline), ("optimized", mine_optimized))
            for (name, miner) in (isodd(rep) ? variants : reverse(variants))
                row = measure(miner, db, threshold)
                row.patterns == length(baseline) || error("Measured count mismatch at width $width")
                println(join((width, digest, name, rep, row.seconds, row.bytes, row.nodes,
                              row.scans, row.frequent, row.patterns), ','))
            end
        end
        flush(stdout)
        println(stderr, "Finished width=", width, " patterns=", length(baseline))
    end
end

main()
