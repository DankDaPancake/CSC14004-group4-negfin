function capture_main(args)
    mktemp() do _, out
        mktemp() do _, err
            status = redirect_stdout(out) do
                redirect_stderr(err) do
                    NegFIN.main(args)
                end
            end
            seekstart(out); seekstart(err)
            return (; status, stdout=read(out, String), stderr=read(err, String))
        end
    end
end

@testset "CLI integration and output safety" begin
    ready = isdefined(NegFIN, :main)
    @test ready
    if ready
        mktempdir() do dir
            input = joinpath(dir, "input with spaces.txt")
            cp(joinpath(ROOT, "data", "toy", "example.txt"), input)
            output = joinpath(dir, "output.txt")
            stats = joinpath(dir, "stats.toml")
            args = ["--input", input, "--output", output, "--minsup", "0.4", "--variant", "baseline", "--stats", stats]
            options = NegFIN.parse_cli(args)
            @test options.minsup == big(2)//big(5)
            @test options.variant == :baseline
            result = capture_main(args)
            @test result.status == 0
            @test isempty(result.stderr)
            @test sort(readlines(output)) == sort(readlines(joinpath(ROOT, "data", "toy", "example.expected.txt")))
            report = TOML.parsefile(stats)
            @test report["n_patterns"] == 15
            @test report["min_count"] == 2
            @test all(report[key] >= 0 for key in ("read_seconds", "mine_write_seconds", "total_seconds"))
            @test capture_main(["--help"]).status == 0
            for bad in (["--input"], ["--unknown", "x"], ["--input",input,"--input",input],
                        ["--input",input,"--output",output,"--minsup","0"],
                        ["--input",input,"--output",output,"--minsup","0.4","--variant","optimized"])
                @test capture_main(bad).status == 2
            end
            @test capture_main(["--input",joinpath(dir,"missing"),"--output",output,"--minsup","0.4"]).status == 2
            original = read(input, String)
            @test capture_main(["--input",input,"--output",input,"--minsup","0.4"]).status == 2
            alias = joinpath(dir, "alias.txt")
            hardlink(input, alias)
            @test capture_main(["--input",input,"--output",alias,"--minsup","0.4"]).status == 2
            @test capture_main(["--input",input,"--output",output,"--minsup","0.4","--stats",input]).status == 2
            @test read(input, String) == original
            if Sys.iswindows()
                # Both names are absent: samefile cannot detect this alias yet.
                case_output = joinpath(dir, "fresh-result.txt")
                case_stats = joinpath(dir, "FRESH-RESULT.TXT")
                @test capture_main(["--input",input,"--output",case_output,"--minsup","0.4","--stats",case_stats]).status == 2
                @test !ispath(case_output)
                # Resolve aliasing in parent directories that do not exist yet too.
                future_output = joinpath(dir, "FutureResults", "patterns.txt")
                future_stats = joinpath(dir, "futureresults", "PATTERNS.TXT")
                @test capture_main(["--input",input,"--output",future_output,"--minsup","0.4","--stats",future_stats]).status == 2
                @test !ispath(dirname(future_output))
            end
            write(output, "previous result\n")
            bad_input = joinpath(dir, "invalid.txt")
            write(bad_input, "1 2\n3 x\n")
            failure = capture_main(["--input",bad_input,"--output",output,"--minsup","0.4"])
            @test failure.status == 2
            @test occursin("line 2", failure.stderr)
            @test read(output, String) == "previous result\n"
            folder = mkdir(joinpath(dir, "not-a-file"))
            @test capture_main(["--input",input,"--output",folder,"--minsup","0.4"]).status == 1
            @test !any(endswith(".tmp"), readdir(dir))
            empty_input = joinpath(dir, "empty.txt")
            write(empty_input, "# metadata only\n")
            @test capture_main(["--input",empty_input,"--output",output,"--minsup","0.4"]).status == 0
            @test isempty(read(output, String))
            # The real entry point must propagate status to the operating system.
            proc = run(pipeline(ignorestatus(`$(Base.julia_cmd()) --startup-file=no --project=$ROOT $(joinpath(ROOT,"run.jl")) --minsup 0`), stdout=devnull, stderr=devnull))
            @test proc.exitcode == 2
        end
    end
end
