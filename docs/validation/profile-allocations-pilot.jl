using Profile, SHA
include(joinpath(abspath(ARGS[1]), "src", "NegFIN.jl"))
using .NegFIN

dataset, minsup = ARGS[2], ARGS[3]
sample_rate = parse(Float64, ARGS[4])
println("Julia: ", VERSION, "; threads: ", Threads.nthreads())
println("Input SHA256: ", bytes2hex(open(sha256, dataset)), "; minsup: ", minsup,
        "; allocation sample rate: ", sample_rate)
db = open(read_spmf, dataset)
ratio = parse_minsup(minsup)

function run_once(db, ratio; profiling=false, sample_rate=0.0001)
    count, digest = Ref(0), Ref(UInt(0))
    emit = (items, support) -> begin
        count[] += 1
        digest[] ⊻= hash((Tuple(items), support))
    end
    GC.gc()
    if profiling
        Profile.Allocs.clear()
        elapsed = @elapsed Profile.Allocs.@profile sample_rate=sample_rate summary = mine_baseline(db, ratio; emit=emit)
    else
        elapsed = @elapsed summary = mine_baseline(db, ratio; emit=emit)
    end
    return (; elapsed, patterns=summary.n_patterns, count=count[], digest=digest[])
end

run_once([[1, 2], [1]], parse_minsup("0.5"))
plain = run_once(db, ratio)
sampled = run_once(db, ratio; profiling=true, sample_rate)
println("Plain: ", plain)
println("Sampled: ", sampled)
println("Pattern count and digest agree: ", (plain.patterns, plain.count, plain.digest) ==
        (sampled.patterns, sampled.count, sampled.digest))
allocs = Profile.Allocs.fetch().allocs
println("Sampled allocation events: ", length(allocs))
counts = Dict{String,Tuple{Int,Int}}()
for alloc in allocs
    key = string(alloc.type)
    old = get(counts, key, (0, 0))
    counts[key] = (old[1]+1, old[2]+alloc.size)
end
for (name, (count, bytes)) in sort!(collect(counts); by=x->x.second[2], rev=true)[1:min(20,length(counts))]
    println("type=", name, " sampled_count=", count, " sampled_bytes=", bytes)
end

# Nearest project frame is contextual: it can include allocations in callback
# or library code and is not proof that the named line allocated the object.
sites = Dict{String,Tuple{Int,Int}}()
project_files = Set(["mine.jl", "negnodesets.jl", "bmc_tree.jl", "prepare.jl", "io.jl"])
for alloc in allocs
    frame_index = findfirst(f -> basename(string(f.file)) in project_files, alloc.stacktrace)
    site = if frame_index === nothing
        "no project frame (runtime/callback)"
    else
        frame = alloc.stacktrace[frame_index]
        string(basename(string(frame.file)), ':', frame.line)
    end
    old = get(sites, site, (0, 0))
    sites[site] = (old[1]+1, old[2]+alloc.size)
end
println("Nearest project frame, sorted by sampled count:")
for (name, (count, bytes)) in sort!(collect(sites); by=x->x.second[1], rev=true)[1:min(20,length(sites))]
    println("site=", name, " sampled_count=", count, " sampled_bytes=", bytes)
end
