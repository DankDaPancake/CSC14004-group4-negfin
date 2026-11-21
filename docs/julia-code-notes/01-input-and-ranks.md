# Đầu vào, ngưỡng và rank

| Julia | Ý nghĩa | Python tương ứng |
|---|---|---|
| `Vector{Vector{Int}}` | Danh sách giao dịch, mỗi giao dịch là một vector ID | `list[list[int]]` |
| `sort!(unique(transaction))` | Tạo vector item duy nhất rồi sắp xếp tại chỗ | `sorted(set(transaction))` |
| `Rational{BigInt}` | Tỷ lệ chính xác để tính ngưỡng nguyên | `fractions.Fraction` |
| `sort!(items; by=item -> (counts[item], item))` | Khóa xếp theo support, rồi ID để phá hòa | `sorted(items, key=lambda item: (counts[item], item))` |
| `items[rank]` | Giải mã rank 1-based về ID | `items[rank - 1]` |

`read_spmf` đọc mỗi dòng dữ liệu thành một giao dịch và bỏ dòng trống hoặc metadata. `mine_baseline` chuẩn hóa lại khi nhận dữ liệu từ API. Hai dòng giao dịch giống nhau vẫn đóng góp hai lần. CLI nhận chuỗi thập phân như `0.4`; `Fraction` trong ví dụ minh họa phép tính sau khi chuỗi đã qua kiểm tra cú pháp của Julia.

```text
m ← ceil(minsup × số giao dịch)
đếm mỗi item tối đa một lần trong mỗi giao dịch
items ← sắp các item đạt m theo (support, ID)
rank[item] ← vị trí 1-based trong items
với mỗi giao dịch:
    bỏ item dưới ngưỡng, đổi các item còn lại thành rank giảm dần
```

```python
from collections import Counter
from fractions import Fraction
from math import ceil

def prepare(transactions, minsup):
    unique_rows = [set(row) for row in transactions]
    minimum = ceil(Fraction(minsup) * len(unique_rows))
    counts = Counter(item for row in unique_rows for item in row)
    items = sorted(
        (item for item in counts if counts[item] >= minimum),
        key=lambda item: (counts[item], item),
    )
    ranks = {item: rank for rank, item in enumerate(items, start=1)}
    ranked_rows = [
        sorted((ranks[item] for item in row if item in ranks), reverse=True)
        for row in unique_rows
    ]
    return minimum, items, ranked_rows

toy = [[1, 3, 4], [2, 3, 5], [1, 2, 3, 5], [2, 5], [1, 2, 3, 5]]
minimum, items, rows = prepare(toy, "0.4")
assert (minimum, items) == (2, [1, 2, 3, 5])
assert rows[0] == [3, 1]
assert rows[2] == rows[4] == [4, 3, 2, 1]
```

Item 4 chỉ có một lần xuất hiện nên bị lọc. Item 5 có **rank 4**, do đó dùng **bit 3**. Rank 4 giải mã về ID 5 khi ghi kết quả SPMF.
