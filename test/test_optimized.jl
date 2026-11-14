if !isdefined(Main, :bruteforce)
    include(joinpath(@__DIR__, "helpers", "bruteforce.jl"))
end

function optimized_patterns(db, ratio)
    result = Dict{Tuple{Vararg{Int}},Int}()
    vectors = Vector{Int}[]
    summary = NegFIN.mine_optimized(db, ratio; emit=(items, support) -> begin
        key = Tuple(items)
        haskey(result, key) && error("Duplicate pattern: $key")
        result[key] = support
        push!(vectors, items)
    end)
    (; result, summary, vectors)
end

@testset "Optimized bitmap and mining" begin
    bits = NegFIN.word_bitmap((big(1) << 0) | (big(1) << 63) | (big(1) << 64) | (big(1) << 129), 130)
    @test all(NegFIN.word_has(bits, i) for i in (1, 64, 65, 130))
    @test all(!NegFIN.word_has(bits, i) for i in (2, 63, 66, 129))
    @test !NegFIN.word_has(UInt64[], 1)
    @test_throws ArgumentError NegFIN.word_has(bits, 0)
    saved_bits = copy(bits)
    for rank in 1:140
        NegFIN.word_has(bits, rank)
    end
    @test bits == saved_bits
    db = [[1,3,4], [2,3,5], [1,2,3,5], [2,5], [1,2,3,5]]
    before = deepcopy(db)
    actual = optimized_patterns(db, big(2)//big(5))
    @test actual.result == bruteforce(db, 2)
    @test actual.summary.n_patterns == 15
    @test db == before
    @test all(actual.vectors[i] !== actual.vectors[j] for i in eachindex(actual.vectors) for j in 1:i-1)
    rng = MersenneTwister(20261114)
    for _ in 1:30
        n = rand(rng, 1:8)
        sample = [unique(rand(rng, 1:n, rand(rng, 0:n))) for _ in 1:rand(rng, 1:12)]
        for ratio in (big(1)//big(4), big(1)//big(2), big(1)//big(1))
            threshold = Int(cld(numerator(ratio)*length(sample), denominator(ratio)))
            @test optimized_patterns(sample, ratio).result == bruteforce(sample, threshold)
        end
    end
    wide = [[i] for i in 1:130]
    @test optimized_patterns(wide, big(1)//big(130)).result == Dict((i,)=>1 for i in 1:130)
    cross = [[i] for i in 1:70]
    push!(cross, [1, 65, 70])
    cross_expected = Dict{Tuple{Vararg{Int}},Int}((i,) => (i in (1,65,70) ? 2 : 1) for i in 1:70)
    merge!(cross_expected, Dict((1,65)=>1, (1,70)=>1, (65,70)=>1, (1,65,70)=>1))
    @test optimized_patterns(cross, big(1)//big(71)).result == cross_expected
    @test isempty(optimized_patterns(Vector{Int}[], big(1)//big(2)).result)
    @test_throws ArgumentError optimized_patterns([[0,1]], big(1)//big(2))
    phase_names = Symbol[]
    measured = NegFIN.mine_optimized(db, big(2)//big(5); emit=(_, _)->nothing,
                                    on_phase=(phase, metrics)->push!(phase_names, phase))
    @test phase_names == [:normalize, :prepare, :build_bmc, :collect_nodesets, :mine]
    @test measured.n_patterns == 15
    empty_phases = Symbol[]
    NegFIN.mine_optimized(Vector{Int}[], big(1)//big(2); emit=(_, _)->nothing,
                          on_phase=(phase, metrics)->push!(empty_phases, phase))
    @test empty_phases == [:normalize, :prepare]
end
