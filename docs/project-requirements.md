# Yêu cầu đồ án CSC14004 — Nhóm 4

Nguồn: [đề FIM chính thức](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/itemset/), đối chiếu ngày 12/11/2026.

## Lựa chọn đã xác nhận

- Thuật toán negFIN, cài bằng Julia >= 1.9; giảng viên đã chấp thuận theo xác nhận của Đăng.
- Baseline dùng bitmap BigInt, giữ đầy đủ NegNodeset và promotion pruning. Chỉ chọn biểu diễn tối ưu thay thế sau khi đo.
- Đăng phụ trách thuật toán, CLI/I/O, tối ưu và Chương 1; Hiếu phụ trách kiểm thử, benchmark và Chương 2; Tiến phụ trách pipeline hai ứng dụng, Chương 3 và tổng hợp báo cáo.
- Repo đích: https://github.com/DankDaPancake/CSC14004-group4-negfin.

## Yêu cầu kỹ thuật

- Tự cài từ paper; SPMF dùng để tham chiếu kết quả, không sao chép source cài đặt có sẵn.
- Xuất frequent itemset và support; CLI nhận minsup, đường dẫn input/output chuẩn SPMF .txt.
- Unit test tự động trên ít nhất 5 CSDL; benchmark ít nhất 4 tập, tối ưu có số liệu so với Baseline.
- Thực nghiệm runtime theo minsup, output size, peak RAM, scalability và độ dài giao dịch khi phù hợp; giải thích kết quả và đề xuất ít nhất 2 hướng cải tiến.
- Kết quả tái lập được, seed cố định khi có ngẫu nhiên; lệnh test dùng `julia --project=. test/runtests.jl`.

## Nộp bài

- Một public GitHub repo với lịch sử commit minh bạch; link repo nộp trên Moodle.
- README có thông tin thành viên, môi trường, hướng dẫn chạy, ví dụ, output test và link demo Colab công khai.
- Notebook `notebooks/demo.ipynb` chạy sạch trên Colab; kernel Python có thể cài Julia và gọi Julia qua shell.
- Báo cáo tiếng Việt, IEEE conference 10–15 trang không kể tham khảo/phụ lục, đặt tại `docs/Report.pdf`; có paper gốc và ít nhất 3 tài liệu liên quan khác.
- Dữ liệu benchmark lớn có link Hugging Face/Kaggle công khai; mã chuẩn bị dữ liệu được notebook chứa hoặc import từ repo.
- Không có yêu cầu Jupyter Book trong trang đề FIM đã kiểm tra; dùng một repo chứa source, notebook và báo cáo.
- Hai ứng dụng: một hướng giỏ hàng/log và một hướng sinh học/hình ảnh; kết quả dùng cài đặt của nhóm.

## Trạng thái Baseline

Đã có source, CLI và kiểm chứng trong [README](../README.md), [contract](baseline-contract.md), [ghi chú thuật toán](negfin-baseline-notes.md) và [bằng chứng correctness](validation/correctness.toml). Colab, Report.pdf, Optimized và benchmark/ứng dụng đầy đủ được bổ sung theo giai đoạn; chưa coi push repo là hoàn tất đồ án.

Paper: Aryabarzan, Minaei-Bidgoli, Teshnehlab (2018), *negFIN: An efficient algorithm for fast mining frequent itemsets*, [DOI](https://doi.org/10.1016/j.eswa.2018.03.041), [PDF nguồn](https://www.philippe-fournier-viger.com/spmf/NEGFINarticle.pdf).
