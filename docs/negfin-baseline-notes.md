# negFIN Baseline: liên hệ với paper

Nguồn: Aryabarzan, Minaei-Bidgoli và Teshnehlab (2018), *negFIN: An efficient algorithm for fast mining frequent itemsets*, DOI: https://doi.org/10.1016/j.eswa.2018.03.041. Cài đặt được viết từ mô tả và giả mã của paper, không chuyển ngữ source SPMF.

## Dữ liệu và cấu trúc

- `prepare.jl`: đếm support; xếp item tăng theo (support, ID) rồi ánh xạ sang rank 1-based. Thứ tự tie cố định làm quan hệ mở rộng duy nhất. Giao dịch đi vào cây theo rank giảm dần.
- `bmc_tree.jl`: Algorithm 1. Bitmap của node chứa các item trên đường từ root đến node, kể cả item tại node. Bit rank r nằm ở vị trí r-1; bitmap root là 0.
- `NodeInfo(bitmap, count)` giữ trọng số node. Tổng count của Nodeset singleton bằng support của item; số record không nhất thiết bằng support.
- Bitmap dùng `BigInt` và phép toán bit công khai. Không giới hạn số frequent item ở 64; không sửa BigInt đã được node khác giữ.

## Hai bước tạo NegNodeset

1. Với cặp iP, lọc Nodeset(P) lấy các record không chứa i. Đây là phần giao dịch của P bị mất khi thêm i.
2. Với P=jX và R=ijX, lấy NegNodeset của **sibling Q=iX**, giữ các record chứa j theo Property 7. Không lọc NegNodeset(P) thay cho Q.
3. Support(R) = support(P) - tổng count trong NegNodeset(R), theo Property 8. Điều kiện bit bật là kết quả AND khác 0, không phải bằng 1 khi mask ở vị trí cao.

## Duyệt và promotion

`visit!` nhận một core jX và các sibling iX còn lại. Tất cả candidate con được tính trước khi đi sâu, để mỗi child có đúng NegNodeset sibling cần dùng.

Nếu thêm i không làm giảm support, i trở thành equivalent item. `emit_family!` phát core hợp với mọi tập con của equivalent cục bộ và kế thừa. Các item đã promote không xuất hiện lại trong candidate con. Đây là cách biểu diễn trực tiếp family/promotion của Algorithms 3/4 bằng DFS và callback, thay vì lưu toàn bộ cây itemset.

Một singleton chỉ được xuất qua family; không có lần xuất riêng thứ hai. Mỗi lần callback nhận vector mới, sắp theo ID gốc, vì rank khai thác không phải thứ tự ID đầu ra.

## Ví dụ kiểm chứng

`data/toy/example.txt` có 5 giao dịch. Minsup `0.4` cho min_count=2 và 15 itemset trong `example.expected.txt`. Trường hợp `[1,2,3], [1,2,3], [3]` ở minsup 2/3 cho 7 mẫu, kiểm tra promotion và support kế thừa.

## Chi phí và phạm vi

Baseline giữ toàn bộ giao dịch và BMC/Nodeset trong RAM khi chuẩn bị; CLI phát output dần. Runtime phụ thuộc số node, tổng số record NegNodeset đã duyệt, độ rộng BigInt và số mẫu cần xuất. Không coi phép AND trên số nguyên nhiều word là O(1) ở mọi kích thước, và không thể bỏ qua chi phí output có thể tăng theo cấp số nhân.

Bitmap và promotion đã là thành phần của negFIN gốc. Bản tối ưu sau này cần đo riêng cải tiến biểu diễn, cấp phát hoặc duyệt; giữ Baseline này để đối chứng.
