if !isdefined(Main, :collect_patterns)
    include(joinpath(@__DIR__, "helpers", "collect.jl"))
end

function mine_with_phases(db, minsup)
    emitted = Tuple{Vector{Int},Int}[]
    phases = Pair{Symbol,NamedTuple}[]
    summary = mine_baseline(db, minsup;
        emit=(items, support) -> push!(emitted, (items, support)),
        on_phase=(phase, metrics) -> push!(phases, phase => metrics))
    return (; emitted, phases, summary)
end

@testset "Phase metrics hook" begin
    toy = [[1,3,4], [2,3,5], [1,2,3,5], [2,5], [1,2,3,5]]
    rng = MersenneTwister(20261113)
    random_db = [sort!(unique(rand(rng, 1:12, rand(rng, 1:12)))) for _ in 1:40]
    cases = [(toy, big(2)//big(5)), ([[1,2,3], [1,2,3], [3]], big(2)//big(3)),
             (random_db, big(1)//big(5))]
    for (db, minsup) in cases
        plain = collect_patterns(db, minsup)
        hooked = mine_with_phases(db, minsup)
        # The hook must not change itemsets, supports or emission order.
        @test hooked.emitted == plain.emitted
        @test first.(hooked.phases) == [:normalize, :prepare, :build_bmc, :collect_nodesets, :mine]
        @test all(m.seconds >= 0 && m.bytes >= 0 && m.gc_seconds >= 0 for m in last.(hooked.phases))
        metrics = Dict(hooked.phases)
        @test metrics[:prepare].n_frequent_items == hooked.summary.n_frequent_items
        @test metrics[:mine].n_patterns == length(hooked.emitted) == hooked.summary.n_patterns
        @test metrics[:mine].negative_records_scanned >= 0
        prepared = NegFIN.prepare([sort!(unique(t)) for t in db], hooked.summary.min_count)
        nodesets = NegFIN.collect_nodesets(NegFIN.build_bmc(prepared), length(prepared.items))
        @test metrics[:collect_nodesets].bmc_nodes == sum(length, nodesets)
    end
    @test Dict(mine_with_phases(toy, big(2)//big(5)).phases)[:mine].negative_records_scanned > 0
    for (db, minsup) in [([[1], [2]], big(1)//big(1)), (Vector{Int}[], big(1)//big(2))]
        empty = mine_with_phases(db, minsup)
        @test first.(empty.phases) == [:normalize, :prepare]
        @test isempty(empty.emitted)
    end
end
