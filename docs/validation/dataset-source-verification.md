# Xác minh nguồn tải benchmark

Kiểm ngày 27-11-2026 theo [task của Hiếu](../task-hieu.md) và [manifest benchmark](../../data/benchmark/manifest.toml). Mỗi URL được tải mới bằng `curl` vào thư mục tạm, không đăng nhập. Sau đó tính SHA-256 và đếm số giao dịch để so với `sha256` và `expected_transactions` trong manifest.

## Kết quả theo manifest

| Tập | URL đã thử | Ngày kiểm | SHA-256 thực tế | Kết luận |
|---|---|---|---|---|
| Chess | <https://www.philippe-fournier-viger.com/spmf/publicdatasets/chess.txt> | 27-11-2026 | `a12ea887df58a396709430af5bf0a9a32d1f6eba8e7c13dd41f28b98572c5db2` | khớp, 3.196 giao dịch |
| Chess | <https://fimi.uantwerpen.be/data/chess.dat> | 27-11-2026 | `a12ea887df58a396709430af5bf0a9a32d1f6eba8e7c13dd41f28b98572c5db2` | khớp |
| Mushroom | <https://www.philippe-fournier-viger.com/spmf/publicdatasets/mushrooms.txt> | 27-11-2026 | `3bc1159b06baa231932810d1d58cbb958684be88b6daa8e3672f8d76c5f0eb98` | khớp, 8.416 giao dịch |
| Retail | <https://www.philippe-fournier-viger.com/spmf/publicdatasets/retail.txt> | 27-11-2026 | `732c26de19888cb570d3fbb97e47206a9b1c0ce064f85dc1403314ba38f04eaa` | khớp, 88.162 giao dịch |
| Accidents | <https://www.philippe-fournier-viger.com/spmf/publicdatasets/accidents.txt> | 27-11-2026 | `8c2275550966e3cb4b6066f2bb168489a9566c500af559fa3925f1b11d97f0cd` | khớp, 340.183 giao dịch |
| Accidents | <https://fimi.uantwerpen.be/data/accidents.dat> | 27-11-2026 | `8c2275550966e3cb4b6066f2bb168489a9566c500af559fa3925f1b11d97f0cd` | khớp |
| T10I4D100K | <https://www.philippe-fournier-viger.com/spmf/publicdatasets/T10I4D100K.txt> | 27-11-2026 | `949983f61aa976d1b774474fadd31c5f15775b24728a5e7c8b79801822ab3f89` | khớp, 100.000 giao dịch |

Cả bảy URL đều tải được và khớp hash. Manifest không cần sửa. Tên file khi khôi phục lấy theo trường `path` trong manifest.

## FIMI cho ba tập chỉ có link SPMF

Mục này chỉ để tham khảo. Các URL dưới đây không có trong manifest.

| Tập | URL | SHA-256 | Kết luận |
|---|---|---|---|
| Mushroom | <https://fimi.uantwerpen.be/data/mushroom.dat> | `6cf94bc482712c3936f0b40c921381ab2b776c3d9941880fecac4d83ca5cbeb5` | khác hash và khác dữ liệu (8.124 giao dịch, so với 8.416), không thay được |
| Retail | <https://fimi.uantwerpen.be/data/retail.dat> | `d967431ba522e32f0fbb243f2ee113ecd4cb374cb0234c1b0858dae1d499a055` | khác hash; cùng 88.162 giao dịch, mã item trong file SPMF bằng mã FIMI cộng 1, FIMI xuống dòng LF còn SPMF dùng CRLF |
| T10I4D100K | <https://fimi.uantwerpen.be/data/T10I4D100K.dat> | `464d7b87aa7fdc0dc432ddad0493515569b2968b0f229ce39399c454a8c62e0c` | khác hash; cùng 100.000 giao dịch, lệch mã item +1 và khác kiểu xuống dòng như Retail |

Với Retail và T10I4D100K, có thể dựng lại file từ FIMI: giữ nguyên thứ tự item, cộng 1 vào mọi mã item, bỏ khoảng trắng cuối dòng và kết thúc mỗi dòng bằng CRLF. File dựng lại khớp SHA-256 trong manifest cho cả hai tập. Lệnh dùng trong Git Bash:

```sh
awk '{sub(/[ \r]+$/,""); n=split($0,a," "); o=""; for(i=1;i<=n;i++) o=o (i>1?" ":"") a[i]+1; printf "%s\r\n", o}' retail.dat > retail.txt
```

Thay `retail` bằng `T10I4D100K` cho tập còn lại. Mushroom không có cách tương tự vì bản FIMI là dữ liệu khác.

## Điểm còn vướng

- Mushroom chỉ có một nguồn là SPMF. Retail và T10I4D100K có link SPMF khớp byte và có thể dựng lại từ FIMI như trên. Cần TA xác nhận chấp nhận link SPMF cho Mushroom, và cách dựng lại từ FIMI cho Retail và T10I4D100K nếu link SPMF không còn khi chấm.
