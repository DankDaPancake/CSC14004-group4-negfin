# Bàn giao bài nộp CSC14004 — Nhóm 4

Bản bàn giao dựa trên `main` tại `ee6364c`. Báo cáo IEEE, hai notebook và bằng chứng chạy Colab đã merge. Người chốt bài cần kiểm tra nguồn benchmark và các liên kết công khai trước khi nộp.

## Sản phẩm đã có

| Sản phẩm | Vị trí và kết quả |
|---|---|
| Báo cáo IEEE | [Report.pdf](Report.pdf), 12 trang, phần tài liệu tham khảo bắt đầu ở trang 12. Có đủ ba chương, benchmark Julia–SPMF, scalability và pilot độ dài giao dịch. |
| Mã nguồn | [negFIN Julia](../src/NegFIN.jl) và [CLI](../run.jl), gồm Baseline và Optimized. |
| Demo local | [demo_local.ipynb](../notebooks/demo_local.ipynb) đã chạy trên Windows với Julia 1.12.0. |
| Demo Colab | [demo_colab.ipynb](../notebooks/demo_colab.ipynb) đã chạy đến cell cuối trên commit `1ff1cfa390248cdd3481f19fffc340c13cefc814`, Julia 1.12.6, variant `baseline`. |

Output mặc định của hai ứng dụng khớp giữa local và Colab. Online Retail có 19.773 giao dịch, 2.026 itemset và 962 luật tại minsup 0,01 và minconf 0,5. Splice-junction ở minsup 0,3 có lần lượt 280, 331 và 0 itemset ở các lớp EI, IE và N. Kiểm tra toy kỳ vọng 15 itemset. [Hướng dẫn chạy và link Colab](../README.md#hai-ứng-dụng-và-demo-colab)

## Dữ liệu và bằng chứng cần giữ

- **Đầu vào benchmark** gồm năm snapshot Chess, Mushroom, Retail, Accidents và T10I4D100K. Lấy đúng tên file, URL và SHA-256 theo [manifest benchmark](../data/benchmark/manifest.toml). Chess và Accidents có mirror FIMI từng được xác minh. Ba snapshot còn lại dùng URL SPMF trong manifest.
- **Đầu vào ứng dụng** do notebook tải từ UCI và kiểm SHA-256 theo [manifest ứng dụng](../data/applications/manifest.toml).
- **Bằng chứng benchmark** gồm hai gói của Hiếu cho Baseline–Optimized và SPMF–Julia. Giữ riêng các gói số liệu, cấu hình, log và biểu đồ. Dùng manifest để tải lại đầu vào. [Hồ sơ benchmark](validation/benchmark-handoff.md)

## Checklist trước khi nộp

1. **Hiếu hoặc người kiểm tra dữ liệu** tải mới năm snapshot benchmark và đối chiếu SHA-256. Xác nhận URL mở được khi chưa đăng nhập. TA đã cho phép dùng FIMI nếu nguồn hoạt động khi chấm. Ghi rõ các snapshot tải từ SPMF và xác nhận với TA nếu cần làm rõ yêu cầu lưu trữ.
2. **Đăng hoặc người chốt repo** kiểm tra commit cuối, chạy `julia --startup-file=no --project=. test/runtests.jl` và lưu kết quả trong README. Nếu có thay đổi ảnh hưởng pipeline, chạy lại cả hai notebook từ đầu và ghi commit, runtime, kết quả.
3. **Người nộp bài** mở link repo, PDF, demo Colab và dữ liệu từ phiên chưa đăng nhập. Kiểm tra bản PDF trên `main` là bản có đủ benchmark và thông tin tác giả. Nộp một link repo GitHub công khai trên Moodle.

Theo dõi thứ tự và trạng thái tại [kế hoạch nộp bài](superpowers/plans/2026-11-26-submission-checklist.md).
