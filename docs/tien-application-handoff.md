# Bàn giao cho Tiến — hai ứng dụng và Colab

**Mục tiêu:** Thực hiện hai ứng dụng bằng negFIN của nhóm, chuẩn bị demo Colab chạy lại được và viết Chương 3. Đề yêu cầu mỗi ứng dụng chọn một trong hai hướng: **giỏ hàng hoặc log**, và **sinh học hoặc mẫu trực quan trên ảnh**. Chi tiết, thang điểm và yêu cầu nộp bài: [đề đồ án](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/itemset/).

**Tình trạng:** Baseline/CLI đã có trên `main`; Optimized, hai ứng dụng và notebook vẫn đang thực hiện. Tiến có thể bắt đầu bằng Baseline, không cần chờ Optimized. Các bộ dữ liệu dưới đây là **đề xuất để nhóm chốt**, không phải lựa chọn đã được Tiến xác nhận.

## 1. Chuẩn bị môi trường và làm quen giao diện

- [ ] Cài Julia >= 1.9; clone repo, tạo nhánh `feature/<ten-cong-viec>` từ `origin/main` theo [AGENTS.md](../AGENTS.md). Không commit trực tiếp lên `main`.
- [ ] Chạy suite `julia --startup-file=no --project=. test/runtests.jl` và ví dụ:

```text
julia --startup-file=no --project=. run.jl --input data/toy/example.txt --output results/toy.txt --minsup 0.4 --variant baseline --stats results/toy.stats.toml
```

Toy có 5 giao dịch và 15 itemset. Đối chiếu `results/toy.txt` với `data/toy/example.expected.txt` theo nội dung itemset/support, không phụ thuộc thứ tự dòng.

- [ ] Đọc [baseline-contract.md](baseline-contract.md): input mỗi dòng là một giao dịch gồm ID nguyên dương; output có dạng `1 3 #SUP: 2`; support là **số giao dịch**, minsup là tỷ lệ thập phân trong `(0,1]`.
- [ ] Chuẩn bị bảng ánh xạ ID ↔ ý nghĩa item và giữ mapping cùng phiên bản dữ liệu. Input, output, stats phải là các file khác nhau.

## 2. Ứng dụng 1 — chọn giỏ hàng hoặc log

### Đề xuất: giỏ hàng với Online Retail

Nguồn gợi ý: [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail). Dữ liệu có `InvoiceNo`, `StockCode`, `Description`, `Quantity`; mỗi hóa đơn có thể chuyển thành một giao dịch gồm các sản phẩm khác nhau. Chọn và giải thích chính sách cho hóa đơn hủy/trả hàng, dòng không phải sản phẩm, dữ liệu thiếu và sản phẩm trùng; ghi số dòng/hóa đơn trước và sau lọc. `StockCode` có thể chứa chữ nên cần ánh xạ ổn định sang ID nguyên dương.

- [ ] Lấy dữ liệu từ nguồn công khai có quyền sử dụng; ghi URL, phiên bản/ngày tải, checksum và quy tắc tiền xử lý. Chốt nguồn với nhóm trước khi dùng trong báo cáo.
- [ ] Viết pipeline tái lập: dữ liệu gốc → giao dịch SPMF + mapping ID/tên sản phẩm; đặt các quyết định lọc trong mã và tài liệu. Các đường dẫn/thư mục cụ thể có thể thống nhất qua PR.
- [ ] Chạy negFIN của nhóm ở `minsup` hợp lý; xuất và diễn giải frequent itemset theo tên sản phẩm. Lưu số giao dịch, ngưỡng và số mẫu.
- [ ] Sinh luật `X → Y` từ itemset bằng bước hậu xử lý do nhóm xây dựng; yêu cầu `X` và `Y` không rỗng, rời nhau. Dùng `support(X ∪ Y) / N`, `confidence = support_count(X ∪ Y) / support_count(X)` và `lift = confidence / (support_count(Y) / N)`; lọc theo minsup/minconf.
- [ ] Trình bày top 10 luật theo lift, kèm support, confidence, lift và ý nghĩa kinh doanh; nêu rõ giới hạn dữ liệu và ngưỡng lựa chọn. Kiểm tra phép tính bằng một ví dụ nhỏ tính tay; không dùng kết quả FIM từ thư viện có sẵn thay cho negFIN của nhóm.

Nếu Tiến chọn **log** thay giỏ hàng: trước khi xử lý, chốt nguồn log và định nghĩa transaction (ví dụ theo phiên hoặc cửa sổ thời gian), ánh xạ sự kiện, các mẫu cần tìm và cách diễn giải khả năng phát hiện lỗi/bất thường.

## 3. Ứng dụng 2 — chọn sinh học hoặc hình ảnh

### Đề xuất: DNA splice-junction

Nguồn gợi ý: [UCI Splice-junction Gene Sequences](https://archive.ics.uci.edu/dataset/69/molecular-biology-splice-junction-gene-sequences), gồm 3.190 chuỗi DNA, mỗi chuỗi 60 vị trí. Có thể mã hóa mỗi chuỗi thành transaction của các item `vị trí–base` hoặc k-mer theo vị trí, rồi khảo sát pattern giữa các nhóm. Chốt cách xử lý base mơ hồ và ý nghĩa vị trí theo tài liệu nguồn.

- [ ] Chốt hướng và nguồn dữ liệu, ghi giấy phép/trích dẫn, checksum và đặc điểm mẫu. Nếu chọn nguồn khác, bảo đảm dữ liệu phù hợp genome/protein sequence hoặc yêu cầu hướng ảnh của đề.
- [ ] Viết pipeline dữ liệu gốc → transaction SPMF + bảng giải mã. Với k-mer không kèm vị trí, giải thích rõ mất thứ tự và số lần xuất hiện vì itemset là tập hợp; tránh diễn giải quá mức.
- [ ] Chạy negFIN của nhóm; trình bày pattern tiêu biểu, support và ý nghĩa sinh học có căn cứ. Nếu so các lớp, ghi rõ mẫu số và cách phân nhóm; không gắn ý nghĩa sinh học chưa kiểm chứng.

Nếu chọn **hình ảnh**: xác định dataset, cách trích xuất visual words và tạo một transaction cho mỗi ảnh; lưu seed, tham số, mapping và giải thích các pattern trực quan. Không xem Mushroom dạng bảng benchmark là dữ liệu genome/protein sequence.

## 4. Notebook Colab và Chương 3

- [ ] Phối hợp nhóm tạo `notebooks/demo.ipynb`: cài Julia tương thích trong Colab, lấy source và dữ liệu công khai, chạy pipeline chuẩn bị dữ liệu, CLI negFIN và cả hai ứng dụng. Không phụ thuộc `.tools/`, file local hay tài khoản riêng.
- [ ] Mỗi bước có lệnh rõ ràng; kiểm tra checksum khi có snapshot cố định, cố định seed nếu dùng ngẫu nhiên, lưu mapping và các tham số `minsup`/`minconf`. Đảm bảo notebook gọi đúng implementation của nhóm.
- [ ] Chạy **Run all trong môi trường Colab mới**, ghi commit, nguồn dữ liệu và kết quả; tạo link public và bổ sung vào README. Phối hợp Hiếu về nguồn benchmark, Đăng về CLI/thuật toán.
- [ ] Viết Chương 3 tiếng Việt: mục tiêu, dữ liệu và quyền sử dụng, cách tạo transaction, tham số, kết quả thực tế, diễn giải và giới hạn cho cả hai ứng dụng. Phối hợp tổng hợp báo cáo IEEE của nhóm theo đề.

## 5. Bàn giao lại cho nhóm

- [ ] PR chứa mã chuẩn bị, mapping/schema hoặc cách tái tạo mapping, lệnh chạy, test phù hợp, notebook và hướng dẫn; không commit dữ liệu lớn, runtime hay output sinh tự động.
- [ ] Cung cấp link dữ liệu công khai, checksum, commit, log/output mẫu, kết quả hai ứng dụng và link Colab. Nếu kết quả lớn, chia sẻ riêng và ghi nơi lưu cùng hướng dẫn tái lập.
- [ ] Đăng hỗ trợ CLI, support/ngưỡng và lỗi negFIN; Hiếu hỗ trợ đo đạc, checksum và tái lập. Nêu rõ các quyết định cần nhóm chốt, khó khăn và phần chưa hoàn thành trong PR.

**Mốc bàn giao đầu tiên:** chọn hai hướng và dữ liệu, đề xuất cách tạo transaction + mapping, rồi chạy một ví dụ nhỏ bằng Baseline trước khi chạy toàn bộ dữ liệu.
