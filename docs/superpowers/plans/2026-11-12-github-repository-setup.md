# GitHub Repository Setup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Đây là kế hoạch; chưa tạo remote, push hoặc đổi nhánh trong lượt lập kế hoạch.

**Goal:** Đưa repo negFIN hiện có lên GitHub public, giữ lịch sử phát triển, có CI và cấu trúc đáp ứng yêu cầu môn học; theo dõi rõ các sản phẩm cần bổ sung trước khi nộp.

**Architecture:** Một repo `CSC14004-group4-negfin` chứa source Julia, test, notebook và báo cáo; default branch đề xuất là `main`. Dữ liệu benchmark lớn lấy từ nguồn công khai bên ngoài và kiểm checksum. CI chạy test local độc lập với SPMF; demo Colab và báo cáo được tích hợp khi các phần đồ án tương ứng hoàn thành.

**Tech Stack:** Git/GitHub, Julia >= 1.9 (đã kiểm chứng 1.12.0), GitHub Actions; không cần Jupyter Book hoặc GitHub Pages cho yêu cầu hiện tại.

**Spec:** [README hiện tại](../../../README.md), [contract Baseline](../../baseline-contract.md), [đề bài FIM](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/itemset/), [tổng quan các đồ án](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/).

## Global Constraints

- Đề FIM yêu cầu một link public GitHub repository của nhóm nộp trên Moodle; lịch sử commit minh bạch.
- Đã kiểm tra trang FIM, trang tổng quan đồ án và trang môn học ngày 12/11/2026: không có yêu cầu tạo Jupyter Book.
- Notebook demo public trên Google Colab; link trong README; notebook chạy sạch từ đầu.
- Báo cáo tiếng Việt, 10–15 trang IEEE conference format, không tính tài liệu tham khảo/phụ lục; file `docs/Report.pdf`.
- README có môi trường, cách chạy, ví dụ và output của lần chạy test cuối.
- Dữ liệu benchmark lớn có link công khai trên Hugging Face/Kaggle; mã chuẩn bị dữ liệu nằm trong notebook hoặc file repo được notebook import.
- Giữ source/test Julia hiện có; không viết lại thuật toán trong notebook hoặc dùng thư viện FIM thay phần nhóm tự cài.
- Chỉ riêng Baseline được hoàn thành; Optimized, các thực nghiệm đầy đủ và hai ứng dụng vẫn là công việc tiếp theo của nhóm.
- Điều kiện tách 2 repo mà Đăng nêu chỉ áp dụng nếu đề yêu cầu Book. Điều kiện hiện không xảy ra: lập kế hoạch cho **1 repo**, không thêm repo Book.

## Hiện trạng đã kiểm tra

- Thư mục local: `CSC14004-group4-negfin/`; branch duy nhất `feat/negfin-baseline`, HEAD `4dc3925`.
- Có 9 commit, working tree sạch trước khi tạo file kế hoạch này.
- Chưa có remote `origin`, chưa có branch `main`; chưa xác định GitHub owner hoặc repo đã tạo sẵn.
- Có source, test, `Project.toml`, toy data và bằng chứng correctness trên 5 file benchmark full.
- CI, `notebooks/demo.ipynb`, `docs/Report.pdf`, link Colab và nguồn lưu trữ HF/Kaggle chưa có.
- Kế hoạch Baseline cũ có link trỏ ra ngoài repo tới tài liệu local và PDF gốc; cần đổi thành tài liệu trong repo hoặc URL nguồn để clone hoạt động độc lập.
- Lệnh `gh` chưa tìm thấy trong PATH; chưa xác định phiên GitHub đã đăng nhập. Khi thực thi, dùng công cụ GitHub khả dụng hoặc Git kết hợp cơ chế đăng nhập của máy; không mặc định tài khoản từ git user.name/email.

## Các lựa chọn đề xuất

| Mục | Đề xuất | Căn cứ |
| --- | --- | --- |
| Số repo | 1 | Đề FIM yêu cầu một repo public và không yêu cầu Book |
| Tên | `CSC14004-group4-negfin` | Giữ tên thư mục dự án hiện có; đề công khai không quy định mẫu tên bắt buộc |
| Owner | Đợi Đăng cung cấp username/org hoặc URL repo | Không suy ra từ tên/email tác giả Git |
| Visibility | Public | Bắt buộc theo đề |
| Default branch | `main` | Quy ước đề xuất để người chấm và Colab lấy bản ổn định |
| Phát triển | Feature branch → review → main | Đề xuất phối hợp nhóm, không phải rubric bắt buộc |
| CI | Local test trên Linux và Windows | Kiểm tra clone độc lập và khác biệt nền tảng |
| Hosting Book/Pages | Không cấu hình | Không nằm trong yêu cầu FIM đã kiểm tra |

Đăng đã xác nhận owner `DankDaPancake` và URL `https://github.com/DankDaPancake/CSC14004-group4-negfin` trong yêu cầu push tiếp theo. Các mô tả chưa có remote phía trên là snapshot lúc lập kế hoạch.

Owner là đầu vào bắt buộc của bước tạo/push remote, nhưng không ngăn việc chuẩn bị file và lập kế hoạch. Chỉ thực hiện các thay đổi GitHub khi Đăng yêu cầu triển khai kế hoạch; lượt hiện tại không có hành động publish.

## Review Focus

1. Link Markdown trỏ ra ngoài repository: clone mới vẫn phải đọc được tài liệu và chạy source. Task 1 và Task 5.
2. Repo remote đã tồn tại hoặc có commit khác: kiểm tra remote trước push; không force-push hoặc ghi đè lịch sử. Task 4.
3. Runtime, dataset và log local: không vô tình đưa `.tools`, jar, scratch hoặc dữ liệu lớn vào Git; giữ được dữ liệu toy và báo cáo kiểm chứng cần thiết. Task 1.
4. Test local pass nhưng Colab/Linux chưa chạy: CI và notebook phải kiểm trên môi trường sạch, không dùng đường dẫn D: hoặc runtime ngoài repo. Task 2 và Task 6.
5. Có repo public nhưng thiếu sản phẩm nộp: theo dõi riêng readiness trước nộp; không coi push Baseline là hoàn thành đồ án. Task 3 và Task 6.

## File sẽ chuẩn bị khi thực thi

| File | Thay đổi |
| --- | --- |
| `README.md` | Nhận diện nhóm, trạng thái các phần, GitHub/Colab/data links và hướng dẫn clone/run |
| `.gitignore` | Kiểm tra loại đúng runtime/dataset/scratch, vẫn giữ toy và evidence |
| `docs/project-requirements.md` | Tóm tắt yêu cầu FIM và các quyết định đã chốt, có nguồn chính thức |
| `docs/submission-checklist.md` | Phân biệt đã setup GitHub với đã đủ điều kiện nộp |
| `docs/superpowers/plans/2026-11-12-negfin-baseline.md` | Sửa link Spec ra ngoài repo; giữ lịch sử kế hoạch |
| `.github/workflows/ci.yml` | Chạy test Julia tự động |
| `CONTRIBUTING.md` | Lệnh test, nhánh làm việc và ghi nhận đóng góp của 3 thành viên |
| `notebooks/demo.ipynb` | Sản phẩm tiếp theo khi dựng demo thực nghiệm/ứng dụng, không tạo notebook trống để đánh dấu hoàn thành |
| `docs/Report.pdf` | Báo cáo hoàn chỉnh ở giai đoạn viết/nộp, không tạo PDF placeholder |

## Task 1: Chuẩn hóa repo để clone độc lập

**Files:** Modify `README.md`, `.gitignore`, `docs/superpowers/plans/2026-11-12-negfin-baseline.md`; Create `docs/project-requirements.md`.

**Input:** Baseline đã kiểm chứng ở HEAD 4dc3925, yêu cầu môn học và quyết định 1 repo.

**Output:** Toàn bộ source và tài liệu cần thiết nằm trong repo; paper dùng DOI/URL nguồn, không cần PDF local bên ngoài.

- [ ] Tạo nhánh chuẩn bị `chore/github-setup` từ HEAD hiện có khi bắt đầu triển khai; không đổi branch trong lượt lập kế hoạch.
- [ ] Tạo `docs/project-requirements.md` ghi một repo public, Julia/negFIN, notebook Colab, Report.pdf, test, nguồn dữ liệu và phân công Đăng/Hiếu/Tiến.
- [ ] Thay các link `../../../../...` trong kế hoạch Baseline bằng link yêu cầu nằm trong repo và DOI/paper URL phù hợp. Không sao chép PDF xuất bản vào Git.
- [ ] Kiểm tra `git ls-files`: không có runtime, dataset benchmark .txt, jar hoặc `.superpowers`; toy .txt, manifest và evidence vẫn được theo dõi.
- [ ] Kiểm tra các blob trong lịch sử bằng `git rev-list --objects --all` kết hợp thông tin size khi cần; repo hiện nhỏ nên chưa cần Git LFS. Không quyết định thêm LFS chỉ vì có Report.pdf.
- [ ] Kiểm lại toàn bộ link local của Markdown tính theo vị trí file: không cần truy cập workspace cha để mở chúng.
- [ ] Chạy test local bằng Julia; chỉ thay tài liệu/config, không sửa thuật toán nếu không có lỗi mới.
- [ ] Commit riêng `docs: prepare self-contained GitHub repository`.

**Gate:** có thể xuất/clone bản đã commit vào một thư mục tạm ngoài workspace cha, đọc README và chạy test mà không dựa vào `.tools` của máy gốc; Julia có thể được cài riêng.

## Task 2: Cấu hình GitHub Actions cho Julia

**Files:** Create `.github/workflows/ci.yml`; Modify `README.md` để mô tả CI khi đã có run thực tế.

**Input:** `julia --startup-file=no --project=. test/runtests.jl` chạy suite local không cần dataset lớn/Java.

**Output:** CI kiểm tra tự động trên mỗi push và PR, có thể chạy thủ công.

- [ ] Tạo workflow `Julia CI` với trigger `push`, `pull_request`, `workflow_dispatch`; quyền `contents: read`, timeout 15 phút, `fail-fast: false`.
- [ ] Dùng action hiện đã đối chiếu tài liệu: `actions/checkout@v6`, `julia-actions/setup-julia@v3`.
- [ ] Matrix đề xuất 3 job: Ubuntu/Julia `1.9`, Ubuntu/Julia `1.12.0`, Windows/Julia `1.12.0`; quote giá trị version để YAML không đọc thành số.
- [ ] Mỗi job setup Julia rồi chạy đúng test command; chưa cần Java, download benchmark hoặc cache package cho source chỉ dùng stdlib.
- [ ] Không hard-code số assertion của Windows cho Linux: 4 regression case-insensitive chỉ chạy trên Windows. Gate là exit 0 và không fail/skip bất ngờ, không phải cùng số đếm mọi OS.
- [ ] Giữ đối chiếu SPMF 5 tập là bước có chủ đích với runtime/dataset; không gắn nó vào mọi push ở đợt setup đầu.
- [ ] Commit `ci: test Julia baseline on Linux and Windows`.

**Gate:** cú pháp workflow được kiểm trước push; sau Task 4 phải thấy cả 3 job chạy thật và pass. Không ghi badge xanh hay tuyên bố Julia 1.9/Linux đã pass trước khi có bằng chứng.

## Task 3: README và checklist nộp bài

**Files:** Modify `README.md`; Create `docs/submission-checklist.md`, `CONTRIBUTING.md`.

**Input:** Các file hiện có, tên repo đề xuất và trạng thái công việc đã xác minh.

**Output:** Người chấm có thể nhận diện nhóm, chạy code và biết phần nào còn đang thực hiện.

- [ ] README có họ tên/mã nhóm; bổ sung MSSV khi thành viên cung cấp, không tự điền dữ liệu cá nhân chưa biết.
- [ ] Giữ hướng dẫn môi trường, CLI, toy 15 mẫu, seed, paper và bằng chứng test; thêm hướng dẫn clone theo owner/repo đã xác nhận.
- [ ] Có bảng tiến độ: Baseline/test/correctness đã có; Optimized, benchmark đầy đủ, 2 ứng dụng, demo Colab và Report.pdf đang bổ sung.
- [ ] Dành mục demo Colab và dữ liệu công khai nhưng ghi rõ chưa hoàn thành khi chưa có link thật; không dùng URL giả để qua checklist.
- [ ] CONTRIBUTING ghi mỗi thành viên commit phần việc của mình, test trước PR, không dùng force push/squash lại lịch sử phát triển đã công khai. Đây là quy ước đề xuất của nhóm.
- [ ] Checklist tách hai mốc: **GitHub đã setup** và **đồ án sẵn sàng nộp**; không đánh đồng 2 mốc.
- [ ] Commit `docs: add contribution and submission guidance`.

**Gate:** README phản ánh đúng sản phẩm có thật; người chấm thấy rõ link nguồn, lệnh chạy và trạng thái.

## Task 4: Tạo public repo và đẩy lịch sử

**Files:** Không cần sửa thuật toán; thay đổi cấu hình remote/branch và repo GitHub khi được yêu cầu triển khai.

**Input bắt buộc:** GitHub owner/URL do Đăng cung cấp; phiên đăng nhập có quyền tạo/push repo đó; các commit chuẩn bị đã kiểm tra.

**Output:** `https://github.com/DankDaPancake/CSC14004-group4-negfin`, visibility public, default branch main, giữ lịch sử Baseline.

- [ ] Xác nhận owner từ tài khoản GitHub thực tế/Đăng cung cấp, không suy ra từ Git author. Nếu cần đăng nhập, dùng cơ chế xác thực của công cụ; không đưa token vào README/remote URL.
- [ ] Kiểm tra repo mục tiêu đã tồn tại chưa. Nếu chưa, tạo repo public **rỗng**, không khởi tạo README/license/gitignore trên remote vì local đã có lịch sử.
- [ ] Nếu repo đã có commit hoặc `origin` đã tồn tại: fetch và kiểm tra quan hệ lịch sử trước khi thay đổi. Không chạy nguyên lệnh dưới đây lên trạng thái khác precondition, không force push.
- [ ] Tạo branch `main` trỏ tới commit chuẩn bị cuối cùng. Giữ branch Baseline cũ; không init lại hoặc gom 9 commit cũ thành một initial commit.
- [ ] Trong trường hợp mới, origin chưa có và main chưa tồn tại, chuỗi lệnh dự kiến là:

```text
git branch main HEAD
git remote add origin https://github.com/DankDaPancake/CSC14004-group4-negfin.git
git remote -v
git push -u origin main
git push -u origin feat/negfin-baseline
```

- [ ] Đặt default branch GitHub là `main`. Chuyển workspace local sang main sau khi xác nhận nhánh và working tree sạch.
- [ ] Thêm description: `Frequent itemset mining with negFIN in Julia — HCMUS Data Mining project`; topics đề xuất `julia`, `data-mining`, `frequent-itemset-mining`, `negfin`.
- [ ] Kiểm tra API/trang public truy cập không cần đăng nhập; đối chiếu SHA `main` local với remote, và xác nhận các commit Baseline cũ vẫn nằm trong lịch sử remote.
- [ ] Khi thêm cộng tác viên, dùng username GitHub và phạm vi quyền Đăng đã cho phép; không tự gửi lời mời trong lượt lập kế hoạch này.

**Gate:** public URL tồn tại, main là default branch, commit history giữ nguyên; không cần tạo PR giả giữa hai branch chứa cùng lịch sử chỉ để khởi tạo repo.

## Task 5: Kiểm chứng từ GitHub và chốt setup

**Files:** Modify `README.md` chỉ khi cần cập nhật URL/CI thật; giữ bằng chứng chạy mới khi thích hợp.

**Input:** URL repo public và workflow đã push.

**Output:** Bằng chứng người khác clone được và chạy được, không dựa vào môi trường local của Đăng.

- [ ] Clone public URL vào thư mục mới bằng phiên không dùng credential riêng cho read; kiểm tra source, toy, manifest và doc có đủ.
- [ ] Chạy unit test và toy command; xác nhận 15 itemset/support khớp fixture.
- [ ] Mở các link tài liệu trong bản clone, bảo đảm không còn link local phụ thuộc thư mục cha hoặc ổ D:.
- [ ] Kiểm tra lần chạy GitHub Actions thật: 3 job phải pass. Nếu CI thất bại, đọc log, sửa, push rồi kiểm tra lại trước khi đánh dấu hoàn thành setup.
- [ ] Cập nhật README với URL/badge đúng nếu dùng badge; không thay output test local bằng trạng thái CI chưa chạy.
- [ ] Theo dõi tiến trình CI bằng cơ chế của công cụ được dùng lúc triển khai; không bỏ dở failure rồi báo đã hoàn tất.

**Gate:** người chấm có thể mở repo, clone và tái lập toy; CI xanh. Hoàn thành Task 1–5 nghĩa là **setup GitHub xong**, chưa phải đồ án đã đủ điều kiện nộp.

## Task 6: Các mục phải bổ sung trước khi nộp Moodle

Các mục này được đưa vào checklist; không yêu cầu hoàn thành toàn bộ Chương 2/3 ngay trong đợt setup GitHub.

| Mục | Phụ trách theo phân công | Điều kiện hoàn thành |
| --- | --- | --- |
| Optimized và số liệu cải thiện | Đăng + Hiếu đo | So với Baseline, giữ kết quả đúng, có số liệu thực |
| Thực nghiệm Chương 2 | Hiếu, Đăng giải thích lõi | Các biểu đồ/runtime/RAM/scalability và phân tích theo đề |
| Hai ứng dụng | Tiến, Đăng hỗ trợ chạy lõi | Một hướng ứng dụng 1 và một hướng ứng dụng 2, chạy bằng code nhóm |
| Nguồn benchmark ổn định | Hiếu | Link HF/Kaggle công khai; checksum khớp manifest hoặc ghi nhận cập nhật nguồn/version |
| `notebooks/demo.ipynb` | Tiến phối hợp Hiếu/Đăng | Colab kernel Python cài Julia chính thức, clone repo public, tải dữ liệu, gọi Julia; chạy sạch từ đầu |
| `docs/Report.pdf` | Đăng/Hiếu/Tiến theo chương | Tiếng Việt, IEEE 10–15 trang, paper gốc + ít nhất 3 tài liệu liên quan |
| README cuối | Hiếu, cả nhóm review | Link Colab/data thật, môi trường, ví dụ, test output cuối, thông tin thành viên đầy đủ |
| Nộp | Nhóm | Nộp đúng một URL repo GitHub public lên Moodle trước hạn thực tế |

- [ ] Notebook giữ cùng repo source; link Colab có dạng `https://colab.research.google.com/github/DankDaPancake/CSC14004-group4-negfin/blob/main/notebooks/demo.ipynb` sau khi file thật được push.
- [ ] Dùng môi trường Colab mới và Run all; không coi notebook mở được là notebook đã chạy sạch.
- [ ] Checkpoint cuối: `docs/Report.pdf` mở được, link data/Colab truy cập public, tất cả phần cần chấm chạy lại được.
- [ ] Ghi commit SHA cuối trong ghi chú nộp/README khi phù hợp để gắn kết quả với phiên bản; không tiếp tục mô tả snapshot cũ là phiên bản đã nộp.

## Tóm tắt thứ tự

1. Chuẩn hóa file và sửa link ngoài repo.
2. Thêm CI cùng README/checklist.
3. Xác định owner, tạo repo public rỗng, push main và lịch sử.
4. Kiểm tra clone mới và CI thật.
5. Tiếp tục bổ sung Colab, dữ liệu, các phần đồ án và Report.pdf trong cùng repo trước khi nộp.

## Nguồn đã kiểm tra

- [Đề FIM](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/itemset/): một repo public, Colab, Report.pdf, dữ liệu và test output.
- [Tổng quan đồ án](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/), [trang môn học](https://hcmus-cs-ta.github.io/lab-book/data-mining/): không có yêu cầu Book bổ sung cho FIM trong các trang đã kiểm tra.
- [GitHub: đưa repo local lên GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github): xác thực, remote, repo rỗng và push lịch sử hiện có.
- [GitHub: giới hạn repo](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits).
- [julia-actions/setup-julia](https://github.com/julia-actions/setup-julia): cú pháp action v3, phiên bản Julia và matrix.
- [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

## Self-review của kế hoạch

- [x] Quyết định 1 repo theo đúng đề FIM, xử lý điều kiện Book mà Đăng nêu.
- [x] Không coi đã có repo GitHub/owner/CI/Colab khi chưa kiểm chứng.
- [x] Có đường xử lý repo remote đã tồn tại; không làm mất lịch sử local.
- [x] Tách yêu cầu của giảng viên khỏi CI/main/branch conventions do trợ lý đề xuất.
- [x] Bao phủ 5 Review Focus bằng kiểm chứng file/history, clone, CI và readiness checklist.
- [x] Không thay thuật toán, tạo Book/Pages, remote, main hoặc push trong lượt lập kế hoạch.
