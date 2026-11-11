@testset "BMC tree and weighted singleton Nodesets" begin
    ready = isdefined(NegFIN, :build_bmc)
    @test ready
    if ready
        p = NegFIN.prepare([[10, 20], [10, 20], [10, 30]], 1)
        @test p.items == [30, 20, 10]
        @test p.supports == [1, 2, 3]
        @test p.transactions == [[3, 2], [3, 2], [3, 1]]
        @test NegFIN.item_mask(65) == BigInt(1) << 64
        root = NegFIN.build_bmc(p)
        @test root.bitmap == 0
        @test root.count == 0
        @test root.children[3].count == 3
        @test root.children[3].children[2].count == 2
        @test root.children[3].children[2].bitmap == 6
        ns = NegFIN.collect_nodesets(root, 3)
        @test [sum(ni.count for ni in nodes; init=0) for nodes in ns] == [1, 2, 3]
        @test all(ni.count > 0 for nodes in ns for ni in nodes)
        @test p.n_transactions == 3
        q = NegFIN.prepare([[1], [2], [2]], 2)
        @test q.n_transactions == 3
        @test q.transactions == [Int[], [1], [1]]
        @test NegFIN.prepare([[7, 90], [7, 500]], 1).items == [90, 500, 7]
        empty = NegFIN.prepare([[1], [2]], 2)
        @test isempty(empty.items)
        @test isempty(NegFIN.build_bmc(empty).children)
        wide = NegFIN.prepare([[i] for i in 1:70], 1)
        @test wide.items == collect(1:70)
        wide_nodes = NegFIN.collect_nodesets(NegFIN.build_bmc(wide), 70)
        @test only(wide_nodes[70]).bitmap == BigInt(1) << 69
        @test only(wide_nodes[70]).count == 1
    end
end
