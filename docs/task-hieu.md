# Task của Hiếu — bổ sung thực nghiệm SPMF và chốt Chương 2

Benchmark Baseline–Optimized trên năm tập đã hoàn tất và phần tổng hợp đã merge. Việc ưu tiên là bổ sung đường runtime SPMF mà [đề đồ án](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/itemset/) yêu cầu, sau đó bàn giao số liệu và hình cuối cho Tiến.

## Đo và đối chiếu

- [ ] Cập nhật `main`, ghi commit, máy, hệ điều hành, phiên bản Julia/Java/SPMF, số luồng, checksum jar và dữ liệu. Dùng các mức `[selected]` trong [cấu hình đã đo](../bench/config-baseline-20261119.toml), bảy mức minsup mỗi tập.
- [ ] Chạy thử SPMF NegFIN và negFIN Julia ở một vài điểm trước để xác nhận ngưỡng tuyệt đối, đầu ra và ước lượng thời gian. Kiểm tra số mẫu và support của các điểm ghép cặp. Ghi và điều tra mọi sai lệch về minsup hoặc output trước khi đưa điểm đo vào đồ thị.
- [ ] Đo SPMF và variant Julia được dùng làm đường so sánh trên cùng máy, cùng input và minsup. Ưu tiên ít nhất ba lần cold cho mỗi điểm và dùng wall time của toàn process, gồm khởi động, đọc và ghi. Dùng lại số Julia cũ khi môi trường và phạm vi đo tương đương, ghi rõ nguồn của từng đường. Lưu log của các lượt timeout, vượt giới hạn hoặc lỗi.
- [ ] Xác minh link Hugging Face hoặc Kaggle công khai cho dữ liệu lớn cần nộp, đối chiếu SHA-256 với manifest. Ghi rõ snapshot nào còn thiếu nguồn phù hợp.

## Chốt và bàn giao

- [ ] Vẽ runtime theo minsup với đường SPMF và Julia trên cùng hình cho từng tập. Hoàn thiện hình số itemset theo minsup, peak RSS tại minsup trung bình và scalability. Ghi đơn vị, số lần lặp và median, kèm khoảng min–max nếu phù hợp.
- [ ] Cập nhật [Chương 2](report/chapter2.md) dựa trên [kết quả benchmark đã xác minh](validation/benchmark-baseline-optimized-results.md). Phân tích xu hướng theo nhóm dữ liệu dày/thưa và kích thước đầu ra. Giữ phần trade-off RSS ở T10I4D100K và cùng Đăng chốt hai hướng tối ưu tiếp. Cùng Đăng quyết định phạm vi phép đo độ dài giao dịch theo yêu cầu có điều kiện của đề.
- [ ] Gửi Tiến bảng/hình có caption và bản Chương 2 cuối để ghép báo cáo. Tạo PR cho tài liệu, hình và script tái lập nếu có thay đổi. Chia sẻ riêng gói raw có SHA-256 gồm số đo từng lượt, config, môi trường, log và lệnh chạy. Giữ dataset lớn và đầu ra thô ngoài Git.

**Bàn giao cho nhóm** gồm PR, kết quả từng điểm chạy, hình chèn báo cáo và danh sách cấu hình chưa có kết quả hợp lệ. Số liệu chính có thể đo trên máy benchmark của Hiếu và đi kèm môi trường tái lập.
