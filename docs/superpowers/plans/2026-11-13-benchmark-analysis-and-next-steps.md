# Kế hoạch phân tích benchmark và công việc tiếp theo

**Mục tiêu:** Cập nhật local, kiểm tra và trực quan hóa số liệu Baseline, sau đó xác định bước tiếp theo có thể kiểm chứng.

**Nguồn:** `docs/validation/benchmark-baseline.md`, `bench/config.toml`, manifest và số liệu thô nếu Hiếu cung cấp. Không coi ước lượng từ các phép đo khác phạm vi là kết quả chính xác. Giữ nguyên Baseline và file chưa được theo dõi.

## 1. Đồng bộ và kiểm tra

- [x] Fetch, xác nhận không xung đột file chưa được theo dõi, fast-forward main lên `eee35e0`.
- [x] Chạy `julia --startup-file=no --project=. test/runtests.jl`: Julia 1.12.0, Windows, 1.195 assertion pass; nhóm SPMF opt-in chưa chạy.
- [x] Kiểm tra theo báo cáo commit đo, số lần lặp, checksum, phạm vi warm/cold, timeout, output cap và trạng thái số liệu thô; cần số liệu thô để kiểm chứng độc lập.

## 2. Trực quan hóa và đánh giá

- [x] Dùng bảng cold và scalability trong báo cáo làm nguồn khi chưa có dữ liệu thô; bảo toàn giá trị, đơn vị, nguồn và giới hạn. Không nội suy số liệu thiếu.
- [x] Tạo biểu đồ runtime cold và peak RSS theo minsup cho từng dataset, kèm min–max; dùng trục phù hợp, không nối các dataset khác ngưỡng thành một đường.
- [x] Tạo biểu đồ scalability theo số giao dịch cho từng dataset; ghi rõ dùng tiền tố 20/40/60/80/100%, chưa phải 10/25/50/75/100% theo checklist.
- [x] Tóm tắt số mẫu, output và thời gian từng giai đoạn theo workload đại diện; phân biệt warm/cold và tổng cấp phát/peak RSS. Không kết luận quan hệ nhân quả hay khẳng định cận trên từ hiệu số hai phép đo khác nhau.
- [x] Kiểm tra số hàng, giá trị đại diện, tiêu đề, đơn vị, nhãn và bố cục; số liệu thô vẫn cần đối chiếu độc lập.

## 3. Hướng công việc tiếp theo

- [x] Xác định workload đại diện và đề xuất profiling BigInt, NegNodeset và output trong `docs/validation/benchmark-analysis.md`.
- [ ] Sau profiling, lập kế hoạch Optimized chi tiết: giữ Baseline, kiểm chứng oracle/SPMF và benchmark hai phiên bản cùng điều kiện, nêu cả trường hợp chậm hơn hoặc tăng bộ nhớ.
- [x] Liệt kê dữ liệu thô cần Hiếu bàn giao, các mức scalability cần bổ sung, nguồn dữ liệu ổn định, và công việc ứng dụng/Colab song song.
- [ ] Kiểm tra tài liệu và biểu đồ; chuẩn bị PR theo quy định repository khi phần việc đã hoàn tất.
