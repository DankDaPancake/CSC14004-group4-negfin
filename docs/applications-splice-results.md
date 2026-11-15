# Ứng dụng 2 — Pattern vị trí–base trên Splice-junction

Dữ liệu và cách tạo transaction: [applications-proposal.md](applications-proposal.md). Mỗi chuỗi DNA 60 base là một transaction gồm item `p<vị trí>_<base>` (vị trí −30..−1, +1..+30; điểm nối nằm giữa −1 và +1). negFIN Baseline chạy **riêng từng lớp**; mẫu số là số chuỗi của lớp đó: EI (exon→intron, donor) 767, IE (intron→exon, acceptor) 768, N (không phải điểm nối) 1.655.

## Số mẫu theo minsup

| Lớp | minsup 0,5 | 0,3 | 0,2 |
|---|---:|---:|---:|
| EI | 35 (dài ≤ 4) | 280 (≤ 5) | 2.375 (≤ 6) |
| IE | 7 (≤ 3) | 331 (≤ 4) | 1.284 (≤ 5) |
| N | 0 | 0 | 240 (chỉ 1 item) |

Chọn **minsup 0,3** cho phân tích chính. Lớp N không có mẫu nào ở 0,3; ở 0,2 có đủ 240 item đơn (mỗi base ở mỗi vị trí ≈ 25%) nhưng không có cặp nào — chuỗi không phải điểm nối không có tín hiệu vị trí, đúng như kỳ vọng và là đối chứng cho hai lớp còn lại.

## Item có mặt ở ≥ 50% chuỗi (minsup 0,5)

- **EI:** `p-2_A` 58%, `p-1_G` 81%, `p+1_G` 99,7%, `p+2_T` 99,0%, `p+4_A` 72%, `p+5_G` 86% → `…AG|GT·AG…`.
- **IE:** `p-3_C` 79%, `p-2_A` 99,6%, `p-1_G` 99,7% → `…CAG|…`.

## Pattern đặc trưng của lớp (minsup 0,3)

`apps/splice/compare.py` tính support của mỗi itemset ở cả ba lớp và growth = support lớp đích / support các lớp khác gộp lại.

**EI (donor)** — top theo growth:

| Pattern | EI | IE | N | Growth |
|---|---:|---:|---:|---:|
| p+1_G p+2_T p+4_A p+5_G p+6_T | 30,2% | 0,0% | 0,0% | ∞ |
| p+1_G p+2_T p+5_G p+6_T | 40,3% | 0,1% | 0,1% | 488 |
| p+1_G p+2_T p+3_A p+4_A | 32,6% | 0,1% | 0,1% | 263 |
| p+1_G p+2_T p+4_A p+5_G | 63,8% | 0,9% | 0,1% | 193 |
| p-1_G p+1_G p+2_T p+4_A p+5_G | 47,3% | 0,9% | 0,0% | 164 |

**IE (acceptor)** — top theo growth:

| Pattern | EI | IE | N | Growth |
|---|---:|---:|---:|---:|
| p-12_T p-3_C p-2_A p-1_G | 3,4% | 33,2% | 0,4% | 25,1 |
| p-10_T p-3_C p-2_A p-1_G | 2,9% | 32,9% | 0,6% | 24,9 |
| p-11_T p-3_C p-2_A p-1_G | 3,8% | 37,1% | 0,7% | 22,5 |
| p-13_T p-3_C p-2_A p-1_G | 4,4% | 32,8% | 0,4% | 19,9 |
| p-7_C p-3_C p-2_A p-1_G | 5,1% | 35,9% | 0,3% | 19,8 |

## Diễn giải sinh học

Đối chiếu với consensus đã biết của vị trí cắt nối ở intron GT-AG: donor `MAG|GTRAGT`, acceptor `(Y)n N CAG|G` (Shapiro & Senapathy, 1987, *Nucleic Acids Research* 15(17)).

- **Donor (EI):** negFIN tìm lại gần đủ consensus: `G` ở −1 (và `A` ở −2) phía exon, `GT` ở +1..+2 (99% chuỗi EI, so với 14% IE và 5,9% N), rồi `A/G` +3, `A` +4, `G` +5, `T` +6. Itemset dài 5 `GT·AGT` xuất hiện ở 30% chuỗi EI và không có ở lớp khác.
- **Acceptor (IE):** `CAG` ở −3..−1 (78,8% IE, so với 22,8% EI, 2,3% N; riêng `AG` 99,5%). Các pattern đặc trưng nhất ghép `CAG` với `T`/`C` ở −6..−17 — tương ứng **polypyrimidine tract** trước acceptor. Kiểm tra trực tiếp: tỷ lệ pyrimidine vùng −20..−5 là 77,4% ở IE, so với 49,1% EI và 49,3% N.
- Growth của IE thấp hơn EI vì tín hiệu acceptor phân tán (nhiều vị trí pyrimidine, mỗi vị trí chỉ ~30–40%), còn donor tập trung ở vài vị trí gần như cố định.

## Giới hạn

- Itemset là tập hợp: mã hóa theo vị trí giữ được vị trí tuyệt đối, nhưng không có thứ tự hay khoảng cách tương đối; motif bị dịch vị trí (polypyrimidine tract không cố định) bị tách thành nhiều pattern rời rạc.
- Growth chỉ mô tả mức đặc trưng trên dữ liệu này, không phải bộ phân lớp đã đánh giá; không dùng cho kết luận dự đoán.
- Dữ liệu năm 1991 (GenBank 64.1), chỉ gen linh trưởng, chỉ quanh điểm nối GT-AG; giữ nguyên 185 chuỗi trùng của nguồn; 15 chuỗi có base mơ hồ không sinh item tại vị trí đó.
- Chỉ khẳng định các pattern khớp consensus đã công bố; các pattern còn lại (ví dụ `p-25_G` trong một pattern EI) chỉ là quan sát.
- `splice.names` mục 3(b) ghi ngược donor/acceptor; dùng theo mục 4 và sinh học: EI = donor, IE = acceptor.

## Kiểm chứng

- `python -m unittest discover -s apps/tests`: test support theo lớp, growth, growth vô hạn và phát hiện lệch support.
- `compare.py` đếm lại support của toàn bộ 611 itemset (EI 280, IE 331) từ transaction và báo lỗi nếu khác output negFIN: không có lệch.

## Tái lập

```text
python apps/splice/prepare.py --input data/applications/raw/splice/splice.data --outdir results/apps/splice/full
julia --startup-file=no --project=. run.jl --input results/apps/splice/full/transactions_EI.txt --output results/apps/splice/full/out_EI_0.3.txt --minsup 0.3 --stats results/apps/splice/full/out_EI_0.3.stats.toml
python apps/splice/compare.py --target EI --itemsets results/apps/splice/full/out_EI_0.3.txt --data results/apps/splice/full --output results/apps/splice/full/compare_EI_0.3.csv
```

Lặp lại hai lệnh cuối với `IE` (lớp `N` không có mẫu ở minsup 0,3).
