# Kế hoạch thí nghiệm negFIN Optimized

**Mục tiêu:** Kiểm tra liệu biểu diễn bitmap theo word `UInt64` có giảm thời gian/cấp phát khi lọc NegNodeset, đồng thời giữ đủ itemset và support. Đây là giả thuyết dựa trên [profiling pilot](../../validation/profiling-pilot.md), chưa phải kết quả cải thiện.

**Ràng buộc:** Giữ `baseline` và API/CLI hiện tại; không sửa input, ngưỡng, support hoặc ownership của vector callback. Chỉ thêm variant riêng, không dùng thư viện FIM. Git branch feature mới từ `main` sau khi công việc phân tích được tích hợp.

**Tiến độ:** Đã có variant thử nghiệm và [pilot](../../validation/optimized-pilot.md). BMC vẫn dùng BigInt, bitmap Nodeset được chuyển sang word khi thu thập; điều này tạo trade-off RAM và khác với ý tưởng thay bitmap toàn bộ cây. Các ô bên dưới chỉ hoàn tất sau khi đáp ứng toàn bộ nội dung, kể cả CI và benchmark đầy đủ.

## 1. Xây và kiểm chứng bitmap

- [ ] Trước khi code, xác định cách lưu bitmap theo số word, ánh xạ rank sang bit, và quy tắc chia sẻ bất biến giữa BMC-node/NodeInfo. Đo chi phí cấp phát, bộ nhớ và phép thử bit; không giả định `Vector{UInt64}` luôn tốt hơn `BigInt`.
- [x] Viết test RED→GREEN cho kiểm tra bit tại rank 1, 64, 65, 70 và lớn hơn; bitmap rỗng và bitmap có nhiều word; phép đọc không thay đổi vector bitmap.
- [ ] Viết test NegNodeset pair/extension và weighted support so với Baseline trên bitmap nhiều word, bao gồm bit vị trí cao.

## 2. Tích hợp variant và correctness

- [ ] Thêm API/CLI `optimized` theo cấu trúc đã chọn, giữ đường chạy `baseline` nguyên vẹn; nếu cần thay interface, cập nhật contract và test tương ứng.
- [ ] So sánh đầy đủ itemset/support với oracle vét cạn trên tập nhỏ, random seed cố định, input rỗng/duplicated/relabel/promotion, và bitmap >64. Xác nhận callback nhận vector độc lập.
- [ ] Chạy toàn bộ test local/CI trên Linux, Windows và Julia tối thiểu; đối chiếu SPMF trên năm snapshot cùng minsup; ghi missing/extra/support mismatch và checksum.

## 3. Đo lường cùng điều kiện

- [ ] Chọn pilot đại diện: Retail 0,002 và 0,001; Chess 0,45 và 0,3; Accidents 0,45 và 0,2; xác nhận thời gian, output cap và RAM trước khi chạy full. Bổ sung Mushroom/T10I4D100K.
- [ ] Đo baseline và optimized trên cùng máy, phiên bản Julia, input/hash, minsup, phạm vi callback/output, startup/warm-up; xen kẽ thứ tự để giảm bias và lưu raw. Dùng cùng quy tắc timeout, output cap và phép đo RSS.
- [ ] Báo median, min–max, số lần lặp, thời gian, cấp phát, peak RSS và số mẫu; nêu trường hợp không cải thiện hoặc hồi quy. Không so sánh cold với warm hay cấp phát với RSS.
- [ ] Với output dày, đo count và CLI write riêng; không gán chênh lệch 2 chế độ khác process hoàn toàn cho I/O. Nếu variance lớn, tăng lặp và kiểm soát CPU/GC trước khi kết luận.

## 4. Quyết định

- [ ] Chỉ đề xuất dùng optimized khi correctness đầy đủ và có cải thiện lặp lại được trên workload mục tiêu; nếu không, giữ baseline, ghi kết quả âm và thử giả thuyết độc lập như giảm cấp phát NegNodeset hoặc output.
- [ ] Không tuyên bố hoàn thành toàn bộ benchmark/chương ứng dụng; các mức scalability, nguồn công khai và dữ liệu raw tiếp tục được theo dõi riêng.
