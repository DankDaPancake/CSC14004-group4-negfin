# Duyệt DFS, promotion và biểu diễn bitmap

`mine_baseline` tạo một `Candidate` cho mỗi singleton phổ biến. `visit!` nhận lõi hiện tại và phần đuôi danh sách ứng viên cùng mức. Mỗi ứng viên con giữ NegNodeset của chính nó để những phép mở rộng sâu hơn dùng được danh sách của sibling. `emit_family!` phát từng tập cùng support qua callback; ở CLI, callback gọi `write_itemset`.

```text
VISIT(core, current, siblings, inherited):
    equivalent ← bản sao inherited
    children ← rỗng
    với mỗi sibling theo thứ tự rank:
        nếu core chỉ có 1 item:
            negative ← lọc Nodeset(current.rank) theo bit vắng của sibling.rank
        nếu core có từ 2 item:
            negative ← lọc sibling.negative theo bit có mặt của current.rank
        support ← current.support − tổng count trong negative
        nếu support bằng current.support: đưa sibling.rank vào equivalent
        nếu support giảm nhưng còn đạt ngưỡng: lưu ứng viên con cùng negative
    phát core hợp với mỗi tập con của equivalent, kể cả tập rỗng
    với mỗi child theo thứ tự:
        VISIT(child.rank ghép trước core, child, các children sau child, equivalent)
```

Nếu support giữ nguyên, item thêm có mặt trong mọi giao dịch chứa lõi và cả mọi tập giao dịch con của lõi. Thuật toán giữ item đó để phát kết quả và chuyển xuống mức sâu hơn. Trong toy, ID 2 luôn đi cùng ID 5, nên nhánh lõi `{2}` phát cả `{2}` và `{2,5}` với support 4.

```python
from itertools import combinations

def emit_family(core, equivalent, support, items, emit):
    for size in range(len(equivalent) + 1):
        for subset in combinations(equivalent, size):
            ranks = [*core, *subset]
            emit(sorted(items[rank - 1] for rank in ranks), support)

output = []
emit_family([2], [4], 4, [1, 2, 3, 5], lambda ids, sup: output.append((ids, sup)))
assert output == [([2], 4), ([2, 5], 4)]

def word_bitmap(bitmap, nbits):
    mask = (1 << 64) - 1
    return [(bitmap >> offset) & mask for offset in range(0, nbits, 64)]

def word_has(words, rank):
    if rank <= 0:
        raise ValueError("rank must be positive")
    word_index, offset = divmod(rank - 1, 64)
    return word_index < len(words) and bool(words[word_index] & (1 << offset))

words = word_bitmap((1 << 63) | (1 << 64), 65)
assert word_has(words, 64) and word_has(words, 65)
assert not word_has(words, 63)
```

Python dùng `combinations` để minh họa cùng họ tập hợp. Julia dùng đệ quy chọn hoặc bỏ từng item tương đương, nên thứ tự phát có thể khác. Trong Julia, dấu `!` là quy ước tên cho hàm có tác động lên dữ liệu/callback. Một lời gọi `do ... end` truyền hàm vào vị trí đối số đầu tiên, tương tự truyền callable vào một hàm Python.

Đoạn Python dưới đây tương ứng với `visit!`. Chạy sau các đoạn Python ở mục 01–03 để có các hàm chuẩn bị, lọc và phát mẫu.

```python
def visit(core, current, siblings, inherited, nodesets, minimum, items, emit):
    rank, parent_support, _ = current
    equivalent = inherited.copy()
    children = []
    for added_rank, _, sibling_negative in siblings:
        if len(core) == 1:
            negative = negative_pair(nodesets[rank], added_rank)
        else:
            negative = negative_extension(sibling_negative, rank)
        support = extended_support(parent_support, negative)
        if support == parent_support:
            equivalent.append(added_rank)
        elif support >= minimum:
            children.append((added_rank, support, negative))

    emit_family(core, equivalent, parent_support, items, emit)
    for position, child in enumerate(children):
        visit([child[0], *core], child, children[position + 1:], equivalent,
              nodesets, minimum, items, emit)

minimum, items, rows = prepare(toy, "0.4")
nodesets = collect_nodesets(rows)
roots = [(rank, sum(count for _, count in nodesets[rank]), [])
         for rank in range(1, len(items) + 1)]
patterns = []
for position, root in enumerate(roots):
    visit([root[0]], root, roots[position + 1:], [], nodesets, minimum, items,
          lambda ids, sup: patterns.append((tuple(ids), sup)))
assert len(patterns) == len(dict(patterns)) == 15
```

| Phần | Baseline | Optimized |
|---|---|---|
| Xây BMC-tree | Bitmap đường đi là `BigInt` | Dùng cùng cây và bước xây |
| Thu Nodeset | `NodeInfo` giữ bitmap `BigInt` | Đổi sang `WordNodeInfo` chứa `Vector{UInt64}` |
| Kiểm tra rank | `bitmap & item_mask(rank)` | `word_has` truy cập trực tiếp một word |
| Duyệt và kết quả | `visit!`, support có trọng số và promotion | `visit_word!` áp dụng cùng hai quy tắc lọc và cùng cách xuất |

Python `int` có độ dài tùy ý như `BigInt`. Các word của ví dụ Python vẫn có kiểu `int`, được giới hạn 64 bit bằng mask để minh họa chỉ số và offset. Trong Julia, word của rank 65 là phần tử **2**, offset **0**. Chi phí chuyển đổi nằm ở `collect_nodesets`, còn peak RSS phụ thuộc cả quá trình giữ cây và các cấu trúc khai thác. [Mã Optimized](../../src/optimized.jl) · [Kết quả thực nghiệm](../report/chapter2.md)
