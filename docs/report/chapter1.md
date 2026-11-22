# Chương 1. Cài đặt thuật toán negFIN

## 1.1. Bài toán khai thác tập phổ biến

Cho cơ sở dữ liệu giao dịch $D=(T_1,\ldots,T_N)$, trong đó mỗi $T_t$ là một tập item. Số lần xuất hiện (support count) của tập item $X$ là $s(X)=|\{t\mid X\subseteq T_t\}|$. Với ngưỡng tương đối $\theta\in(0,1]$, bài toán trả về mọi tập khác rỗng thỏa $s(X)\ge m$, với $m=\lceil\theta N\rceil$, cùng số lần xuất hiện của chúng. Hai giao dịch giống nhau vẫn được tính riêng. Với $X\subseteq Y$, ta có $s(Y)\le s(X)$, nên có thể bỏ toàn bộ nhánh mở rộng một tập có support dưới ngưỡng.

Nhóm cài đặt negFIN bằng Julia dựa trên mô tả của Aryabarzan và cộng sự [1]. Thuật toán gom tiền tố giao dịch trong một cây mã hóa bitmap và tính support bằng cách đếm phần giao dịch bị mất khi thêm item. Thư viện SPMF [2] cung cấp kết quả tham chiếu để kiểm chứng cài đặt của nhóm.

## 1.2. Cài đặt Baseline

**Mã hóa giao dịch và dựng cây.** Sau khi loại item trùng trong từng giao dịch, bước chuẩn bị đếm support của singleton, lọc theo $m$ và xếp hạng tăng dần theo cặp (support, ID gốc). Mỗi giao dịch đi vào cây tiền tố BMC (bitmap-coded tree) theo hạng giảm dần. Mỗi node lưu hạng item, số giao dịch đi qua node và bitmap của toàn đường đi đến node. Hạng $r$ tương ứng bit $r-1$. Khi các giao dịch có cùng tiền tố, chúng dùng chung node và tăng cùng bộ đếm. Nodeset của singleton gồm các bản ghi (bitmap, count) tương ứng với item đó. Tổng các count là support của singleton, kể cả khi nhiều giao dịch đi qua cùng một node.

**Tính support từ NegNodeset.** Với phép mở rộng $R=P\cup\{i\}$, NegNodeset của $R$ biểu diễn các giao dịch chứa $P$ nhưng thiếu $i$. Support được tính bằng $s(R)=s(P)-\sum_{u\in\operatorname{NegNodeset}(R)}u.\mathrm{count}$, theo Tính chất 8 trong [1]. Có hai trường hợp theo thứ tự mở rộng của thuật toán:

- Nếu $P$ là singleton, lọc Nodeset của $P$ và giữ bản ghi có bit của $i$ bằng 0.
- Nếu $P=\{j\}\cup X$ và $R=\{i,j\}\cup X$, lấy NegNodeset của ứng viên cùng mức $Q=\{i\}\cup X$ và giữ bản ghi có bit của $j$ bật. Các bản ghi này biểu diễn phần giao dịch chứa cả $X$ và $j$ nhưng thiếu $i$ (Tính chất 7 trong [1]).

**Duyệt và tỉa nhánh.** Cài đặt duyệt theo chiều sâu và chuẩn bị các ứng viên cùng mức trước khi đi sâu để mỗi phép mở rộng lấy đúng NegNodeset. Nếu $s(P\cup\{i\})=s(P)$, mọi giao dịch chứa $P$ đều chứa $i$. Theo quy tắc promotion trong [1], $i$ được lưu vào nhóm item tương đương và chuyển xuống các nhánh con của $P$. Với mỗi lõi phổ biến, hàm xuất kết quả kết hợp lõi với mọi tập con của nhóm item tương đương đang áp dụng. Cách này giảm số nhánh phải duyệt riêng và vẫn phát từng mẫu qua callback. Thứ tự hạng cố định giới hạn các hướng mở rộng, còn callback nhận ID gốc theo thứ tự tăng dần.

**Ví dụ.** Bộ toy trong repo có 5 giao dịch. Với $\theta=0{,}4$, ngưỡng tuyệt đối là 2. Item 1 xuất hiện 3 lần, trong đó chỉ giao dịch $\{1,3,4\}$ thiếu item 2, nên $s(\{1,2\})=3-1=2$. Item 2 xuất hiện 4 lần và luôn đi cùng item 5. Khi mở rộng $\{2\}$ bằng 5, NegNodeset rỗng và support vẫn là 4. Thuật toán lưu 5 như item tương đương cho nhánh này và phát mẫu $\{2,5\}$ cùng support 4. Sau khi loại item 4 vì chỉ xuất hiện một lần, kết quả đầy đủ có 15 tập phổ biến.

## 1.3. Biến thể Optimized và chi phí

Baseline biểu diễn bitmap bằng `BigInt`. Optimized giữ nguyên thứ tự hạng, cấu trúc BMC và công thức support. Khi thu Nodeset, bản này chuyển bitmap của mỗi bản ghi sang `Vector{UInt64}`. Với $F$ item phổ biến, mỗi bitmap dùng $\lceil F/64\rceil$ word. Để kiểm tra hạng $r$, thuật toán đọc word chỉ số $1+\lfloor(r-1)/64\rfloor$ và kiểm tra bit $(r-1)\bmod 64$. Mỗi phép kiểm tra như vậy dùng một lần truy cập word và một phép AND. Các phép lọc NegNodeset tái sử dụng bitmap đã chuyển, còn chi phí chuyển đổi được đo ở giai đoạn thu Nodeset.

Chi phí duyệt phụ thuộc vào tổng số bản ghi được quét qua các phép lọc NegNodeset và số mẫu phải phát. Trong Baseline, chi phí phép toán trên bitmap `BigInt` còn phụ thuộc vào độ rộng của toán hạng. Với Optimized, phần word của bitmap cần $8\lceil F/64\rceil$ byte cho mỗi bản ghi, cộng chi phí quản lý vector. Trong lúc chuyển đổi, dữ liệu bitmap của cây và các vector mới có thể cùng tồn tại. Kích thước cây phụ thuộc vào số tiền tố khác nhau sau khi lọc item. Số tập cần xuất có thể đạt $2^F-1$, chẳng hạn khi cả $F$ item luôn xuất hiện cùng nhau. Xuất dần giúp tránh giữ toàn bộ tập kết quả trong RAM.

Chương 2 báo cáo ba lần chạy cold cho mỗi cấu hình, gồm khởi động, JIT, đọc và ghi tệp. Ở Accidents, minsup 0,2, Optimized giảm median từ 49,54 xuống 12,76 giây và peak RSS từ 2.720,1 xuống 2.594,8 MiB. Ở T10I4D100K, minsup 0,002, median giảm từ 28,49 xuống 9,68 giây trong khi peak RSS tăng từ 1.503,5 lên 1.895,7 MiB. Hai ví dụ minh họa sự phụ thuộc của bộ nhớ vào cấu hình đo. [Chương 2](chapter2.md)

## 1.4. Giao diện và kiểm chứng

CLI `run.jl` đọc tệp giao dịch SPMF, mỗi dòng gồm các ID item nguyên dương cách nhau bằng khoảng trắng. Tham số `--minsup` nhận tỷ lệ thập phân và được chuyển sang phân số chính xác để tính ngưỡng nguyên. `--input` và `--output` chỉ định đường dẫn, còn `--variant` chọn `baseline` hoặc `optimized`. Mỗi dòng kết quả ghi ID tăng dần và số giao dịch chứa tập đó, ví dụ `1 2 #SUP: 2`. CLI ghi kết quả vào tệp tạm cùng thư mục đích rồi đổi tên khi hoàn tất. [Đặc tả CLI](../baseline-contract.md)

Kiểm thử tự động bao phủ parser, ngưỡng support, cây BMC, phép lọc có trọng số, promotion, bitmap qua ranh giới 64 bit và kết quả so với phép vét cạn trên các cơ sở dữ liệu nhỏ có seed cố định. Với benchmark đầy đủ, nhóm kiểm tra checksum của từng tập và chuẩn hóa kết quả thành ánh xạ từ tập item đến support, nhờ vậy có thể so sánh từng mẫu dù thứ tự dòng khác nhau.

**Bảng I.** Đối chiếu với SPMF 2.67a tại các mức minsup trong manifest. Số mẫu khớp là số mẫu có cả tập item và support giống nhau, tính riêng cho mỗi biến thể.

| Tập dữ liệu | Số giao dịch | Minsup | Mẫu SPMF | Baseline khớp | Optimized khớp |
|---|---:|---:|---:|---:|---:|
| Chess | 3.196 | 0,9 | 622 | 622/622 | 622/622 |
| Mushroom | 8.416 | 0,8 | 17 | 17/17 | 17/17 |
| Retail | 88.162 | 0,01 | 159 | 159/159 | 159/159 |
| Accidents | 340.183 | 0,9 | 31 | 31/31 | 31/31 |
| T10I4D100K | 100.000 | 0,02 | 155 | 155/155 | 155/155 |

Kết quả ở Bảng I đạt tỷ lệ khớp 100% trên cả năm cấu hình đã thử, với 0 mẫu thiếu, 0 mẫu dư và 0 trường hợp sai support ở mỗi biến thể. Có thể tái lập bằng nhóm test `spmf` theo [hướng dẫn trong README](../../README.md#tái-lập-đối-chiếu-spmf). Các phép đo hiệu năng sử dụng thiết lập riêng trong Chương 2.

## Tài liệu tham khảo (Chương 1)

[1] N. Aryabarzan, B. Minaei-Bidgoli và M. Teshnehlab, “negFIN: An efficient algorithm for fast mining frequent itemsets,” *Expert Systems with Applications*, tập 105, tr. 129–143, 2018. [DOI 10.1016/j.eswa.2018.03.041](https://doi.org/10.1016/j.eswa.2018.03.041).

[2] P. Fournier-Viger, J. C.-W. Lin, A. Gomariz, T. Gueniche, A. Soltani, Z. Deng và H. T. Lam, “The SPMF open-source data mining library version 2,” trong *Proc. ECML PKDD*, LNCS, tập 9853, tr. 36–40, 2016. DOI 10.1007/978-3-319-46131-1_8.
