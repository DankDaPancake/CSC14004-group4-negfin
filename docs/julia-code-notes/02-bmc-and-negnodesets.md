# BMC-tree, Nodeset và NegNodeset

`build_bmc` đi qua từng giao dịch đã xếp rank giảm dần. `get!(parent.children, rank) do ... end` chỉ tạo node khi nhánh đó chưa có, còn `count` tăng trên mọi lượt đi qua. Bitmap của node con lấy bitmap cha OR với bit của rank mới. `collect_nodesets` gom bản ghi `NodeInfo(bitmap, count)` theo rank và bỏ root nhân tạo.

```text
với mỗi giao dịch đã xếp rank:
    node ← root
    với mỗi rank r:
        nếu thiếu cạnh r: tạo node con có bitmap = bitmap cha OR bit(r)
        node ← node con theo cạnh r
        tăng node.count
duyệt các node khác root và gom (bitmap, count) theo rank
```

```python
def bit(rank):
    return 1 << (rank - 1)

def collect_nodesets(rows):
    root = {"children": {}, "bitmap": 0, "count": 0}
    for row in rows:
        node = root
        for rank in row:
            children = node["children"]
            if rank not in children:
                children[rank] = {
                    "children": {}, "bitmap": node["bitmap"] | bit(rank), "count": 0
                }
            node = children[rank]
            node["count"] += 1

    nodesets = {}
    pending = list(root["children"].items())
    while pending:
        rank, node = pending.pop()
        nodesets.setdefault(rank, []).append((node["bitmap"], node["count"]))
        pending.extend(node["children"].items())
    return nodesets

def negative_pair(nodes, added_rank):
    return [(bitmap, count) for bitmap, count in nodes if (bitmap & bit(added_rank)) == 0]

def negative_extension(sibling_negative, current_rank):
    return [(bitmap, count) for bitmap, count in sibling_negative if bitmap & bit(current_rank)]

def extended_support(parent_support, negative):
    return parent_support - sum(count for _, count in negative)

rows = [[3, 1], [4, 3, 2], [4, 3, 2, 1], [4, 2], [4, 3, 2, 1]]
nodesets = collect_nodesets(rows)
assert sum(count for _, count in nodesets[1]) == 3
assert extended_support(3, negative_pair(nodesets[1], 2)) == 2
assert extended_support(4, negative_pair(nodesets[2], 4)) == 4
demo = collect_nodesets([[3, 2, 1], [3, 2, 1], [2, 1], [3, 1]])
negative_q = negative_pair(demo[1], 3)
assert extended_support(3, negative_extension(negative_q, 2)) == 2
```

| Cần tính | Giả mã | Hàm Julia |
|---|---|---|
| Cặp `R = {i} ∪ P` với `P` là singleton | Giữ các bản ghi trong Nodeset(P) thiếu bit i | `negative_pair` |
| Tập lớn hơn `R = {i,j} ∪ X`, lõi hiện tại `P = {j} ∪ X` | Lấy NegNodeset của ứng viên cùng mức `Q = {i} ∪ X` rồi giữ bản ghi có bit j | `negative_extension` |
| Support của R | Support của P trừ **tổng count** các bản ghi được giữ | `extended_support` |

Trong toy, Nodeset của rank 1 có 2 bản ghi nhưng tổng count là 3. Thêm rank 2 làm mất một giao dịch, nên support cặp là 2. Ví dụ `demo` dùng bốn giao dịch đã cho rank để tính trường hợp ba item. Lõi `P = {1,2}` có support 3. Danh sách âm của `Q = {1,3}` giữ bản ghi từ giao dịch `{1,2}`. Vì bit 2 bật, phần mất đi là 1 và support của bộ ba là 2. Phép AND với một bit bật có thể trả về 2, 4, 8… nên điều kiện của Julia là `!iszero(bitmap & mask)`.
