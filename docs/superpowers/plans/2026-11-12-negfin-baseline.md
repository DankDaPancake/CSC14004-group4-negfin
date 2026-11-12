# negFIN Baseline bằng Julia — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Thực hiện tuần tự trong phiên hiện tại; chỉ dùng subagent khi người dùng yêu cầu.

**Execution:** Baseline đã được triển khai ngày 12/11/2026; test local và đối chiếu 5 CSDL full đã chạy. Xem README và docs/validation/correctness.toml. Việc thành viên xác nhận trực tiếp và các sản phẩm ngoài Baseline chưa được coi là hoàn tất.

**Goal:** Dựng negFIN Baseline đúng paper bằng Julia, đọc/ghi SPMF, chạy qua CLI và kiểm chứng itemset/support bằng tính tay, vét cạn và SPMF trên 5 CSDL.

**Architecture:** Tách đọc/ghi, chuẩn hóa thứ tự item, BMC-tree, phép toán NegNodeset và duyệt tìm kiếm. Bitmap dùng `BigInt`; tập kết quả được phát qua callback để CLI ghi dần, không bắt buộc giữ mọi itemset trong RAM. Promotion là thành phần của Baseline; tối ưu bổ sung được thực hiện ở giai đoạn khác sau khi đo điểm nghẽn.

**Tech Stack:** Julia >= 1.9; Base và các thư viện chuẩn `Test`, `Random`, `TOML`, `SHA`; Java/SPMF NegFIN chỉ làm tham chiếu bên ngoài. Chưa thêm package Julia bên thứ ba.

**Spec:** [Yêu cầu và phân công](../../project-requirements.md), [contract Baseline](../../baseline-contract.md), [paper gốc](https://doi.org/10.1016/j.eswa.2018.03.041). Đọc phần 3–4, Algorithms 1/3/4 và Properties 5–9 của paper khi thực hiện. Thư mục hiện tại là `CSC14004-group4-negfin/`; tên `group04-fim-negfin/` phía dưới là tên lịch sử tại thời điểm lập kế hoạch.

## Global Constraints

- Ngôn ngữ đã chọn: Julia >= 1.9; thuật toán đã chọn: negFIN; thầy đã chấp thuận theo xác nhận của Đăng.
- Tự cài từ paper; không sao chép hoặc chuyển ngữ source Java/C++/GitHub có sẵn.
- Đầu ra gồm tất cả frequent itemset khác rỗng và support số đếm; không chỉ closed hoặc maximal.
- Có CLI nhận minsup và đường dẫn file; input/output tương thích SPMF .txt.
- Unit test tự động; đối chiếu với SPMF trên ít nhất 5 CSDL theo kế hoạch nhóm.
- Seed cố định cho test sinh dữ liệu; lưu phiên bản môi trường và tham số đối chiếu.
- Baseline phải bao gồm BMC-tree, NegNodeset, phép thử bit và promotion; không thay bằng Eclat hoặc vét cạn.
- Vét cạn chỉ là oracle trong test; không được dùng làm đường chạy của sản phẩm.
- Kế hoạch này chưa triển khai Optimized, biểu đồ benchmark, hai ứng dụng hoặc báo cáo PDF.

## Trạng thái, quyết định đã chốt và các lựa chọn đề xuất

- Ngày 12/11/2026: `group04-fim-negfin/` trống trước khi tạo tài liệu này, chưa là Git repository. Lệnh Julia/Java chưa được tìm thấy trong PATH. Chưa chạy test hay thuật toán.
- Dùng `group04-fim-negfin/` làm root triển khai theo tên thư mục hiện có; chưa suy ra tên GitHub remote hoặc mã nhóm đã được đăng ký.
- Đăng đã chốt đề xuất biểu diễn bitmap: **Baseline dùng `BigInt`**; sau khi có Baseline đúng và số liệu đo, đánh giá `BitVector` hoặc `Vector{UInt64}` cho bản tối ưu. Chưa chọn trước kiểu thay thế hoặc khẳng định nó nhanh hơn.
- Định dạng CLI và xử lý input trong tài liệu vẫn là các đề xuất cần review; việc chốt biểu diễn bitmap không tự xác nhận toàn bộ giao diện.
- Không đặt mục tiêu Baseline nhanh hơn SPMF. Mục tiêu là đúng, giải thích được và có phép đo tái lập.
- BigInt giúp tránh giới hạn 64 bit nhưng có chi phí cấp phát và thao tác nhiều word; không suy ra phép thử bitmap có chi phí hằng số với mọi số item.
- Khi bước sang tối ưu, đo riêng chi phí xây bitmap, thử một bit, số byte cấp phát và peak RAM; đối chiếu kết quả đầy đủ trước khi so hiệu năng trên cùng input/minsup. Giữ nguyên Baseline BigInt làm đối chứng.

## Review Focus

1. Ngưỡng thập phân, dòng metadata và giao dịch trùng: đếm đúng N, làm tròn đúng và không bỏ các giao dịch giống nhau. Test ở Task 1.
2. Hơn 64 item, ID thưa và support bằng nhau: bitmap không tràn, thứ tự nội bộ ổn định và xuất lại đúng ID gốc. Test ở Task 2 và Task 5.
3. Node có count > 1; mở rộng tập từ 3 item: lấy đúng NegNodeset của sibling Q, cộng count thay vì đếm node. Test ở Task 3 và Task 4.
4. Promotion nhiều cấp: xuất đủ các tổ hợp với support đúng và không sinh trùng, kể cả chỉ một đường đi trên cây. Test ở Task 4 và Task 6.
5. File lỗi, cùng đường dẫn input/output và tiến trình thất bại: báo lỗi rõ, không ghi đè dữ liệu đầu vào và không coi kết quả dở dang là thành công. Test ở Task 5 và Task 7.

## Cấu trúc file dự kiến

Tất cả đường dẫn dưới đây tính từ `group04-fim-negfin/`; đây là kế hoạch tạo file, chưa phải các file đã được cài đặt.

| File | Trách nhiệm |
| --- | --- |
| `Project.toml` | Môi trường Julia, compat >= 1.9 và thư viện chuẩn được dùng |
| `.gitignore` | Bỏ qua output chạy, jar, dữ liệu lớn và file tạm; không bỏ qua fixture nhỏ |
| `src/NegFIN.jl` | Module, include và API công khai |
| `src/types.jl` | Các kiểu dữ liệu chung được định nghĩa dưới đây |
| `src/io.jl` | Parser giao dịch, minsup và ghi itemset |
| `src/prepare.jl` | Đếm support, lọc và ánh xạ item sang rank |
| `src/bmc_tree.jl` | Dựng BMC-tree và lấy Nodeset |
| `src/negnodesets.jl` | Kernel kiểm tra bitmap và tính support |
| `src/mine.jl` | Tìm kiếm theo sibling, promotion và phát kết quả |
| `src/cli.jl`, `run.jl` | Đọc tham số, gọi API và mã thoát |
| `test/runtests.jl` | Điểm vào test; nhận tên nhóm test tùy chọn |
| `test/test_{io,tree,negnodesets,mining,cli,differential,spmf}.jl` | Các nhóm test tương ứng |
| `test/helpers/bruteforce.jl` | Oracle vét cạn độc lập cho CSDL nhỏ |
| `test/helpers/collect.jl` | Collector dùng trong test, giữ toàn bộ lần phát để bắt duplicate |
| `test/helpers/spmf.jl` | Gọi SPMF và chuẩn hóa đầu ra tham chiếu |
| `data/toy/example.txt`, `data/toy/example.expected.txt` | Ví dụ 5 giao dịch và 15 kết quả tính tay |
| `docs/baseline-contract.md` | Quy ước CLI/I/O bàn giao cho Hiếu và Tiến |
| `docs/negfin-baseline-notes.md` | Liên hệ code với paper, ví dụ và giải thích |
| `README.md` | Môi trường, lệnh chạy/test và trạng thái kiểm chứng |

Dùng `test/` để khớp lệnh đề bài `julia --project test/runtests.jl`; không tạo thêm `tests/` song song.

## Kiểu dữ liệu và quy ước dùng xuyên suốt

Định nghĩa trong `src/types.jl` khi task đầu tiên cần tới; không dùng `Any` cho trường dữ liệu hoặc biến toàn cục để giữ trạng thái tìm kiếm.

- `TransactionDB = Vector{Vector{Int}}`: item gốc là số nguyên dương; mỗi giao dịch đã sort/unique, các giao dịch giống nhau vẫn được giữ riêng.
- `PreparedDB`: `transactions::TransactionDB` chứa rank giảm dần, `items::Vector{Int}` ánh xạ rank → ID gốc, `supports::Vector{Int}`, `min_count::Int`, `n_transactions::Int`.
- Rank là chỉ số Julia 1-based; `items` xếp tăng theo `(support, ID gốc)`. Bit của rank r là `BigInt(1) << (r - 1)`. Giao dịch đưa vào cây theo rank giảm dần.
- `BMCNode`: `rank::Int`, `count::Int`, `bitmap::BigInt`, `children::Dict{Int,BMCNode}`. Root rank=0, count=0, bitmap=0; không đưa root vào Nodeset.
- `NodeInfo`: `bitmap::BigInt`, `count::Int`; một record cho mỗi node gốc, không gộp các record rồi làm mất trọng số.
- `Candidate`: `rank::Int`, `support::Int`, `negative::Vector{NodeInfo}`. Singleton để negative rỗng; tập >= 2 dùng NegNodeset thực.
- `MiningContext`: `prepared::PreparedDB`, `nodesets::Vector{Vector{NodeInfo}}`.
- `MiningSummary`: `n_transactions::Int`, `min_count::Int`, `n_frequent_items::Int`, `n_patterns::Int`.
- Callback `emit(items::Vector{Int}, support::Int)` nhận một vector mới, sort theo ID gốc; tìm kiếm không thay đổi vector đã bàn giao.
- `CLIOptions`: `input::String`, `output::String`, `minsup::Rational{BigInt}`, `variant::Symbol`, `stats::Union{Nothing,String}`.

## Task 1: Giao dịch SPMF, minsup và điểm vào test

**Files:** Create `Project.toml`, `.gitignore`, `src/NegFIN.jl`, `src/types.jl`, `src/io.jl`, `test/runtests.jl`, `test/test_io.jl`, `data/toy/example.txt`, `data/toy/example.expected.txt`.

**Interfaces:**
- Produces `read_spmf(io::IO)::TransactionDB`, `parse_minsup(text::AbstractString)::Rational{BigInt}`, `min_support(r::Rational{BigInt}, n::Int)::Int`, `write_itemset(io::IO, items::Vector{Int}, support::Int)::Nothing`.
- Test runner không có ARGS chạy các test local đã tạo; ARGS lọc nhóm test như `io`, `tree`, `mining`. Nhóm `spmf` chỉ chạy khi được gọi tường minh.

- [x] Chuẩn bị Julia >= 1.9, ghi phiên bản cụ thể; khởi tạo Git tại root này khi bắt đầu thực thi, không tạo repo bao trùm thư mục tài liệu môn học.
- [x] Viết test trước implementation:

```julia
@test read_spmf(IOBuffer("# note\n% note\n@FILETYPE=x\n\n3 1 1\n3 1 1\n")) == [[1, 3], [1, 3]]
@test parse_minsup("0.4") == big(2)//big(5)
@test min_support(parse_minsup("0.07"), 100) == 7
@test min_support(parse_minsup("0.401"), 5) == 3
@test min_support(parse_minsup("1"), 0) == 0
@test_throws ArgumentError parse_minsup("0")
@test_throws ArgumentError parse_minsup("1.1")
@test_throws ArgumentError read_spmf(IOBuffer("1 -2\n"))
```

- [x] Chạy `julia --project=. test/runtests.jl io`; xác nhận FAIL do API chưa được cài, không phải do thiếu Julia.
- [x] Cài parser: strip whitespace/BOM đầu file; bỏ dòng trắng và dòng bắt đầu `#`, `%`, `@`; normalize item trùng trong một dòng nhưng giữ nguyên số dòng giao dịch hợp lệ. Reject token không nguyên dương hoặc vượt Int, kèm số dòng.
- [x] Chỉ nhận minsup dạng thập phân `0.4`, `1`, `1.0` với 0 < r <= 1; reject `%`, NaN, Inf, số mũ và chuỗi rỗng ở phiên bản đầu. Parse chữ số bằng BigInt, không đi qua Float64; dùng `cld(numerator(r)*n, denominator(r))` rồi chuyển kết quả sang Int; n âm là lỗi.
- [x] Thêm test BOM, khoảng trắng/tab, metadata-only, item 0, token chữ, minsup âm/NaN và output đúng chuỗi `1 3 #SUP: 2\n`; chạy lại test đến PASS.
- [x] Lưu fixture 5 giao dịch trong checklist khởi động. Expected có 15 mẫu: singleton `1:3, 2:4, 3:4, 5:4`; pair `12:2, 13:3, 15:2, 23:3, 25:4, 35:3`; triple `123:2, 125:2, 135:2, 235:3`; quadruple `1235:2`. Các ký hiệu viết gọn này là tập item, không phải số nguyên ghép chữ số; file thực dùng khoảng trắng và `#SUP:`.
- [x] Commit: `feat: add SPMF IO and exact support thresholds`.

**Gate:** parser/threshold test pass; fixture được kiểm lại bằng tính tay. Chưa tuyên bố negFIN chạy được.

## Task 2: Chuẩn hóa thứ tự, BMC-tree và Nodeset

**Files:** Create `src/prepare.jl`, `src/bmc_tree.jl`, `test/test_tree.jl`; Modify `src/types.jl`, `src/NegFIN.jl`, `test/runtests.jl`.

**Interfaces:**
- Consumes Task 1 types và min_support.
- Produces `prepare(db::TransactionDB, min_count::Int)::PreparedDB`, `item_mask(rank::Int)::BigInt`, `build_bmc(prepared::PreparedDB)::BMCNode`, `collect_nodesets(root::BMCNode, nitems::Int)::Vector{Vector{NodeInfo}}`.
- `prepare` giữ `n_transactions = length(db)` kể cả giao dịch rỗng sau lọc; không tính lại N trên giao dịch còn item.

- [x] Viết test ordering, BigInt và prefix count:

```julia
p = prepare([[10, 20], [10, 20], [10, 30]], 1)
@test p.items == [30, 20, 10]
@test p.transactions == [[3, 2], [3, 2], [3, 1]]
@test item_mask(65) == BigInt(1) << 64
root = build_bmc(p)
@test root.children[3].count == 3
@test root.children[3].children[2].count == 2
@test root.children[3].children[2].bitmap == 6
ns = collect_nodesets(root, 3)
@test sum(ni.count for ni in ns[2]) == 2
```

- [x] Chạy `julia --project=. test/runtests.jl tree`; xác nhận FAIL vì các API chưa có.
- [x] Cài prepare và Algorithms 1/3 phần dựng cây/Nodeset; root có bitmap 0, bitmap con = bitmap cha OR mask item. Xếp tie theo ID để chỉ có một thứ tự toàn phần.
- [x] Thêm test nhiều nhánh, tất cả item bị lọc, ID thưa `[7, 90, 500]` và 70 singleton có cùng support; Nodeset giữ đúng tổng count và root bị loại.
- [x] Chạy `julia --project=. test/runtests.jl io tree`; yêu cầu PASS. Không sửa hay mutate bitmap BigInt đã gắn cho node khác.
- [x] Commit: `feat: construct BMC tree and singleton nodesets`.

**Gate:** hình cây và weighted support khớp tính tay; bitmap hoạt động ở bit 65 trở lên.

## Task 3: Kernel NegNodeset và support

**Files:** Create `src/negnodesets.jl`, `test/test_negnodesets.jl`; Modify `src/NegFIN.jl`, `test/runtests.jl`.

**Interfaces:**
- Consumes `NodeInfo`, `item_mask`.
- Produces `negative_pair(nodes::Vector{NodeInfo}, added_rank::Int)::Vector{NodeInfo}`, `negative_extension(sibling_negative::Vector{NodeInfo}, current_rank::Int)::Vector{NodeInfo}`, `extended_support(parent_support::Int, negative::Vector{NodeInfo})::Int`.
- Pair: lọc Nodeset của singleton hiện tại theo bit item thêm bằng 0.
- Extension P=jX, R=ijX: lọc NegNodeset(Q=iX) theo bit j bằng 1. Q là sibling cùng prefix X, không phải NegNodeset(P).

- [x] Viết test định nghĩa với trọng số và mask khác bit thấp nhất:

```julia
nodes = [NodeInfo(BigInt(5), 3), NodeInfo(BigInt(4), 2)]
@test sum(ni.count for ni in negative_pair(nodes, 1)) == 2
@test extended_support(5, negative_pair(nodes, 1)) == 3
@test sum(ni.count for ni in negative_extension(nodes, 3)) == 5
@test isempty(negative_extension(nodes, 2))
```

- [x] Chạy `julia --project=. test/runtests.jl negnodesets`; xác nhận FAIL trước khi cài kernel.
- [x] Cài theo Definitions 9/10 và Properties 6/7/8. Kiểm tra bit bật bằng `(bitmap & mask) != 0`, không dịch nguyên điều kiện `== 1` trong giả mã sang so sánh số nguyên vì mask có thể là 4, 8, ...
- [x] Thêm test NegNodeset rỗng, record count > 1 và rank 70; xác nhận kernel không mutate đầu vào, support = support cha trừ tổng count của các record âm.
- [x] Chạy `julia --project=. test/runtests.jl io tree negnodesets`; yêu cầu PASS.
- [x] Commit: `feat: implement weighted NegNodeset kernels`.

**Gate:** cả hai trường hợp pair/extension đều có ví dụ đúng độc lập; không nhầm số node với support.

## Task 4: Tìm kiếm đầy đủ và promotion

**Files:** Create `src/mine.jl`, `test/test_mining.jl`, `test/helpers/collect.jl`; Modify `src/types.jl`, `src/NegFIN.jl`, `test/runtests.jl`, Create `docs/negfin-baseline-notes.md`.

**Interfaces:**
- Produces API công khai `mine_baseline(db::TransactionDB, minsup::Rational{BigInt}; emit::Function)::MiningSummary`.
- Nội bộ `emit_family!(emit::Function, core::Vector{Int}, equivalent::Vector{Int}, support::Int, items::Vector{Int})::Int` trả số mẫu đã phát.
- Nội bộ `visit!(ctx::MiningContext, core::Vector{Int}, current::Candidate, siblings::Vector{Candidate}, inherited::Vector{Int}, emit::Function)::Int` trả số mẫu của nhánh.
- `core` gồm các rank trên prefix thực, xếp giảm; `current.rank == first(core)`. `siblings` là các candidate cùng parent X với current jX, có rank i > j và đã xếp tăng; negative của mỗi sibling biểu diễn Q=iX.
- Helper test `collect_patterns(db::TransactionDB, minsup::Rational{BigInt})` trả NamedTuple có `emitted::Vector{Tuple{Vector{Int},Int}}`, `supports::Dict{Tuple{Vararg{Int}},Int}` và `summary::MiningSummary`. Helper assert không duplicate trước khi tạo supports; chỉ được include trong test.

- [x] Viết test với collector append vào vector, giữ cả thứ tự phát và số lần phát; tạo map từ tuple item → support chỉ sau khi xác nhận không có tuple lặp. Không dùng map ghi đè để che lỗi duplicate.
- [x] Ghim các assertion sau trong test:

```julia
# expected_from_fixture là Dict tuple → support khai báo trực tiếp trong test
# từ 15 kết quả tính tay ở Task 1, không được tính bằng chính thuật toán.
sample = collect_patterns([[1,3,4], [2,3,5], [1,2,3,5], [2,5], [1,2,3,5]], big(2)//big(5))
got, emitted = sample.supports, sample.emitted
@test got == expected_from_fixture
@test length(emitted) == length(got) == 15
promotion_got = collect_patterns([[1,2,3], [1,2,3], [3]], big(2)//big(3)).supports
@test promotion_got == Dict((1,)=>2, (2,)=>2, (3,)=>3,
    (1,2)=>2, (1,3)=>2, (2,3)=>2, (1,2,3)=>2)
# promotion_db = [[1,2,3], [1,2,3], [3]], minsup = 2//3
```

- [x] Chạy `julia --project=. test/runtests.jl mining`; xác nhận FAIL trước implementation.
- [x] Dựng các singleton Candidate; gọi visit theo rank tăng và chỉ truyền các sibling có rank lớn hơn current. Nhánh rỗng không phát empty itemset; DB rỗng cho summary 0 mẫu.
- [x] Trong visit, tính **toàn bộ candidate mở rộng trước khi đệ quy**. Nếu core dài 1, dùng negative_pair trên Nodeset của current; nếu dài >= 2, dùng negative_extension trên sibling. Tính support qua kernel Task 3.
- [x] Nếu support mới bằng support current, ghi rank vào equivalent cục bộ; nếu support >= min_count và nhỏ hơn support current, lưu Candidate con; còn lại bỏ. Equivalent đã kế thừa không được đưa lại vào danh sách candidate.
- [x] Phát mỗi core hợp với mọi tập con của inherited ∪ equivalent cục bộ, gồm tập con rỗng, cùng support current; decode ID gốc và sort. Đệ quy vào các candidate con với tail của danh sách con và equivalent đã kế thừa. Đây là biểu diễn DFS của phép khai triển family/promotion trong paper, không tạo một thuật toán FIM khác.
- [x] Chỉ phát singleton qua cơ chế family; không phát thêm lần riêng kiểu F ∪ L1 rồi lại in family. Không sinh lại mẫu bằng một nhánh chứa item đã promote.
- [x] Thêm test all-identical 3 item cho đúng 7 mẫu, single item, item bị lọc, DB rỗng và 70 giao dịch singleton cho đúng 70 mẫu ở minsup 1//70. Không test 70 item luôn đi cùng nhau vì sẽ đòi xuất 2^70-1 mẫu.
- [x] Ghi notes: mapping paper → code, invariants sibling, promotion, quy ước rank/bit, chi phí bitmap theo số word và output size. Không chép nguyên pseudocode hoặc khẳng định độ phức tạp độc lập với output.
- [x] Chạy toàn bộ test local hiện có; yêu cầu PASS; commit `feat: mine complete frequent itemsets with negFIN promotion`.

**Gate:** ví dụ 15 mẫu, promotion 7 mẫu, trường hợp >64 item đều đúng; callback không nhận vector bị tái sử dụng/mutate sau đó.

## Task 5: CLI, xuất streaming và dữ liệu thống kê

**Files:** Create `src/cli.jl`, `run.jl`, `test/test_cli.jl`, `docs/baseline-contract.md`, `README.md`; Modify `src/types.jl`, `src/NegFIN.jl`, `test/runtests.jl`.

**Interfaces:**
- `parse_cli(args::Vector{String})::CLIOptions`; `main(args::Vector{String})::Int`.
- `run.jl` gọi module và `exit(main(ARGS))`; module không tự thoát process khi được import.
- Lệnh: `julia --project=. run.jl --input <path> --output <path> --minsup 0.4 --variant baseline [--stats <path.toml>]`.
- Chỉ hỗ trợ baseline; yêu cầu optimized phải báo chưa hỗ trợ, không âm thầm chạy baseline. `--help` thoát 0; lỗi tham số/input thoát 2, lỗi thực thi/I/O thoát 1; thông báo ở stderr.

- [x] Viết test parse và CLI subprocess trước implementation: fixture → exit 0, 15 dòng kết quả; minsup lỗi → exit 2; file không tồn tại → exit 2; variant optimized → exit 2.
- [x] Chạy `julia --project=. test/runtests.jl cli`; xác nhận FAIL.
- [x] Cài CLI dùng parser nhỏ của nhóm, không thêm package để parse 5 option. Output dùng callback ghi từng dòng; toàn bộ kết quả không bị giữ trong RAM ở CLI.
- [x] Ghi vào file tạm cùng thư mục output và chỉ thay output sau khi chạy thành công; reject input/output trỏ cùng file kể cả đường dẫn tương đối khác nhau hoặc symlink. Reject stats trùng input/output. Kiểm tra đường dẫn canonical khi thực thi.
- [x] `--stats` ghi TOML bằng stdlib: `variant`, `julia_version`, `n_transactions`, `min_count`, `n_frequent_items`, `n_patterns`, `read_seconds`, `mine_write_seconds`, `total_seconds`. mine_write gồm chuẩn bị, xây cây, khai thác và ghi; total bao phủ pipeline trong main, **không** đo startup trước khi Julia gọi main. Không gắn nhãn các giá trị này là pure mining hoặc peak RAM.
- [x] Thêm test output/temp cleanup khi có lỗi, đường dẫn có khoảng trắng, cùng input/output, metadata-only input tạo output rỗng, stats.n_patterns=15 và các thời gian không âm. Test callback phát bản copy bằng giữ snapshot sau khi mining hoàn tất.
- [x] Chạy test local; thử lệnh demo dưới đây và ghi ví dụ vào README/contract; chỉ ghi câu lệnh thật sự chạy và kết quả thật.

```text
julia --project=. test/runtests.jl
julia --project=. run.jl --input data/toy/example.txt --output results/toy.txt --minsup 0.4 --variant baseline --stats results/toy.stats.toml
```

- [x] Commit `feat: expose baseline CLI with streaming output and run stats`.

**Gate:** Hiếu/Tiến gọi được một lệnh ổn định; file kết quả chỉ có itemset/support; thông số thống kê nêu rõ phạm vi đo.

## Task 6: Differential test với vét cạn độc lập

**Files:** Create `test/helpers/bruteforce.jl`, `test/test_differential.jl`; Modify `test/runtests.jl`.

**Interfaces:** `bruteforce(db::TransactionDB, min_count::Int)::Dict{Tuple{Vararg{Int}},Int}` chỉ dùng trong test.

Consumes `collect_patterns` từ Task 4 để lấy kết quả sản phẩm và bắt duplicate trước khi đối chiếu oracle.

- [x] Viết oracle tự liệt kê các tập con khác rỗng của universe, đếm số giao dịch chứa mỗi tập, lọc min_count; không tái dùng BMC/NegNodeset để tránh hai bên cùng một lỗi.
- [x] Dùng `MersenneTwister(20261112)`, sinh 50 DB có 1–8 item và 1–20 giao dịch không rỗng, có giao dịch trùng; kiểm tra các ngưỡng 1/4, 1/2, 3/4, 1 và một trường hợp không có transaction.
- [x] Mỗi lần kiểm tra: support map bằng oracle, không có duplicate, không có empty itemset, min_count đúng. Thêm biến đổi hoán vị thứ tự giao dịch/item và đổi ID sang các số nguyên dương thưa; kết quả chỉ đổi theo ánh xạ ID.
- [x] Thêm fixture promotion nhiều cấp có cả candidate strict và promoted, để test được việc truyền equivalent qua ít nhất hai cấp.
- [x] Chạy `julia --project=. test/runtests.jl differential`; nếu có failure, lưu seed, input và minsup tái hiện, viết regression test rồi sửa đúng phần thuật toán.
- [x] Chạy toàn bộ test local; yêu cầu PASS; commit `test: verify negFIN against independent exhaustive oracle`.

**Gate:** mọi test đối chiếu đều pass; không dùng thời gian chạy của oracle làm benchmark negFIN.

## Task 7: Đối chiếu SPMF trên 5 CSDL và bàn giao

**Files:** Create `test/helpers/spmf.jl`, `test/test_spmf.jl`; Modify `README.md`, `docs/baseline-contract.md`, `docs/negfin-baseline-notes.md`, `test/runtests.jl`.

**Interfaces:**
- Đầu vào tích hợp: biến `SPMF_JAR` trỏ jar đã có, `FIM_BENCHMARK_MANIFEST` trỏ TOML do Hiếu chuẩn bị.
- Manifest có 5 bảng `[[datasets]]`: `name`, `path`, `minsup` (chuỗi thập phân), `source_url`; đường dẫn dataset tương đối tính từ vị trí manifest.
- Tên dataset: Chess, Mushroom, Retail, Accidents, T10I4D100K. Hiếu chọn và ghi ngưỡng thực tế có output không rỗng, phù hợp tài nguyên; ưu tiên chạy mẫu nhỏ để khảo sát trước, nhưng phải ghi rõ sample/full. Không bịa kết quả hoặc coi sample đã thay thế kiểm chứng full.

- [x] Phối hợp Hiếu chuẩn bị Java, SPMF jar, dataset và manifest; ghi phiên bản, nguồn, SHA256 input, minsup và thời điểm chạy. Không đọc source SPMF.
- [x] Viết parser output tham chiếu thành map tuple item → support, bỏ metadata/blank và chuẩn hóa thứ tự; test parser bằng file nhỏ tự viết có thứ tự khác output nhóm. Duplicate phải báo lỗi.
- [x] Gọi cùng input/minsup: `java -jar <jar> run NegFIN <input> <reference-output> <minsup>`; đối chiếu count, mọi key và mọi support. SPMF trả mã lỗi hoặc kết quả thiếu thì test phải FAIL; thiếu env khi gọi nhóm `spmf` cũng FAIL với hướng dẫn, không skip rồi báo đã pass.
- [x] Ghim unit test so sánh parser: thứ tự dòng/item khác vẫn bằng; thiếu mẫu, dư mẫu hoặc sai support đều bị phát hiện. Khi lệch ngưỡng số thực, ghi rõ min_count hai bên và chọn giá trị kiểm chứng được, không nới tolerance cho support nguyên.
- [x] Chạy `julia --project=. test/runtests.jl spmf`; bắt đầu fixture rồi 5 tập full ở ngưỡng manifest. Lưu báo cáo `results/correctness.toml` gồm dataset, SHA256, n_patterns của hai bên, missing, extra, support_mismatch và trạng thái sample/full. Kết quả chạy không commit cùng dữ liệu lớn; README ghi output cuối cùng có dẫn chiếu cấu hình.
- [ ] Đăng bàn giao CLI/API và giải thích thuật toán; Hiếu xác nhận harness hoạt động, Tiến thử một file giao dịch ứng dụng qua cùng CLI. Đây là kiểm tra tích hợp, chưa thay cho thực hiện hai ứng dụng đầy đủ.
- [x] Chạy lại test local, cập nhật README theo bằng chứng thực tế và commit `test: validate baseline against SPMF NegFIN`.

**Gate:** kết quả full của 5 tập được đối chiếu hoàn toàn ở cấu hình ghi lại; mọi missing/extra/support_mismatch bằng 0. Nếu thiếu runtime/dữ liệu hoặc chạy chưa xong, ghi đúng điều còn thiếu và không đánh dấu Baseline đã hoàn tất.

## Lịch thực hiện gợi ý và bàn giao

Đây là thứ tự theo phụ thuộc, không phải cam kết số giờ khi chưa chạy Julia/dataset.

| Phiên | Phạm vi | Bằng chứng cuối phiên |
| --- | --- | --- |
| 1 | Task 1 | Parser, minsup chính xác, test và fixture |
| 2 | Task 2–3 | Cây, weighted Nodeset, hai kernel đúng tính tay |
| 3 | Task 4 | 15 mẫu fixture và promotion đầy đủ |
| 4 | Task 5–6 | CLI dùng được, differential test pass |
| 5 | Task 7, phối hợp Hiếu/Tiến | Báo cáo đối chiếu và hướng dẫn bàn giao |

Hiếu có thể chuẩn bị SPMF/manifest ngay từ đầu; Tiến dùng contract sau Task 5. Các bước cài lõi của Đăng thực hiện tuần tự vì dùng chung invariant rank, bitmap và sibling.

## Definition of Done

- [x] `julia --project=. test/runtests.jl` pass, gồm fixture, bitmap >64, weighted count, promotion và random oracle.
- [x] CLI sinh đúng 15 mẫu/support trên toy, không duplicate, output đọc lại được và lỗi có exit code rõ.
- [x] `julia --project=. test/runtests.jl spmf` pass trên 5 CSDL full ở cấu hình được lưu; giữ riêng trạng thái test local với tích hợp ngoài.
- [x] README có môi trường Julia cụ thể, lệnh chạy/test, kết quả cuối và quy ước minsup.
- [x] Notes giải thích được khác biệt Nodeset/NegNodeset, promotion, số lần xuất mẫu và ánh xạ sang paper.
- [x] Cách đo đã ghi rõ; peak RSS và runtime sau warm-up thuộc harness của Hiếu, không suy ra từ allocation của Julia hay timing cold CLI.
- [x] Baseline được giữ làm đối chứng cho lần tối ưu tiếp theo; không đặt tên optimized cho mã chưa có cải tiến đo được.

## Nguồn đối chiếu kỹ thuật

- [Paper negFIN, DOI](https://doi.org/10.1016/j.eswa.2018.03.041), bản local trong mục Spec; dùng định nghĩa và giả mã, không dùng source cài đặt.
- [SPMF NegFIN: CLI, format và ví dụ](https://www.philippe-fournier-viger.com/spmf/NegFIN.php).
- [Julia: arbitrary-precision arithmetic](https://docs.julialang.org/en/v1/manual/integers-and-floating-point-numbers/#Arbitrary-Precision-Arithmetic).
- [Julia Test](https://docs.julialang.org/en/v1/stdlib/Test/).
- [Đề bài môn học](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/itemset/).

## Rà soát kế hoạch trước khi bàn giao

- [x] Phủ phạm vi Baseline: I/O, CLI, thuật toán, kiểm thử, đối chiếu và tài liệu.
- [x] Mỗi task có file, API, test và gate; setup gắn Task 1, tài liệu gắn task cần nó.
- [x] Các task dùng cùng rank 1-based, BigInt, support số đếm và callback; Task 3 phân biệt NegNodeset(Q) với NegNodeset(P).
- [x] Năm Review Focus có test ở task sở hữu; không để collector che duplicate.
- [x] Có giới hạn output, bitmap >64, ngưỡng chính xác và startup/compilation; không hứa cải thiện chưa đo.
- [x] Không chạy implementation/test trong lượt lập kế hoạch; các ô execution vẫn để trống.
