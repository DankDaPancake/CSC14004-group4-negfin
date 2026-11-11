@testset "NegNodeset filters and weighted support" begin
    ready = isdefined(NegFIN, :negative_pair)
    @test ready
    if ready
        nodes = [NegFIN.NodeInfo(BigInt(5), 3), NegFIN.NodeInfo(BigInt(4), 2)]
        original = [(n.bitmap, n.count) for n in nodes]
        pair = NegFIN.negative_pair(nodes, 1)
        @test sum(n.count for n in pair) == 2
        @test NegFIN.extended_support(5, pair) == 3
        @test sum(n.count for n in NegFIN.negative_extension(nodes, 3)) == 5
        @test isempty(NegFIN.negative_extension(nodes, 2))
        @test NegFIN.extended_support(5, NegFIN.NodeInfo[]) == 5
        @test [(n.bitmap, n.count) for n in nodes] == original
        wide = [NegFIN.NodeInfo(BigInt(1) << 69, 7), NegFIN.NodeInfo(BigInt(1), 2)]
        @test only(NegFIN.negative_extension(wide, 70)).count == 7
        @test only(NegFIN.negative_pair(wide, 70)).count == 2
        @test isempty(NegFIN.negative_pair(NegFIN.NodeInfo[], 1))
    end
end
