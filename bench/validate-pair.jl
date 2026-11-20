using SHA
using TOML

"""Compare two CLI output files byte-for-byte and return their SHA256 digests."""
function compare_outputs(left::String, right::String; chunk_size::Int=1024*1024, max_bytes::Union{Nothing,Integer}=nothing)::NamedTuple
    chunk_size > 0 || throw(ArgumentError("chunk_size must be positive"))
    max_bytes !== nothing && (filesize(left) > max_bytes || filesize(right) > max_bytes) &&
        error("Output exceeds comparison cap of $max_bytes bytes")
    left_ctx, right_ctx = SHA.SHA2_256_CTX(), SHA.SHA2_256_CTX()
    equal = true
    open(left, "r") do left_io
        open(right, "r") do right_io
            left_buffer, right_buffer = Vector{UInt8}(undef, chunk_size), Vector{UInt8}(undef, chunk_size)
            while true
                left_n = readbytes!(left_io, left_buffer, chunk_size)
                right_n = readbytes!(right_io, right_buffer, chunk_size)
                left_n == 0 && right_n == 0 && break
                SHA.update!(left_ctx, view(left_buffer, 1:left_n))
                SHA.update!(right_ctx, view(right_buffer, 1:right_n))
                (left_n == right_n && @view(left_buffer[1:left_n]) == @view(right_buffer[1:right_n])) || (equal = false)
            end
        end
    end
    return (left_sha256=bytes2hex(SHA.digest!(left_ctx)),
            right_sha256=bytes2hex(SHA.digest!(right_ctx)),
            equal=equal)
end

compare_outputs(left::String, right::String)::NamedTuple = compare_outputs(left, right; chunk_size=1024*1024)

"""Hash emitted itemsets without retaining or writing the complete output."""
function validate_pair_stream(input::String, minsup::String)::NamedTuple
    db = open(NegFIN.read_spmf, input)
    digest_and_count(miner, db, minsup) = begin
        ctx = SHA.SHA2_256_CTX()
        count = Ref(0)
        summary = miner(db, NegFIN.parse_minsup(minsup); emit=(items, support) -> begin
            line = string(join(items, ' '), " #SUP: ", support, '\n')
            SHA.update!(ctx, codeunits(line))
            count[] += 1
        end)
        (digest=bytes2hex(SHA.digest!(ctx)), count=count[], summary=summary)
    end
    baseline = digest_and_count(NegFIN.mine_baseline, db, minsup)
    optimized = digest_and_count(NegFIN.mine_optimized, db, minsup)
    return (baseline_sha256=baseline.digest, optimized_sha256=optimized.digest,
            baseline_patterns=baseline.count, optimized_patterns=optimized.count,
            equal=baseline.digest == optimized.digest && baseline.count == optimized.count)
end

"""Count CLI output and staged sibling files written since a timestamp."""
function staged_output_bytes(dir::String, since::Float64; max_bytes::Union{Nothing,Integer}=nothing)::Int
    total = 0
    for name in readdir(dir)
        path = joinpath(dir, name)
        (startswith(name, "jl_") || name in ("baseline.txt", "optimized.txt")) || continue
        isfile(path) || continue
        mtime(path) >= since || continue
        total += filesize(path)
        max_bytes !== nothing && total > max_bytes && return total
    end
    return total
end

"""Run both CLI variants on one input and compare exact output and pattern counts."""
function validate_pair(repo::String, input::String, minsup::String, output_dir::String;
                       max_output_bytes::Integer=2*1024^3, timeout_seconds::Real=120)::NamedTuple
    max_output_bytes > 0 || throw(ArgumentError("max_output_bytes must be positive"))
    timeout_seconds > 0 || throw(ArgumentError("timeout_seconds must be positive"))
    mkpath(output_dir)
    baseline_output = joinpath(output_dir, "baseline.txt")
    optimized_output = joinpath(output_dir, "optimized.txt")
    baseline_stats = joinpath(output_dir, "baseline.toml")
    optimized_stats = joinpath(output_dir, "optimized.toml")
    julia = `$(Base.julia_cmd()) --startup-file=no --project=$repo`
    cli = joinpath(repo, "run.jl")
    try
        for (variant, output, stats) in (("baseline", baseline_output, baseline_stats),
                                         ("optimized", optimized_output, optimized_stats))
            cmd = `$julia $cli --input $input --output $output --minsup $minsup --variant $variant --stats $stats`
            started_at = time()
            process = run(pipeline(cmd; stdout=devnull, stderr=devnull); wait=false)
            started = time()
            status = "ok"
            while !process_exited(process)
                if time() - started > timeout_seconds
                    status = "timeout"
                elseif staged_output_bytes(dirname(output), started_at; max_bytes=max_output_bytes) > max_output_bytes
                    status = "output_cap"
                end
                if status != "ok"
                    kill(process)
                    break
                end
                sleep(0.1)
            end
            wait(process)
            status == "ok" || error("$variant CLI validation stopped: $status")
            success(process) || error("$variant CLI validation exited with code $(process.exitcode)")
            isfile(output) || error("$variant CLI produced no output")
            filesize(output) <= max_output_bytes || error("$variant CLI output exceeds $max_output_bytes bytes")
        end
        comparison = compare_outputs(baseline_output, optimized_output; max_bytes=max_output_bytes)
        baseline_patterns = TOML.parsefile(baseline_stats)["n_patterns"]
        optimized_patterns = TOML.parsefile(optimized_stats)["n_patterns"]
        return (baseline_sha256=comparison.left_sha256,
                optimized_sha256=comparison.right_sha256,
                baseline_patterns=baseline_patterns,
                optimized_patterns=optimized_patterns,
                equal=comparison.equal && baseline_patterns == optimized_patterns)
    finally
        for path in (baseline_output, optimized_output, baseline_stats, optimized_stats)
            isfile(path) && rm(path; force=true)
        end
    end
end
