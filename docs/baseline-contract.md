# Giao diện negFIN Baseline

## Chạy và gọi API

```text
julia --project=. run.jl --input data/toy/example.txt --output results/toy.txt --minsup 0.4 --variant baseline --stats results/toy.stats.toml
julia --project=. test/runtests.jl
```

`--input`, `--output`, `--minsup` bắt buộc. `--variant` mặc định `baseline`, hiện chưa có `optimized`. `--stats` tùy chọn.

```julia
include("src/NegFIN.jl")
using .NegFIN
db = open(read_spmf, "data/toy/example.txt")
summary = mine_baseline(db, parse_minsup("0.4");
    emit=(items, support) -> println(items, " => ", support))
```

`items` là vector ID gốc tăng dần, có thể giữ lại an toàn; `support` là số giao dịch. API tự copy/normalize giao dịch; giữ riêng các giao dịch giống nhau. File giao dịch chỉ có metadata được xem là DB rỗng; API cũng nhận giao dịch rỗng và vẫn tính chúng vào mẫu số N.

## Input và minsup

Mỗi dòng dữ liệu là một giao dịch gồm số nguyên dương, cách nhau bằng whitespace. Item trùng trong cùng giao dịch được loại; thứ tự đầu vào không ảnh hưởng kết quả. Bỏ dòng trắng và dòng có ký tự đầu sau strip là `#`, `%`, `@`; hỗ trợ BOM đầu file. Token sai hoặc ngoài Int báo số dòng và thoát 2.

Minsup là chuỗi thập phân trong (0,1], ví dụ `0.4`, `0.07`, `1.0`. Chưa nhận `40%`, `4e-1` hoặc `.4`. Min_count = ceil(minsup*N) bằng phân số BigInt chính xác, không làm tròn qua Float64. 0.07 trên 100 giao dịch cho ngưỡng 7; 0.401 trên 5 giao dịch cho ngưỡng 3.

## Output và lỗi

Mỗi dòng: `1 3 #SUP: 2`. Không có empty itemset hoặc metadata/log lẫn trong file kết quả. Item trong dòng tăng dần; thứ tự các dòng phụ thuộc duyệt tìm kiếm, không dùng thứ tự dòng để kiểm tra correctness.

Mã thoát: 0 thành công hoặc help; 2 tham số/input không hợp lệ; 1 lỗi chạy/ghi file. stderr chứa lỗi. Input, output và stats phải là các file khác nhau, kể cả alias symlink/hardlink. Trên Windows, đường dẫn canonical chỉ khác hoa/thường bị từ chối bảo thủ ngay cả khi file/thư mục cha chưa tồn tại, tránh stats ghi đè output. Output được ghi vào file tạm cùng thư mục và rename sau khi khai thác thành công, giữ kết quả cũ nếu khai thác/ghi tạm thất bại. Output và stats là hai file xuất riêng; nếu ghi stats thất bại, process báo lỗi 1 dù output có thể đã hoàn chỉnh.

## Đo lường

Stats TOML chứa số giao dịch, số frequent item, min_count và số mẫu. `read_seconds` đo đọc input; `mine_write_seconds` gồm normalize/prepare, xây cây, Nodeset, khai thác, ghi và rename output. `total_seconds` đo từ đầu main đến lúc output hoàn tất, trước khi ghi stats; không gồm startup/load module trước main. Lần gọi đầu có thể bao gồm JIT ở các phần được đo.

Các số trên không phải peak RAM hoặc pure mining time. Hiếu đo wall-clock toàn process/peak RSS bằng harness ngoài; benchmark sau warm-up cần gọi API trong cùng process và mô tả rõ phạm vi đo.

## Colab và bàn giao

Notebook Python có thể cài Julia rồi gọi cùng CLI qua shell, không cần viết lại negFIN trong Python. Tiến lưu ánh xạ ID -> ý nghĩa item ngoài file transaction để diễn giải. Sinh luật, confidence/lift và hai ứng dụng nằm ngoài module Baseline.
