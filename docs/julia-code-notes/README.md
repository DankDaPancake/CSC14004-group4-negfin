# Đọc mã negFIN qua Julia, giả mã và Python

Đọc theo luồng từ tệp giao dịch đến từng dòng itemset và support. Các đoạn Python minh họa cùng thao tác bằng thư viện chuẩn. Mã chạy đồ án nằm ở Julia trong `src/`.

| Phần | Mã Julia | Giả mã và Python |
|---|---|---|
| Nhận tham số, đọc tệp, tính ngưỡng và chuẩn bị rank | [cli.jl](../../src/cli.jl), [io.jl](../../src/io.jl), [prepare.jl](../../src/prepare.jl) | [01 — Đầu vào và rank](01-input-and-ranks.md) |
| Dựng BMC-tree, gom Nodeset và tính phần support bị mất | [bmc_tree.jl](../../src/bmc_tree.jl), [negnodesets.jl](../../src/negnodesets.jl) | [02 — BMC và NegNodeset](02-bmc-and-negnodesets.md) |
| Duyệt DFS, promotion, xuất mẫu và thay biểu diễn bitmap | [mine.jl](../../src/mine.jl), [optimized.jl](../../src/optimized.jl) | [03 — Duyệt và tối ưu](03-search-and-optimization.md) |

`run.jl` gọi CLI trong module [NegFIN](../../src/NegFIN.jl). CLI chọn `mine_baseline` hoặc `mine_optimized` và truyền một callback để ghi từng mẫu. Cả hai nhận cùng kiểu đầu vào và trả `MiningSummary`; nội dung itemset đi qua callback.

BMC-tree và NegNodeset bám theo Algorithm 1, Algorithms 3–4 và Properties 7–8 của bài báo gốc. Giả mã trong bộ ghi chú phản ánh cách repo tổ chức các bước đó. [Bài báo negFIN](https://www.philippe-fournier-viger.com/spmf/NEGFINarticle.pdf)

Khi đọc ví dụ, cần phân biệt **ID gốc** (nhãn trong tệp), **rank** (thứ tự khai thác bắt đầu từ 1), **bit** (vị trí bắt đầu từ 0) và **count của node** (số giao dịch dùng chung một tiền tố). [Dữ liệu toy](../../data/toy/example.txt) có 5 giao dịch và [kết quả chuẩn](../../data/toy/example.expected.txt) có 15 mẫu ở ngưỡng 0,4.
