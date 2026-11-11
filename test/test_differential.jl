if !isdefined(Main, :collect_patterns)
    include(joinpath(@__DIR__, "helpers", "collect.jl"))
end
if isfile(joinpath(@__DIR__, "helpers", "bruteforce.jl"))
    include(joinpath(@__DIR__, "helpers", "bruteforce.jl"))
end

@testset "Independent exhaustive oracle and metamorphic inputs" begin
    ready = isdefined(Main, :bruteforce)
    @test ready
    if ready
        rng = MersenneTwister(20261112)
        for trial in 1:50
            nitems, ntransactions = rand(rng, 1:8), rand(rng, 1:20)
            db = [sort!(unique(rand(rng, 1:nitems, rand(rng, 1:nitems)))) for _ in 1:ntransactions]
            for ratio in (big(1)//big(4), big(1)//big(2), big(3)//big(4), big(1)//big(1))
                count = Int(cld(numerator(ratio)*ntransactions, denominator(ratio)))
                expected = bruteforce(db, count)
                actual = collect_patterns(db, ratio)
                @test actual.supports == expected
                @test actual.summary.n_patterns == length(expected)
                @test all(!isempty(items) && support >= count for (items, support) in actual.emitted)
                shuffled = [shuffle(rng, t) for t in shuffle(rng, db)]
                @test collect_patterns(shuffled, ratio).supports == expected
                # Non-monotone original IDs exercise tie ordering and decoding.
                ids = shuffle(rng, [7 + 19*i for i in 1:nitems])
                mapped = [[ids[i] for i in t] for t in db]
                mapped_expected = Dict(Tuple(sort!([ids[i] for i in key])) => support for (key, support) in expected)
                @test collect_patterns(mapped, ratio).supports == mapped_expected
            end
        end
        mixed = [[1,2,3,4,5], [1,2,3,4], [1,2,6], [2,6], [1,2,3,5], [2,3,4,5]]
        @test collect_patterns(mixed, big(1)//big(3)).supports == bruteforce(mixed, 2)
        @test collect_patterns([Int[], [1], [1]], big(1)//big(1)).supports == Dict{Tuple{Vararg{Int}},Int}()
        @test collect_patterns(Vector{Int}[], big(1)//big(2)).supports == bruteforce(Vector{Int}[], 0)
    end
end
