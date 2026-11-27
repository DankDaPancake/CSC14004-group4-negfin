# Khôi phục Retail và T10I4D100K từ FIMI

Dùng hướng dẫn này nếu URL tải SPMF trong [manifest benchmark](../../data/benchmark/manifest.toml) gặp lỗi. Đây là phương án dự phòng của nhóm để tái lập đầu vào đã đo. Các file `.dat` của FIMI cần chuyển đổi trước khi dùng cho benchmark.

Trong trao đổi trên Google Chat, thầy chấp nhận cho notebook tải trực tiếp từ FIMI thay Kaggle và lưu ý rằng sự cố ở nguồn tải có thể làm việc chấm khó khăn. Đăng cũng đã xác nhận với thầy rằng nhóm có thể để notebook tải Mushroom trực tiếp từ URL công khai của SPMF và kiểm tra SHA-256 sau khi tải. Với Retail và T10I4D100K, nhóm kiểm lại SHA-256 sau khi chuyển đổi từ FIMI để xác nhận dữ liệu khôi phục khớp với dữ liệu dùng trong benchmark.

| Snapshot | Nguồn FIMI | File cần khôi phục | Số giao dịch |
|---|---|---|---:|
| Retail | [retail.dat](https://fimi.uantwerpen.be/data/retail.dat) | `retail.txt` | 88.162 |
| T10I4D100K | [T10I4D100K.dat](https://fimi.uantwerpen.be/data/T10I4D100K.dat) | `T10I4D100K.txt` | 100.000 |

Bản FIMI của Mushroom có 8.124 giao dịch, trong khi snapshot SPMF đã đo có 8.416. Quy trình này chỉ áp dụng cho hai tập trong bảng. [Kết quả xác minh nguồn của Hiếu](dataset-source-verification.md)

## Tải, chuyển đổi và kiểm checksum

Chạy từ thư mục gốc repo bằng PowerShell với Python 3.11 trở lên. Script dùng thư mục tạm, giữ thứ tự giao dịch và item, cộng 1 vào mỗi mã item và ghi dữ liệu dưới dạng ASCII, mỗi dòng kết thúc bằng CRLF. File đã kiểm tra được lưu ngoài Git trong `results/`.

```powershell
@'
import hashlib
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

with Path("data/benchmark/manifest.toml").open("rb") as manifest:
    datasets = {entry["name"]: entry for entry in tomllib.load(manifest)["datasets"]}

sources = {
    "Retail": "https://fimi.uantwerpen.be/data/retail.dat",
    "T10I4D100K": "https://fimi.uantwerpen.be/data/T10I4D100K.dat",
}
results = Path("results")
results.mkdir(exist_ok=True)
verified = Path(tempfile.mkdtemp(prefix="fimi-verified-", dir=results))

with tempfile.TemporaryDirectory(prefix="negfin-fimi-") as temp:
    work = Path(temp)
    for name, url in sources.items():
        entry = datasets[name]
        original = work / f"{name}.dat"
        rebuilt = work / entry["path"]
        subprocess.run(
            ["curl.exe", "--fail", "--location", "--silent", "--show-error",
             "--max-time", "120", "--output", str(original), url],
            check=True,
        )
        transactions = 0
        with original.open("rb") as src, rebuilt.open("wb") as dst:
            for line in src:
                items = line.split()
                if not items:
                    raise ValueError(f"{name}: giao dịch rỗng tại dòng {transactions + 1}")
                dst.write(b" ".join(str(int(item) + 1).encode("ascii") for item in items) + b"\r\n")
                transactions += 1
        with rebuilt.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if transactions != entry["expected_transactions"] or digest != entry["sha256"]:
            raise ValueError(f"{name}: không khớp manifest ({transactions} giao dịch, SHA-256 {digest})")
        shutil.copyfile(rebuilt, verified / entry["path"])
        print(f"{entry['path']}: {transactions} giao dịch, SHA-256 {digest}, khớp")

print(f"File đã xác minh: {verified}")
'@ | python -
```

Dùng đúng tên file được in ra khi chép snapshot đã xác minh vào `data/benchmark/`. Nếu quá trình dừng do hash hoặc số dòng khác manifest, giữ nguyên dữ liệu hiện có và ghi lại URL cùng thông báo lỗi để nhóm kiểm tra.
