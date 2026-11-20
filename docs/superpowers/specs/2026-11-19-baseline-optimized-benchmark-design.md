# Thiết kế: Benchmark Baseline và Optimized

## Mục đích
Tạo phép so sánh có thể kiểm toán giữa Baseline và Optimized trên cùng máy, cùng snapshot dữ liệu, minsup và phạm vi đo; cung cấp kết quả dùng được cho Chương 2 và gói bàn giao tái lập.

## Mục tiêu và ngoài phạm vi
- Xác minh `origin/main`, commit đo, Julia, cấu hình máy, manifest và SHA256 trước khi chạy.
- Chạy thử trên cấu hình nhỏ; xác nhận hai variant cho cùng kết quả chính xác và ước lượng runtime trước các lượt dài.
- Chạy warm, cold, peak RSS và output size trên 5 dataset; ghi rõ timeout, output cap và lỗi, không tính lượt chưa hoàn tất là số đo thành công.
- Đo scalability tại 10%, 25%, 50%, 75%, 100% trên cả 5 dataset theo lựa chọn của người dùng; đặc biệt theo dõi T10I4D100K vì peak RSS của Optimized tăng trong pilot.
- Tổng hợp bảng/biểu đồ/nhận xét Chương 2; bàn giao config, manifest/checksum, dữ liệu thô, logs, môi trường, lệnh và ZIP có SHA256.
- Không chuyển benchmark sang Colab; không ghép số liệu cũ khác máy thành phép so sánh trực tiếp; không commit dataset lớn hay output itemset.
- Không gửi liên lạc ra ngoài hoặc thay mặt phối hợp với Đăng; nội dung cần trao đổi sẽ được ghi thành ghi chú đề xuất.

## Các hướng đã cân nhắc
1. Chạy lại cả hai variant bằng harness hiện tại trên máy này — được chọn; công bằng và đáp ứng yêu cầu, tận dụng khả năng checksum, warm/cold, RSS, output cap và CSV có sẵn.
2. Ghép số liệu Baseline handoff với pilot Optimized rồi chỉ đo phần thiếu — không chọn vì khác máy/commit/phạm vi, không thể xem là so sánh trực tiếp.
3. Viết harness benchmark mới — không chọn vì làm tăng phạm vi và rủi ro; chỉ bổ sung tối thiểu nếu harness hiện tại không thể đo/đối chiếu đúng yêu cầu.

## Cách thực hiện dự kiến
- Tạo branch riêng từ `origin/main` mới nhất sau khi xác nhận trạng thái sạch.
- Kiểm tra năm file dữ liệu hiện có với manifest SHA256; xác định nguồn/snapshot nếu thiếu hoặc không khớp. Tạo config chạy riêng cho mỗi variant, với đúng cùng thông số và scalability fractions.
- Thực hiện pilot nhỏ và kiểm chứng tương đương output/pattern count. Dùng kết quả pilot để ước lượng wall time và xác định ngưỡng dừng, nhất là T10I4D100K. Không bắt đầu full run nếu checksum/correctness không qua.
- Chạy các lượt full theo cặp điều kiện giống nhau; giữ logs và trạng thái thất bại. Ghi rõ cold bao gồm startup/JIT/I/O, warm loại trừ chúng, RSS gồm runtime process, output size theo CLI. Không diễn giải tổng cấp phát như peak RAM.
- Tạo báo cáo/bảng/biểu đồ trong tài liệu Chương 2 và archive tái lập có SHA256. Không đưa dữ liệu lớn/runtime/artifact sinh tự động vào Git; chỉ commit tài liệu, script/config cần thiết và biểu đồ phù hợp.
- Chạy kiểm thử phù hợp, rà soát nội dung gói/metadata, rồi mở PR vào main; không tự merge.

## Quyết định còn để người triển khai
Dùng phiên bản Julia và phần cứng đang có tại checkout này; ghi chính xác trong metadata. Giữ ngưỡng timeout/output của config hiện tại nếu pilot không chỉ ra là thiếu an toàn, nếu không thì ghi rõ thay đổi và áp dụng giống nhau cho cả hai variant. Theo lựa chọn của người dùng, scalability chạy trên cả 5 dataset tại 10%, 25%, 50%, 75%, 100%. Nếu pilot cho thấy chi phí vượt khả năng chạy thực tế, sẽ báo số liệu pilot và xin điều chỉnh phạm vi trước khi bỏ dataset nào.
