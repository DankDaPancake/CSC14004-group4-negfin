const USAGE = """
negFIN (Julia)
Usage: julia --project=. run.jl --input FILE --output FILE --minsup RATIO
       [--variant baseline|optimized] [--stats FILE.toml]
RATIO is a decimal in (0, 1], for example 0.4. Support in output is a count.
"""

function parse_cli(args::Vector{String})::CLIOptions
    options = Dict{String,String}()
    allowed = ("--input", "--output", "--minsup", "--variant", "--stats")
    position = 1
    while position <= length(args)
        key = args[position]
        key in allowed || throw(ArgumentError("Unknown option: $key"))
        haskey(options, key) && throw(ArgumentError("Repeated option: $key"))
        position < length(args) || throw(ArgumentError("Missing value for $key"))
        value = args[position+1]
        isempty(value) && throw(ArgumentError("Empty value for $key"))
        options[key] = value
        position += 2
    end
    for required in ("--input", "--output", "--minsup")
        haskey(options, required) || throw(ArgumentError("Required option: $required"))
    end
    variant = get(options, "--variant", "baseline")
    variant in ("baseline", "optimized") || throw(ArgumentError("Variant must be baseline or optimized"))
    return CLIOptions(options["--input"], options["--output"],
                      parse_minsup(options["--minsup"]), Symbol(variant), get(options, "--stats", nothing))
end

# Resolve existing ancestors as well as symlinks, including outputs not created yet.
function canonical_path(path::String)::String
    absolute = abspath(path)
    ispath(absolute) && return realpath(absolute)
    parent = dirname(absolute)
    parent == absolute && return absolute
    return normpath(joinpath(canonical_path(parent), basename(absolute)))
end

function paths_alias(a::String, b::String)::Bool
    left, right = canonical_path(a), canonical_path(b)
    # Windows names normally ignore case, including names/parents not created
    # yet. Fail conservatively before writing; samefile alone needs both files.
    if Sys.iswindows()
        lowercase(left) == lowercase(right) && return true
    else
        left == right && return true
    end
    return ispath(a) && ispath(b) && samefile(a, b)
end

function validate_paths(options::CLIOptions)::Nothing
    isfile(options.input) || throw(ArgumentError("Input file does not exist: $(options.input)"))
    paths_alias(options.input, options.output) && throw(ArgumentError("Input and output must be different files"))
    if options.stats !== nothing
        (paths_alias(options.input, options.stats) || paths_alias(options.output, options.stats)) &&
            throw(ArgumentError("Stats must be different from input and output"))
    end
    return nothing
end

"""Write to a sibling temporary file and rename only after the writer succeeds."""
function staged_write(writer::Function, destination::String)::Nothing
    directory = dirname(abspath(destination))
    mkpath(directory)
    path, io = mktemp(directory)
    try
        writer(io)
        close(io)
        # rename within one filesystem; do not remove the old result beforehand.
        Base.Filesystem.rename(path, abspath(destination))
    finally
        isopen(io) && close(io)
        ispath(path) && rm(path)
    end
    return nothing
end

function main(args::Vector{String})::Int
    if "--help" in args
        print(USAGE)
        return 0
    end
    started = time_ns()
    options = try
        parsed = parse_cli(args)
        validate_paths(parsed)
        parsed
    catch err
        println(stderr, "negFIN: ", sprint(showerror, err))
        return err isa ArgumentError ? 2 : 1
    end
    reading = time_ns()
    db = try
        open(read_spmf, options.input)
    catch err
        println(stderr, "negFIN: ", sprint(showerror, err))
        return err isa ArgumentError ? 2 : 1
    end
    read_seconds = (time_ns() - reading) / 1e9
    try
        mining = time_ns()
        summary = Ref{MiningSummary}()
        phases = Dict{String,Any}()
        counters = Dict{String,Any}()
        on_phase = options.stats === nothing ? nothing : (phase, metrics) -> begin
            phases[string(phase)] = Dict{String,Any}("seconds" => metrics.seconds,
                "bytes" => metrics.bytes, "gc_seconds" => metrics.gc_seconds)
            for key in (:bmc_nodes, :negative_records_scanned)
                haskey(metrics, key) && (counters[string(key)] = metrics[key])
            end
        end
        staged_write(options.output) do io
            miner = options.variant == :baseline ? mine_baseline : mine_optimized
            summary[] = miner(db, options.minsup; on_phase,
                emit=(items, support) -> write_itemset(io, items, support))
        end
        mine_write_seconds = (time_ns() - mining) / 1e9
        total_seconds = (time_ns() - started) / 1e9
        if options.stats !== nothing
            report = Dict{String,Any}(
                "variant" => string(options.variant), "julia_version" => string(VERSION),
                "n_transactions" => summary[].n_transactions, "min_count" => summary[].min_count,
                "n_frequent_items" => summary[].n_frequent_items, "n_patterns" => summary[].n_patterns,
                "read_seconds" => read_seconds, "mine_write_seconds" => mine_write_seconds,
                "total_seconds" => total_seconds, "phases" => phases, counters...)
            staged_write(io -> TOML.print(io, report), options.stats)
        end
        return 0
    catch err
        println(stderr, "negFIN: ", sprint(showerror, err))
        return 1
    end
end
