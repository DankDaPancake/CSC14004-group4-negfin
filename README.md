# CSC14004-group4-negfin

Repository: https://github.com/DankDaPancake/CSC14004-group4-negfin

```text
git clone https://github.com/DankDaPancake/CSC14004-group4-negfin.git
cd CSC14004-group4-negfin
```

Đồ án FIM: tự cài negFIN bằng Julia từ paper Aryabarzan et al. (2018), [DOI](https://doi.org/10.1016/j.eswa.2018.03.041). Thầy đã chấp thuận thuật toán theo xác nhận của Đăng. Thành viên: Đăng (thuật toán), Hiếu (kiểm thử/benchmark), Tiến (ứng dụng).

## Môi trường

Julia >= 1.9; đang kiểm chứng bằng Julia 1.12.0 trên Windows x64. Chỉ dùng Base và thư viện chuẩn, không có thư viện FIM hoặc package bên thứ ba. Không cần tải registry/package để chạy bộ test local. Đặt Julia trong PATH hoặc dùng đường dẫn đầy đủ đến julia.exe.

## Chạy

```text
julia --project=. test/runtests.jl
julia --project=. run.jl --input data/toy/example.txt --output results/toy.txt --minsup 0.4 --variant baseline --stats results/toy.stats.toml
```

Ví dụ có 5 giao dịch, min_count=2; đầu ra kỳ vọng là 15 mẫu trong `data/toy/example.expected.txt`. Chưa có bản Optimized.

- [Quy ước CLI/I/O và phạm vi đo](docs/baseline-contract.md)
- [Yêu cầu và phạm vi đồ án](docs/project-requirements.md)
- [Giải thích cấu trúc dữ liệu và promotion](docs/negfin-baseline-notes.md)
- [Kế hoạch triển khai](docs/superpowers/plans/2026-11-12-negfin-baseline.md)

## Kiểm chứng Baseline

Đã chạy trên Windows x64 bằng Julia 1.12.0, SPMF 2.67a và Temurin Java 25.0.5. SPMF jar hiện dùng cần Java 25; Java 21 không chạy được jar này. Java chỉ cần cho test tham chiếu, không cần để chạy thuật toán Julia.

Bộ test local đã qua 1.120 assertion trên Windows: I/O 27, BMC-tree 21, NegNodeset 10, mining/promotion 18, CLI 32, differential 1.004, parser tham chiếu 8. Differential dùng seed 20261112, 50 CSDL nhỏ với 4 ngưỡng và các phép hoán vị/đổi ID, đối chiếu oracle vét cạn độc lập. CLI có regression cho alias hoa/thường của output/stats chưa tồn tại trên Windows.

Đối chiếu SPMF trên **5 file đầy đủ**, cùng input/minsup, đã qua 35 assertion. Cả 5 file đều có missing=0, extra=0, support_mismatch=0. Manifest ghi ngưỡng và SHA256; [báo cáo máy đọc được](docs/validation/correctness.toml) giữ số giao dịch và số mẫu thực tế.

Lưu ý nguồn dữ liệu: snapshot `mushrooms.txt` tải từ SPMF có **8.416 giao dịch**, khác con số 8.124 trong bảng minh họa của đề. Nhóm không chỉnh dữ liệu để ép khớp con số mô tả; checksum trong manifest xác định chính xác bản đã kiểm chứng.

Đây là kiểm tra correctness tại một ngưỡng mỗi file, không thay cho benchmark 5–7 mức minsup, peak RAM, scalability hoặc chứng minh tăng tốc. Thời gian trong báo cáo correctness có phạm vi khác nhau giữa Julia và Java nên không dùng để kết luận bên nào nhanh hơn.

## Tái lập đối chiếu SPMF

File benchmark và jar không commit vào repo. Nguồn file nằm trong [manifest](data/benchmark/manifest.toml); tải về đúng tên ở `data/benchmark/`:

```powershell
curl.exe --fail -L https://www.philippe-fournier-viger.com/spmf/publicdatasets/chess.txt -o data/benchmark/chess.txt
curl.exe --fail -L https://www.philippe-fournier-viger.com/spmf/publicdatasets/mushrooms.txt -o data/benchmark/mushrooms.txt
curl.exe --fail -L https://www.philippe-fournier-viger.com/spmf/publicdatasets/retail.txt -o data/benchmark/retail.txt
curl.exe --fail -L https://www.philippe-fournier-viger.com/spmf/publicdatasets/accidents.txt -o data/benchmark/accidents.txt
curl.exe --fail -L https://www.philippe-fournier-viger.com/spmf/publicdatasets/T10I4D100K.txt -o data/benchmark/T10I4D100K.txt
```

Tải jar từ [SPMF](https://www.philippe-fournier-viger.com/spmf/download.php), chuẩn bị Java tương thích rồi thiết lập đường dẫn thật của máy:

```powershell
$env:SPMF_JAR = 'C:\tools\spmf.jar'
$env:JAVA_EXE = 'C:\tools\java\bin\java.exe'
$env:FIM_BENCHMARK_MANIFEST = (Resolve-Path 'data/benchmark/manifest.toml').Path
julia --project=. test/runtests.jl spmf
```

`JAVA_EXE` có thể bỏ nếu `java` đã có trong PATH. Nhóm `spmf` là opt-in; thiếu runtime, file hoặc checksum không khớp sẽ FAIL, không im lặng skip. Kết quả mới ghi ở `results/correctness.toml`, output và log ở `results/spmf/`. Chess và Accidents có bản giống hệt checksum ở kho FIMI (`mirror_url` trong manifest); chưa có bản Hugging Face/Kaggle khớp, xem [benchmark-baseline.md](docs/validation/benchmark-baseline.md#nguồn-dữ-liệu-công-khai).

Output cuối của lần chạy kiểm chứng:

```text
SPMF input and exact thresholds                     27/27
BMC tree and weighted singleton Nodesets            21/21
NegNodeset filters and weighted support              10/10
Complete negFIN mining and promotion                18/18
CLI integration and output safety                   32/32
Independent exhaustive oracle and metamorphic     1004/1004
Reference parser and exact comparison                8/8
SPMF NegFIN correctness on full benchmark databases 35/35
```

## Benchmark Baseline

Harness trong `bench/`, cấu hình ở `bench/config.toml`; kết quả ghi vào `results/bench/<thời điểm>/` (không commit). Cần 5 file ở `data/benchmark/` đúng checksum như trên. Phạm vi đo, số liệu và nhận xét: [docs/validation/benchmark-baseline.md](docs/validation/benchmark-baseline.md).

```powershell
julia --startup-file=no --project=. bench/pilot.jl --dataset Chess        # chọn minsup: 1 lần cold mỗi mức
julia --startup-file=no --project=. bench/run.jl --scope warm --dataset Chess
julia --startup-file=no --project=. bench/run.jl --scope cold --dataset Chess
julia --startup-file=no --project=. bench/run.jl --scope scalability --dataset Accidents
julia --startup-file=no --project=. bench/run.jl --all                     # mọi tập trong [selected] + scalability
```

`--stats` của CLI có thêm `[phases]` và hai bộ đếm; xem [contract](docs/baseline-contract.md#đo-lường).

## Các sản phẩm còn lại của nhóm

Demo Colab công khai, 2 ứng dụng, bản Optimized và `docs/Report.pdf` được bổ sung ở các giai đoạn tương ứng. Repo hiện chưa có các sản phẩm này.
