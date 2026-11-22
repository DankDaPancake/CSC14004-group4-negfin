# Thiết kế benchmark cold SPMF–Julia đo mới

## Mục tiêu và quyết định của người dùng

Bổ sung thực nghiệm SPMF NegFIN để hoàn thiện Chương 2 và chuẩn bị bảng/hình cho Tiến theo checklist `task-hieu.md` đính kèm. Người dùng chọn **đo mới cả SPMF và Julia**, không tái sử dụng thời gian Julia cũ làm đường so sánh SPMF.

Đo Julia **Optimized**, cùng SPMF NegFIN, trên năm snapshot và bảy mức `[selected]` mỗi tập trong `bench/config-baseline-20261119.toml`: 35 điều kiện × 3 cold × 2 cài đặt = **210 lượt chính**, ngoài các lượt pilot. Không tự thay đổi mức minsup khi gặp timeout hoặc output cap.

## Các cách đã cân nhắc

1. **Đo mới cả hai — người dùng chọn.** Tốn thêm lượt Julia nhưng có phiên đo đồng nhất, cùng input, môi trường và phạm vi thời gian.
2. Đo mới SPMF, dùng lại Julia cold cũ sau kiểm toán môi trường và raw. Tiết kiệm thời gian nhưng khó loại trừ chênh lệch giữa hai phiên; không dùng theo lựa chọn của người dùng.

## Hiện trạng và giới hạn

- Nhánh làm việc: `test/spmf-julia-cold-benchmark`, tạo từ `origin/main` tại `70ad97c` sau fetch. Không thay đổi thuật toán, không commit/push trực tiếp main.
- Có năm file dataset local; phải kiểm lại SHA-256 và số giao dịch trước chạy.
- Tìm thấy Julia tại `C:/Users/tlthi/AppData/Local/Programs/Julia-1.12.0/bin/julia.exe`. Java/SPMF chưa được định vị, không có trong PATH/biến môi trường đã kiểm. Không coi benchmark có thể chạy trước khi xác minh đủ runtime.
- Harness cold hiện dành riêng Julia và xóa output sau đo. Helper SPMF correctness dùng dictionary toàn bộ output và không có cổng timeout/output; không dùng nguyên trạng cho các điểm hàng chục triệu itemset.
- Báo cáo Baseline–Optimized cũ có dữ liệu warm/cold/scalability và trade-off RSS; giữ nguồn và phân biệt với phiên mới.

## Phạm vi và những việc không làm

Làm runner tái lập, kiểm chứng output, đo mới, tổng hợp CSV, hình báo cáo và cập nhật Chương 2. Không sửa thuật toán negFIN, không benchmark warm mới, không thêm SPMF scalability hoặc đo độ dài giao dịch vào 210 lượt. Không tự coi hai hướng tối ưu hoặc phạm vi độ dài giao dịch đã được Đăng chấp thuận. Không gửi tin nhắn, upload raw, push hay mở PR trước khi được phép thực hiện hành động ra ngoài.

## Quy trình đề xuất

### 1. Preflight và nguồn gốc

Ghi commit, trạng thái dirty và SHA-256 source/config thực dùng; CPU, RAM, OS build, Julia/Java/SPMF versions, đường dẫn runtime local, jar SHA-256, hash và số giao dịch input, số thread và toàn bộ argv. Dùng Julia một thread. JVM đặt `-XX:ActiveProcessorCount=1` và `-Xmx4g`; ghi đây là cấu hình JVM và giới hạn Java heap, không phải giới hạn RSS tương đương giữa hai runtime. Không ép cache đĩa lạnh: cold nghĩa là **process mới**, không phải cold filesystem cache.

Tìm runtime local trước. Nếu thiếu jar/JDK, báo nguồn chính thức và xin phép tải; mỗi file tải/giải nén ở thư mục mới riêng trong vùng bị Git bỏ qua, không thực thi script tải về. Không chia sẻ chi tiết riêng của dự án với dịch vụ tìm nguồn dữ liệu.

### 2. Pilot và ngưỡng support

Chạy fixture nhỏ có đáp án và trường hợp ranh giới `ceil(N × minsup)`; kiểm tra cách SPMF chuyển chuỗi decimal sang ngưỡng nguyên, kể cả sai khác floating-point ở ranh giới. Lưu minsup yêu cầu, argv thực tế và ngưỡng kỳ vọng. Không âm thầm đổi ngưỡng hoặc làm tròn cho vừa kết quả. Nếu cần biểu diễn SPMF khác để có cùng ngưỡng, ghi ánh xạ rõ, kiểm chứng bằng fixture/source/log, và giữ điểm lỗi ngoài bảng đến khi giải thích được.

Pilot một mức dễ mỗi tập và điểm lớn Chess 0.3/Mushroom 0.02 theo thứ tự tăng tải, có các cổng tài nguyên bên dưới. Pilot tách hoàn toàn khỏi ba lượt chính. So từng itemset và support, không chỉ count/byte. Chỉ khởi chạy toàn bộ chiến dịch sau khi pilot không còn sai lệch chưa giải thích.

### 3. Runner và đo chính

Bổ sung orchestration Python standard library chạy bằng `python -I`, giữ Julia CLI và SPMF CLI thật. Phiên đầu hỗ trợ Windows hiện có; nếu nền tảng không có phương pháp peak RSS đã kiểm thử thì fail rõ, không ghi sampling hoặc Java heap như peak RSS.

Mỗi lượt là process mới, chạy tuần tự, không chạy hai miner cùng lúc. Luân phiên thứ tự SPMF/Julia giữa ba repetition của mỗi điều kiện; lưu thứ tự và thời điểm. Timer monotonic bắt đầu ngay trước tạo process, kết thúc khi process hoàn tất: bao gồm startup/JIT, đọc, mine, ghi và thoát. Không tính SHA/output validation, tổng hợp hoặc vẽ vào wall time. Dùng cùng filesystem và cùng file input, output riêng mỗi lượt; không ghi ra null device.

Windows peak RSS lấy từ OS peak working set của process qua handle còn hợp lệ; không lấy RSS của runner và không suy từ allocation/heap. Ghi metric/phương pháp cụ thể. Giữ stats Julia, stdout/stderr SPMF và exit code. Timeout 1.800 giây/process, cap output 2 GiB/process, cap RSS 8 GiB/process bằng giám sát (có độ trễ được ghi); kiểm tra cap cả trong khi chạy lẫn sau thoát. Không coi cổng giám sát là giới hạn tuyệt đối. Kiểm tra dung lượng đĩa trống tối thiểu 20 GiB trước lượt lớn và kiểm tra lại trước validation; dừng rõ khi không đủ.

Mỗi run có thư mục mới, config đóng băng và CSV append ngay sau từng lượt. Các trạng thái `timeout`, `output_cap`, `memory_cap`, `error`, `validation_failed`, `disk_limit` được giữ cùng log, không dùng tính median và không thay bằng số 0. Resume không ghi đè lượt cũ: chỉ bổ sung slot còn thiếu nếu provenance/config/source khớp; nếu không thì tạo campaign mới.

### 4. Kiểm chứng ngoài vùng đo

Canonical hóa mỗi dòng thành itemset tăng dần + support nguyên; bác bỏ dòng sai, item trùng, support không hợp lệ. External sort theo chunk với ngân sách RAM 64 MiB (giới hạn nội dung, có overhead được ghi), merge nhiều vòng fan-in tối đa 32; so hai luồng canonical, phát hiện duplicate itemset kể cả support khác nhau, missing/extra/support mismatch và đối chiếu ngưỡng/count. Không yêu cầu hai miner có cùng thứ tự output.

Thực hiện so chính xác trên cặp output đầu tiên của **mọi 35 điều kiện**, ngoài timer. Hai repetition còn lại kiểm tra parser/count và canonical digest đối với output đã xác minh của mỗi cài đặt; digest là kiểm tra lặp lại, không thay thế phép so chính xác đầu tiên. Scratch validation có cap 16 GiB và kiểm tra free disk; vượt cap là điểm chưa hợp lệ, không bỏ kiểm chứng để đưa vào đồ thị. Đóng băng SHA canonical/count và báo cáo so sánh trước khi xóa các output lớn do campaign mới tạo. Không xóa dữ liệu hay output cũ ngoài campaign.

### 5. Tổng hợp và bàn giao

Chỉ công bố median/min–max khi đủ ba lần hợp lệ, provenance đúng và output đã xác minh; điểm thiếu được ghi rõ, không nối thành số đo giả. Sinh runtime–minsup cho từng dataset với SPMF và Julia Optimized; hình itemset–minsup; peak RSS tại mức thứ tư của bảy mức selected (giữa theo thứ tự cấu hình). Scalability giữ số Baseline–Optimized cũ và ghi rõ ngày/phạm vi, không gán thành SPMF mới.

Xuất PNG/PDF dùng trong báo cáo, kèm caption, đơn vị, n và định nghĩa cold/RSS. Cập nhật Chương 2 dựa trên raw mới, giữ phân tích dày/thưa, output volume và trade-off T10I4D100K. Kiểm tra nguồn Hugging Face/Kaggle công khai; chỉ kết luận có snapshot phù hợp khi SHA-256 khớp, còn thiếu thì liệt kê rõ.

Git chỉ chứa config, runner/validator/tests, bảng tổng hợp nhỏ, hình và tài liệu; raw CSV/log/env/config được đóng gói local ngoài Git với manifest SHA-256 và hướng dẫn tái lập. Chuẩn bị nội dung bàn giao và PR; chưa thực hiện gửi/chia sẻ ra ngoài trong giai đoạn này.

## Kiểm thử và tiêu chí hoàn thành

- Unit test canonicalization, duplicate/support mismatch, external merge nhiều chunk, digest ổn định khi đảo thứ tự, lỗi/truncated output và cap validation.
- Runner test process thành công, exit lỗi, timeout, output/memory cap, log/CSV/resume không dùng stale output; test peak RSS bằng process con thật trên Windows.
- Test aggregate loại trial/error, không ghép campaign, xử lý thiếu repetition và không nhập số cũ vào đường mới.
- Chạy `julia --startup-file=no --project=. test/runtests.jl`, test Python mới và kiểm chứng SPMF fixture/pilot; ghi rõ phần chưa chạy/thất bại.
- Bàn giao số điểm hợp lệ/chưa hợp lệ, từng lượt có provenance, median/range tái tạo được, hình/caption và Chương 2 khớp raw. Không khẳng định đủ 210 lượt thành công khi có điểm timeout/cap.

## Các lựa chọn do người triển khai đề xuất, chờ duyệt

Python stdlib orchestration/validation, Windows native peak working set; Julia Optimized một thread, JVM active CPU 1/heap 4 GiB; timeout 30 phút, output 2 GiB, RSS giám sát 8 GiB; validation 64 MiB/chunk và 16 GiB scratch. Không chạy chính trước khi runtime/pilot/correctness sẵn sàng. Các ngưỡng có thể cần điều chỉnh sau pilot, nhưng phải ghi quyết định và tạo config phiên đo mới thay vì âm thầm thay đổi.
