if isfile(joinpath(@__DIR__, "helpers", "spmf.jl")) && !isdefined(Main, :read_patterns)
    include(joinpath(@__DIR__, "helpers", "spmf.jl"))
end

@testset "Reference parser and exact comparison" begin
    ready = isdefined(Main, :read_patterns)
    @test ready
    if ready
        actual = read_patterns(IOBuffer("@FILETYPE=Frequent itemsets\n3 1 #SUP: 2\n2 #SUP: 4\n"))
        reference = read_patterns(IOBuffer("2 #SUP: 4\n1 3 #SUP: 2\n"))
        @test actual == reference == Dict((1,3)=>2, (2,)=>4)
        @test compare_patterns(actual, reference) == (; missing=0, extra=0, support_mismatch=0)
        @test compare_patterns(Dict((2,)=>3, (5,)=>1), reference) == (; missing=1, extra=1, support_mismatch=1)
        @test_throws ArgumentError read_patterns(IOBuffer("1 3 #SUP: 2\n3 1 #SUP: 2\n"))
        @test_throws ArgumentError read_patterns(IOBuffer("1 1 #SUP: 2\n"))
        @test_throws ArgumentError read_patterns(IOBuffer("1 3\n"))
        @test_throws ArgumentError read_patterns(IOBuffer("#SUP: 2\n"))
    end
end
