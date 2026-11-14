# Profiling thăm dò Baseline — 14/11/2026

**Phạm vi:** một lượt không profiler và một lượt profiler CPU cho mỗi cấu hình, trên Julia 1.12.0, một thread, Windows, i7-11800H, RAM 16,9 GB; source `src/` tương ứng commit `af39d5e`, `main` gốc `eee35e0`. Các thay đổi chưa commit tại thời điểm đo chỉ nằm trong tài liệu/script đồ thị. Đây là máy khác máy benchmark của Hiếu, không dùng số thời gian để so sánh hiệu năng giữa hai máy.

Script `profile-baseline-pilot.jl` đọc dataset trước khi đo, warm-up trên toy, gọi `mine_baseline` không phase hook, callback đếm và tính fingerprint; không format/ghi output, không tính thời gian đọc input. CPU profiler lấy mẫu `Profile.@profile`, xuất flat với `C=false`, nên phần native không có attribution chi tiết. Mỗi cấu hình chỉ một cặp liên tiếp, không có CI hay ước lượng độ ổn định.

| Dataset | minsup | Mẫu | Không profiler (s) | Có profiler (s) | CPU snapshots |
|---|---:|---:|---:|---:|---:|
| Retail | 0,002 | 2.691 | 20,174 | 21,946 | 11.214 |
| Retail | 0,001 | 7.589 | 55,039 | 56,460 | 28.663 |
| Chess | 0,45 | 2.832.777 | 3,705 | 3,883 | 1.937 |
| Chess | 0,3 | 37.282.962 | 41,852 | 43,453 | 22.235 |
| Accidents | 0,45 | 16.123 | 6,122 | 6,273 | 3.105 |

Đây không phải ước lượng overhead có độ tin cậy: cặp không random hóa, chạy một lần. Số mẫu bằng benchmark, số mẫu và XOR fingerprint của cặp trong cùng process trùng nhau; fingerprint có thể va chạm, **không thay cho đối chiếu chính xác từng itemset/support**.

- Retail: trong bảng flat, `negative_pair` xuất hiện trên stack ở 10.718 mẫu; wrapper `BigInt &` ở 8.025 mẫu. Đây là số frame inclusive có thể chồng lấp, không được cộng hoặc quy đổi trực tiếp thành tỷ lệ thời gian của các hàm độc lập.
- Retail 0,001: `negative_pair` xuất hiện trên stack ở 27.573 mẫu và `BigInt &` ở 20.554 mẫu; hai dòng có thể chồng lấp. Số mẫu và fingerprint giữa hai lượt trùng nhau.
- Chess: `emit_family!` xuất hiện trên stack ở 1.295 mẫu. Callback fingerprint tạo tuple và hash mỗi mẫu, có thể đóng góp đáng kể; số này không ước lượng chi phí output CLI.
- Chess 0,3: `emit_family!` xuất hiện trên stack ở 17.444 mẫu, với cùng giới hạn về callback fingerprint và frame inclusive; số mẫu và fingerprint của hai lượt trùng nhau.
- Accidents: `negative_pair` xuất hiện ở 1.166 mẫu, các dòng `build_bmc` cũng xuất hiện trong profile. Profile bao gồm normalize/prepare/build và mine, không chỉ mine.

## Cấp phát thăm dò

`profile-allocations-pilot.jl` dùng `Profile.Allocs` sample_rate 0,0001, một cặp mỗi cấu hình, cùng callback fingerprint. Retail 0,004 thu được 3.020 allocation events, trong đó 2.686 được báo type `BigInt`; Chess 0,45 thu được 4.403 events, trong đó 852 `BigInt`, 654 `Memory{Int64}` và 580 `Vector{Int64}`. Đây là **số sự kiện được lấy mẫu, không phải tổng số cấp phát hoặc peak RSS**, và các tuple/vector do callback fingerprint cũng có trong mẫu. Cấp phát native của GMP không nhất thiết được quy đầy đủ vào kích thước Julia object. Chưa kiểm tra độ biến thiên giữa các seed/lượt, nên chưa định lượng được phần tiết kiệm khả dĩ.

Một cặp chạy thêm có phân nhóm theo **frame project gần nhất**: Retail 0,004 có 2.599/2.929 event mẫu mang frame `negnodesets.jl:8`; Chess 0,45 có 2.025/4.344 mang `mine.jl:7` và 894 mang `negnodesets.jl:15`. Frame gần nhất chỉ xác định ngữ cảnh stack: nó cũng có thể bao gồm cấp phát từ thư viện hoặc callback, không chứng minh dòng đó tự cấp phát. Đặc biệt `mine.jl:7` gọi callback fingerprint tạo tuple/hash. Đây là hai mẫu mới, không cộng với các số type ở đoạn trước; vẫn cần lặp độc lập và đối chiếu với callback count thuần.

Hash input của Retail, Chess và Accidents khớp manifest bàn giao. Log, script chạy và fingerprint local nằm tại `results/profile-*.log` và `results/profile-*-pilot.jl`; `results/` không theo dõi bằng Git. Hai script cũng được lưu cạnh tài liệu này. Ví dụ từ checkout gốc (thay JULIA bằng đường dẫn Julia):

```powershell
julia --startup-file=no --project=. docs/validation/profile-baseline-pilot.jl . data/benchmark/retail.txt 0.002
julia --startup-file=no --project=. docs/validation/profile-allocations-pilot.jl . data/benchmark/retail.txt 0.004 0.0001
```

## Pilot ghi output

`profile-output-pilot.jl` chạy riêng callback `write_itemset` vào file tạm, không dùng callback fingerprint; thời gian đo bao gồm mining và ghi trong vòng `open`, không gồm đọc input, mở/đóng file hoặc tính SHA256. Trên Chess 0,55, không profiler là 1,050 s và có profiler là 1,217 s; cả hai tạo 574.998 mẫu, 19.045.853 byte và cùng SHA256 `314e8c74ce4fe2ad6d6bd2c0c742bbbc6081df54d8c411dcbb1f265d53376068`. `write_itemset` xuất hiện trong stack của 394/565 CPU snapshots; đây là số inclusive, không phải tỷ lệ thời gian ghi đĩa thuần. So khớp byte là so hai lượt cùng process và không thay thế oracle/SPMF.

Thời gian hai lượt dùng callback khác nhau, dataset/ngưỡng khác với pilot count, nên không trừ chúng để tính chi phí I/O. Log local: `results/profile-output-chess-055.log`. Tái chạy: `julia --startup-file=no --project=. docs/validation/profile-output-pilot.jl . data/benchmark/chess.txt 0.55`.

Đã chạy CLI Baseline và SPMF 2.67a với Chess 0,55; parser tham chiếu đối chiếu đủ **574.998 itemset**, missing=0, extra=0, support_mismatch=0. File CLI Baseline có SHA256 trùng hai file của pilot write ở trên; do đó cặp profiled/non-profiled của workload này cũng khớp SPMF qua file CLI, với giả định SHA256. Đây không phải kiểm chứng cho các cấu hình count khác.

Đối chiếu tương tự cho hai tập khác:

| Dataset | minsup | Itemset | SHA256 output CLI = cặp pilot write | SPMF missing/extra/support mismatch |
|---|---:|---:|---|---|
| Accidents | 0,45 | 16.123 | `0264e70e97ae643eebd85c0f69339344bba59749fe72eb34662a03ae1cc3c5b4` | 0/0/0 |
| Retail | 0,002 | 2.691 | `9c5f11fa348dbb14c8ffd6c1c479668274b4ae0b59d4fefab76128bdad81ecea` | 0/0/0 |

Lệnh SPMF: `java -Xmx2g -jar spmf.jar run NegFIN INPUT OUTPUT MINSUP`. Kết quả được chuẩn hóa và đối chiếu bằng `read_patterns`/`compare_patterns` trong `test/helpers/spmf.jl`. Các file output và log của từng pilot nằm trong `results/`, không được Git theo dõi. Không so thời gian Julia/SPMF vì phạm vi đo khác nhau.

## Diễn giải và bước kế tiếp

Ưu tiên thí nghiệm giảm chi phí lọc bitmap/NegNodeset trên tập thưa; kết quả này chỉ ủng hộ lựa chọn **giả thuyết**, chưa chứng minh thay bitmap sẽ nhanh hơn. Chess cần thí nghiệm riêng với count không hash và CLI ghi output để tách tác động callback, tạo vector và I/O. Lặp lại các workload để ước lượng độ biến thiên, thu stack cấp phát và đối chiếu kết quả với oracle/SPMF.
