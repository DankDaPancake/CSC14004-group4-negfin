# Đề xuất hai ứng dụng negFIN (Mốc 1 — cần nhóm chốt)

Tiến, 2026-11-15. Nguồn, checksum và giấy phép: [data/applications/manifest.toml](../data/applications/manifest.toml) (cả hai CC BY 4.0, UCI). Dữ liệu gốc không commit.

## Ứng dụng 1 — Giỏ hàng: UCI Online Retail

Hóa đơn của một cửa hàng quà tặng trực tuyến ở Anh, 2010-12-01 → 2011-12-09, 541.909 dòng.

**Transaction** = một `InvoiceNo`; **item** = `StockCode` sản phẩm (đổi sang chữ hoa), trùng trong hóa đơn → 1 item. ID = thứ tự sắp xếp chuỗi mã sau lọc (1..n), ổn định với cùng dữ liệu + quy tắc. `mapping.csv`: `id, stock_code, description, n_invoices`; description là mô tả xuất hiện nhiều nhất của mã (650 mã có > 1 mô tả).

| Bước lọc (theo thứ tự) | Lý do | Dòng | Hóa đơn |
|---|---|---:|---:|
| Gốc | | 541.909 | 25.900 |
| Bỏ InvoiceNo không toàn số (`C…` hủy, `A…` điều chỉnh nợ) | không phải giao dịch mua | 532.618 | 22.061 |
| Bỏ `Quantity ≤ 0` | trả hàng / ghi nhận hỏng | 531.282 | 20.725 |
| Bỏ `UnitPrice ≤ 0` | điều chỉnh kho, không phải bán | 530.103 | 19.959 |
| Chỉ giữ mã `^\d{5}[A-Z]*$` | bỏ POST, DOT, M, C2, BANK CHARGES, AMAZONFEE, gift_*, DCGS*… | 527.725 | **19.773** |

Kết quả: 19.773 giao dịch, 3.791 item, trung bình 26,2 item/giao dịch. **Giữ** dòng thiếu `CustomerID` (135.080 dòng) vì phân tích giỏ hàng chỉ cần hóa đơn — cần nhóm đồng ý.

Chạy thử Baseline (toàn bộ dữ liệu): minsup 0,03 → 143 mẫu (dài nhất 2); 0,02 → 395 (dài 3, 8,8 s); 0,01 → 2.026 (dài 5, 34 s). **Đề xuất minsup chính 0,01** (≥ 198 hóa đơn) để có itemset ≥ 3 sản phẩm cho sinh luật; minconf đề xuất 0,5. Ví dụ itemset (minsup 0,02): GREEN + PINK + ROSES REGENCY TEACUP AND SAUCER, 541 hóa đơn (2,7%).

## Ứng dụng 2 — Sinh học: UCI Splice-junction Gene Sequences

3.190 chuỗi DNA linh trưởng (GenBank 64.1), mỗi chuỗi 60 base, vị trí −30..−1, +1..+30 quanh điểm nối. Lớp: EI 767 (exon→intron, *donor*), IE 768 (intron→exon, *acceptor*), N 1.655 (không phải điểm nối). Lưu ý: mục 3(b) của `splice.names` ghi nhầm donor/acceptor; mục 4 và sinh học xác nhận EI = donor, IE = acceptor.

**Transaction** = một chuỗi; **item** = cặp `vị trí–base`, ví dụ `p+1_G`. ID cố định không phụ thuộc dữ liệu: `id = 4·chỉ_số_vị_trí + chỉ_số_base(A,C,G,T) + 1` (240 item). Base mơ hồ (N 56, D 2, S 1, R 1 lần; 15 chuỗi) không sinh item tại vị trí đó. Giữ nguyên 185 chuỗi trùng như nguồn. Khai thác riêng từng lớp (mẫu số = số chuỗi của lớp) rồi so sánh.

Chạy thử Baseline trên 200 chuỗi/lớp, minsup 0,5: EI 35 mẫu, IE 19, N 0. Pattern dài nhất khớp motif đã biết:
- EI: `p-1_G + p+1_G + p+2_T` (83%), `p-1_G + p+1_G + p+2_T + p+5_G` (66,5%) — consensus donor `…G|GT·AG…`.
- IE: `p-3_C + p-2_A + p-1_G` (86,5%), `+ p+1_G` (53%) — consensus acceptor `…CAG|G…`.
- N: không vị trí nào có base ≥ 50% — đúng kỳ vọng với chuỗi không phải điểm nối.

**Giới hạn:** itemset là tập hợp nên chỉ thể hiện đồng xuất hiện của các base ở vị trí cố định, không có thứ tự hay khoảng cách; mã hóa theo vị trí giữ được vị trí nhưng không phát hiện motif dịch chuyển. Đề xuất minsup chính 0,3–0,5 trên toàn bộ từng lớp.

## Kiểm chứng đã làm

- `python -m unittest discover -s apps/tests` — 5 test cho lọc, mapping, mẫu và base mơ hồ.
- Support của 104 itemset lấy ngẫu nhiên từ output negFIN được đếm lại độc lập bằng Python: khớp 100%.

## Tái lập

```text
python apps/retail/prepare.py --input "data/applications/raw/retail/Online Retail.xlsx" --outdir results/apps/retail/full
python apps/splice/prepare.py --input data/applications/raw/splice/splice.data --outdir results/apps/splice/full
julia --startup-file=no --project=. run.jl --input results/apps/retail/full/transactions.txt --output results/apps/retail/full/out_0.01.txt --minsup 0.01
```

Cần Python ≥ 3.10 với `pandas`, `openpyxl`. Thêm `--max-transactions N` / `--max-per-class N` để chạy mẫu.

## Cần nhóm chốt

1. Hai hướng: giỏ hàng + sinh học (splice).
2. Chính sách lọc retail, đặc biệt giữ dòng thiếu `CustomerID`.
3. Tiền xử lý + sinh luật bằng Python, negFIN qua CLI Julia (contract cho phép).
4. minsup chính: retail 0,01 / minconf 0,5; splice 0,3–0,5 theo lớp.
