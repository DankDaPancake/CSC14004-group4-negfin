if !isdefined(Main, :collect_patterns)
    include(joinpath(@__DIR__, "helpers", "collect.jl"))
end

@testset "Complete negFIN mining and promotion" begin
    ready = isdefined(NegFIN, :mine_baseline)
    @test ready
    if ready
        expected = Dict((1,)=>3, (2,)=>4, (3,)=>4, (5,)=>4,
            (1,2)=>2, (1,3)=>3, (1,5)=>2, (2,3)=>3, (2,5)=>4, (3,5)=>3,
            (1,2,3)=>2, (1,2,5)=>2, (1,3,5)=>2, (2,3,5)=>3, (1,2,3,5)=>2)
        db = [[1,3,4], [2,3,5], [1,2,3,5], [2,5], [1,2,3,5]]
        sample = collect_patterns(db, big(2)//big(5))
        @test sample.supports == expected
        @test length(sample.emitted) == sample.summary.n_patterns == 15
        @test sample.summary.n_transactions == 5
        @test sample.summary.min_count == 2
        @test sample.summary.n_frequent_items == 4
        promoted = collect_patterns([[1,2,3], [1,2,3], [3]], big(2)//big(3))
        @test promoted.supports == Dict((1,)=>2, (2,)=>2, (3,)=>3,
            (1,2)=>2, (1,3)=>2, (2,3)=>2, (1,2,3)=>2)
        @test length(collect_patterns([[1,2,3], [1,2,3]], big(1)//big(1)).emitted) == 7
        @test collect_patterns([[10], [10], [20]], big(2)//big(3)).supports == Dict((10,)=>2)
        @test isempty(collect_patterns([[1], [2]], big(1)//big(1)).emitted)
        @test collect_patterns(Vector{Int}[], big(1)//big(2)).summary.n_patterns == 0
        wide = collect_patterns([[i] for i in 1:70], big(1)//big(70))
        @test wide.supports == Dict((i,)=>1 for i in 1:70)
        @test collect_patterns([[90,7], [500,7]], big(1)//big(2)).supports ==
            Dict((7,)=>2, (90,)=>1, (500,)=>1, (7,90)=>1, (7,500)=>1)
        @test collect_patterns([[1,1,2], [2,1]], big(1)//big(1)).supports == Dict((1,)=>2, (2,)=>2, (1,2)=>2)
        @test db == [[1,3,4], [2,3,5], [1,2,3,5], [2,5], [1,2,3,5]]
        @test all(issorted(items) && !isempty(items) for (items, _) in sample.emitted)
        @test all(sample.emitted[i][1] !== sample.emitted[j][1]
                  for i in eachindex(sample.emitted) for j in 1:i-1)
        @test_throws ArgumentError collect_patterns([[0,1]], big(1)//big(2))
    end
end
