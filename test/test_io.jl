@testset "SPMF input and exact thresholds" begin
    ready = isdefined(Main, :NegFIN) && isdefined(NegFIN, :read_spmf)
    @test ready
    if ready
        @test read_spmf(IOBuffer("# note\n% note\n@FILETYPE=x\n\n3 1 1\n3 1 1\n")) == [[1, 3], [1, 3]]
        @test read_spmf(IOBuffer("\ufeff@FILETYPE=x\n 5\t2  5 \n")) == [[2, 5]]
        @test isempty(read_spmf(IOBuffer("\n# empty\n@SOURCE=x\n")))
        @test parse_minsup("0.4") == big(2)//big(5)
        @test parse_minsup("1") == parse_minsup("1.0") == 1
        @test parse_minsup(" 0.07 ") == big(7)//big(100)
        @test min_support(parse_minsup("0.07"), 100) == 7
        @test min_support(parse_minsup("0.401"), 5) == 3
        @test min_support(parse_minsup("1"), 0) == 0
        for value in ("0", "-0.1", "1.1", "", "NaN", "Inf", "40%", "4e-1", ".4")
            @test_throws ArgumentError parse_minsup(value)
        end
        @test_throws ArgumentError min_support(big(1)//big(2), -1)
        for line in ("1 -2\n", "1 0\n", "1 nope\n", "99999999999999999999999999999\n")
            @test_throws ArgumentError read_spmf(IOBuffer(line))
        end
        failure = try
            read_spmf(IOBuffer("1 2\n3 x\n"))
        catch e
            e
        end
        @test occursin("2", sprint(showerror, failure))
        output = IOBuffer()
        @test write_itemset(output, [1, 3], 2) === nothing
        @test String(take!(output)) == "1 3 #SUP: 2\n"
    end
end
