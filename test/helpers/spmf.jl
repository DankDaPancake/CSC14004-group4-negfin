function read_patterns(io::IO)::Dict{Tuple{Vararg{Int}},Int}
    result = Dict{Tuple{Vararg{Int}},Int}()
    for (number, raw) in enumerate(eachline(io))
        line = strip(raw)
        isempty(line) && continue
        if first(line) in ('@', '%', '#') && !startswith(line, "#SUP:")
            continue
        end
        matched = match(r"^(.*?)\s*#SUP:\s*([0-9]+)\s*$", line)
        matched === nothing && throw(ArgumentError("Invalid pattern on line $number"))
        tokens = split(matched.captures[1])
        isempty(tokens) && throw(ArgumentError("Empty pattern on line $number"))
        items = [tryparse(Int, token) for token in tokens]
        any(item -> item === nothing || item <= 0, items) && throw(ArgumentError("Invalid item on line $number"))
        length(unique(items)) == length(items) || throw(ArgumentError("Repeated item on line $number"))
        key = Tuple(sort!(Int[item for item in items]))
        haskey(result, key) && throw(ArgumentError("Duplicate pattern on line $number: $key"))
        support = tryparse(Int, matched.captures[2])
        support !== nothing && support > 0 || throw(ArgumentError("Invalid support on line $number"))
        result[key] = support
    end
    return result
end

function compare_patterns(actual::AbstractDict, reference::AbstractDict)
    missing = count(key -> !haskey(actual, key), keys(reference))
    extra = count(key -> !haskey(reference, key), keys(actual))
    support_mismatch = count(key -> haskey(actual, key) && actual[key] != reference[key], keys(reference))
    return (; missing, extra, support_mismatch)
end

function run_spmf(java::String, jar::String, input::String, output::String, minsup::String)::Float64
    isfile(input) || error("SPMF input does not exist: $input")
    isfile(jar) || error("SPMF jar does not exist: $jar")
    started = time_ns()
    logfile = output * ".log"
    mktempdir(dirname(abspath(output))) do staging
        fresh_output = joinpath(staging, "patterns.txt")
        open(logfile, "w") do io
            process = run(pipeline(ignorestatus(`$java -Xmx1g -jar $jar run NegFIN $input $fresh_output $minsup`), stdout=io, stderr=io))
            success(process) || error("SPMF exited $(process.exitcode); inspect $logfile")
        end
        isfile(fresh_output) || error("SPMF did not create a fresh result; inspect $logfile")
        mv(fresh_output, output; force=true)
    end
    return (time_ns() - started) / 1e9
end
