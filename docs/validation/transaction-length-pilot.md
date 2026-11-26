# Pilot ảnh hưởng của độ dài giao dịch

Pilot dùng dữ liệu tổng hợp để xem lượng công việc của negFIN thay đổi thế nào khi mỗi giao dịch có nhiều item hơn. Kết quả bổ sung cho thí nghiệm scalability trên dữ liệu thực, vốn thay đổi số giao dịch.

## Thiết lập

- 10.000 giao dịch, universe 512 item, seed `20261125`. Mỗi giao dịch lấy tiền tố dài 5, 10, 20 hoặc 40 của cùng một hoán vị ngẫu nhiên. Không lặp item trong giao dịch.
- Minsup 0,008, tương ứng ít nhất 80 giao dịch. Giữ ngưỡng tuyệt đối và tương đối cố định giữa các độ dài. Lượt thử với universe 256 và minsup 0,015 được dừng vì quá nhiều cặp ứng viên ở độ dài 40 và được loại khỏi kết quả.
- Windows 11 build 26100, Intel Core i7-11800H, Julia 1.12.0 một luồng. Một lượt kiểm chứng và một lượt warm-up count cho mỗi biến thể ở mỗi độ dài, sau đó ba lần đo xen kẽ thứ tự Baseline/Optimized. Gọi GC trước khi bấm giờ.
- Thời gian warm count đo lời gọi hàm Julia, gồm chuẩn hóa, dựng cây, thu Nodeset và khai thác qua callback. Sinh dữ liệu, khởi động process, kiểm chứng itemset và ghi tệp nằm ngoài thời gian đo. Byte cấp phát là tổng cấp phát của lời gọi. Pilot này không đo peak RSS.
- Đối chiếu trực tiếp tập itemset và support giữa hai biến thể ở mỗi độ dài trước khi đo. Hash đầu vào, node BMC, số bản ghi đã quét và số mẫu được ghi theo từng lượt.

## Kết quả

Mỗi ô thời gian là median [min–max] từ ba lượt mới, đơn vị giây. Hai biến thể có cùng số node, bản ghi quét và itemset ở từng độ dài. Đã kiểm đủ 24 lượt đo.

| Item/giao dịch | Singleton phổ biến | Node BMC | Bản ghi quét | Itemset | Baseline (s) | Optimized (s) |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 496 | 37.638 | 10.592.198 | 496 | 1.557 [1.481–1.631] | 0.343 [0.318–0.359] |
| 10 | 512 | 86.572 | 24.000.798 | 512 | 3.843 [3.554–3.898] | 0.892 [0.795–0.977] |
| 20 | 512 | 183.235 | 49.244.166 | 512 | 7.457 [7.214–7.621] | 1.646 [1.612–1.650] |
| 40 | 512 | 378.929 | 100.444.039 | 1.365 | 17.211 [17.124–18.498] | 3.644 [3.553–3.681] |

Từ 10 lên 20 item/giao dịch, số mẫu vẫn là 512. Số node BMC tăng 2,12 lần, số bản ghi quét tăng 2,05 lần và median thời gian tăng ở cả hai biến thể. Đây là cặp điểm thuận tiện để minh họa chi phí tăng dù đầu ra giữ nguyên trong thiết lập này. Ở mức 40 item, cả lượng bản ghi quét và số mẫu cùng tăng. Mức 5 chỉ có 496 singleton vượt ngưỡng, nên số item thực sự tham gia khai thác cũng thay đổi. Các kết quả mô tả một seed và một máy, và chỉ áp dụng cho phạm vi warm count đã ghi ở trên.

## Tái lập

```powershell
julia --startup-file=no --threads=1 --project=. bench/transaction-length-pilot.jl > results/transaction-length-pilot-20261125.csv
```

Tạo thư mục `results/` nếu chưa có. Script yêu cầu bộ sinh số ngẫu nhiên của Julia để tái lập dữ liệu. Dùng cùng phiên bản Julia và so SHA-256 trong CSV trước khi đối chiếu số đo. Dữ liệu tổng hợp được tạo trong RAM.

## Hai hướng tối ưu tiếp theo

1. **Biểu diễn bitmap thưa.** Profile heap theo pha trên T10I4D100K để định vị phần bộ nhớ tăng. Thử cấu trúc thưa cho bitmap có ít bit bật. So peak RSS cold và thời gian warm với variant hiện tại trên cùng input/minsup, tính cả chi phí chuyển đổi ở `collect_nodesets`.
2. **Ghi output theo lô.** Tách phép đo count và write trên các điểm nhiều mẫu của Chess và Mushroom. Thử ghi theo lô rồi so wall time cold, thời gian ghi và peak RSS. Với cả hai hướng, đối chiếu từng itemset và support trước khi đánh giá hiệu năng.
