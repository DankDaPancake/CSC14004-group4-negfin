# Ứng dụng 1 — Luật kết hợp trên Online Retail

Dữ liệu và cách tạo transaction: [applications-proposal.md](applications-proposal.md). Tham số: **minsup 0,01** (≥ 198/19.773 hóa đơn), **minconf 0,5**, negFIN Baseline của nhóm.

| | Giá trị |
|---|---:|
| Giao dịch N | 19.773 |
| Frequent itemset (negFIN, minsup 0,01) | 2.026 (dài nhất 5) |
| Luật (minconf 0,5) | 962, từ 477 itemset |
| Lift: nhỏ nhất / trung vị | 4,74 / 12,03 |

Luật sinh từ output negFIN bằng `apps/retail/rules.py`: với mỗi frequent itemset Z, mọi cách chia Z = X ∪ Y (X, Y ≠ ∅, rời nhau); support = sup(Z)/N, confidence = sup(Z)/sup(X), lift = confidence/(sup(Y)/N).

## Top 10 theo lift

| # | X ⇒ Y | Support | Conf | Lift |
|---:|---|---:|---:|---:|
| 1 | THYME ⇒ ROSEMARY + PARSLEY | 1,03% (203) | 0,86 | 78,77 |
| 2 | ROSEMARY + PARSLEY ⇒ THYME | 1,03% (203) | 0,94 | 78,77 |
| 3 | THYME + PARSLEY ⇒ ROSEMARY | 1,03% (203) | 0,95 | 78,52 |
| 4 | ROSEMARY ⇒ THYME + PARSLEY | 1,03% (203) | 0,85 | 78,52 |
| 5 | THYME + BASIL ⇒ ROSEMARY | 1,01% (200) | 0,95 | 78,46 |
| 6 | ROSEMARY ⇒ THYME + BASIL | 1,01% (200) | 0,83 | 78,46 |
| 7 | ROSEMARY + BASIL ⇒ THYME | 1,01% (200) | 0,93 | 77,97 |
| 8 | THYME ⇒ ROSEMARY + BASIL | 1,01% (200) | 0,84 | 77,97 |
| 9 | THYME ⇒ ROSEMARY | 1,12% (221) | 0,93 | 76,83 |
| 10 | ROSEMARY ⇒ THYME | 1,12% (221) | 0,92 | 76,83 |

(Tất cả là `HERB MARKER <tên>` — que cắm đánh dấu chậu thảo mộc.) Cả 10 luật thuộc một họ sản phẩm và chỉ là các cách chia khác nhau của 3 itemset, nên bảng thứ hai dùng quy tắc khách quan để thấy nhiều nhóm hơn.

## Top 10 không trùng sản phẩm

Duyệt danh sách theo lift giảm dần, giữ luật chỉ khi không chứa sản phẩm nào đã có ở luật được giữ trước (`diverse_top` trong `rules.py`).

| # | X ⇒ Y | Support | Conf | Lift |
|---:|---|---:|---:|---:|
| 1 | HERB MARKER THYME ⇒ HERB MARKER ROSEMARY + PARSLEY | 1,03% (203) | 0,86 | 78,77 |
| 2 | HERB MARKER MINT ⇒ HERB MARKER BASIL | 1,05% (208) | 0,87 | 70,81 |
| 3 | REGENCY TEA PLATE PINK ⇒ REGENCY TEA PLATE ROSES + GREEN | 1,29% (255) | 0,84 | 51,82 |
| 4 | SET OF 3 WOODEN TREE DECORATIONS ⇒ SET OF 3 WOODEN STOCKING DECORATION | 1,11% (219) | 0,75 | 46,33 |
| 5 | REGENCY SUGAR BOWL GREEN ⇒ REGENCY MILK JUG PINK | 1,23% (243) | 0,75 | 45,36 |
| 6 | POPPY'S PLAYHOUSE LIVINGROOM ⇒ POPPY'S PLAYHOUSE BEDROOM + KITCHEN | 1,13% (224) | 0,68 | 43,14 |
| 7 | JAM JAR WITH GREEN LID ⇒ JAM JAR WITH PINK LID | 1,15% (228) | 0,74 | 42,94 |
| 8 | PINK POLKADOT CUP ⇒ BLUE POLKADOT CUP | 1,05% (208) | 0,68 | 41,22 |
| 9 | CHILDRENS CUTLERY DOLLY GIRL ⇒ CHILDRENS CUTLERY SPACEBOY | 1,15% (228) | 0,76 | 40,97 |
| 10 | BLUE POLKADOT BOWL ⇒ PINK POLKADOT BOWL | 1,05% (208) | 0,65 | 38,36 |

## Diễn giải kinh doanh

- **Mua trọn bộ sưu tập** (herb marker, Poppy's Playhouse, đồ trang trí gỗ Giáng sinh): khách mua một mẫu thường mua các mẫu cùng dòng. Gợi ý: bán theo bộ/combo, trang sản phẩm hiển thị "các mẫu còn lại trong bộ", xếp cạnh nhau khi trưng bày.
- **Phối nhiều màu cùng mẫu** (Regency tea set, jam jar, cốc/bát polkadot, dao dĩa trẻ em girl/boy): khách mua cùng thiết kế với nhiều màu/biến thể. Gợi ý: gói "mix màu", nhập kho các màu theo tỷ lệ cùng nhau, tránh hết hàng một màu làm mất đơn cả bộ.
- Confidence 0,65–0,95: ví dụ 93% hóa đơn có HERB MARKER THYME cũng có ROSEMARY. Lift 38–79: các cặp này cùng xuất hiện nhiều gấp hàng chục lần so với nếu mua độc lập.

## Giới hạn

- Một cửa hàng quà tặng ở Anh, 12/2010–12/2011; theo mô tả UCI, nhiều khách là **người bán sỉ**, nên luật phản ánh hành vi nhập hàng theo bộ nhiều hơn người tiêu dùng lẻ.
- Lift cao một phần vì từng sản phẩm hiếm (support riêng ~1,2–1,9%); lift nhạy với item hiếm, nên đọc kèm support và confidence.
- minsup 0,01 chỉ giữ sản phẩm có trong ≥ 198 hóa đơn; luật của sản phẩm ngách không xuất hiện. Hạ minsup tăng nhanh số mẫu (0,02 → 395; 0,01 → 2.026).
- Luật là đồng xuất hiện, không phải quan hệ nhân quả. Tên sản phẩm là mô tả phổ biến nhất của mỗi `StockCode`.

## Kiểm chứng

- `python -m unittest discover -s apps/tests`: test luật với ví dụ tính tay trên `data/toy` ({2}⇒{3}: conf 0,75, lift 0,9375; {5}⇒{1,2}: conf 0,5, lift 1,25; 50 luật khi minconf 0).
- 20 luật trong hai bảng được tính lại support/confidence/lift trực tiếp từ `transactions.txt`, không qua negFIN: khớp 100%. Mọi luật có confidence ≥ 0,5 và support count ≥ 198.

## Tái lập

```text
python apps/retail/prepare.py --input "data/applications/raw/retail/Online Retail.xlsx" --outdir results/apps/retail/full
julia --startup-file=no --project=. run.jl --input results/apps/retail/full/transactions.txt --output results/apps/retail/full/out_0.01.txt --minsup 0.01 --stats results/apps/retail/full/out_0.01.stats.toml
python apps/retail/rules.py --itemsets results/apps/retail/full/out_0.01.txt --stats results/apps/retail/full/out_0.01.stats.toml --mapping results/apps/retail/full/mapping.csv --output results/apps/retail/full/rules_0.01_0.5.csv --minconf 0.5
```
