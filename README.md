# group04-fim-negfin

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
- [Giải thích cấu trúc dữ liệu và promotion](docs/negfin-baseline-notes.md)
- [Kế hoạch triển khai](docs/superpowers/plans/2026-11-12-negfin-baseline.md)

## Trạng thái kiểm chứng

Xem các kết quả chạy thực tế được cập nhật sau khi hoàn tất differential test và đối chiếu SPMF. Không coi các bước kiểm chứng còn chờ là đã pass.

## Các sản phẩm còn lại của nhóm

Demo Colab công khai, 2 ứng dụng, benchmark đầy đủ, bản Optimized và `docs/Report.pdf` được bổ sung ở các giai đoạn tương ứng. Repo hiện chưa có các sản phẩm này.
