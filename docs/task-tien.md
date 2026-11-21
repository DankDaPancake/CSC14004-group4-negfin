# Task của Tiến — hoàn thiện ứng dụng và tổng hợp báo cáo

Hai ứng dụng Online Retail và Splice-junction, notebook demo và bản nháp Chương 3 đã có trên `main`. Tiến hoàn thiện các sản phẩm này và ghép báo cáo của nhóm theo [đề đồ án](https://hcmus-cs-ta.github.io/lab-book/data-mining/projects/itemset/).

## Làm ngay

- [ ] Rà soát [Chương 3](report/chapter3.md) và [kết quả Online Retail](applications-retail-results.md). Đưa **top 10 luật có lift cao nhất** vào chương hoặc phụ lục có dẫn chiếu. Giữ bảng luật đa dạng nếu cần minh họa thêm. Kiểm tra support, confidence, lift và diễn giải kinh doanh.
- [ ] Rà soát phần Splice-junction. Nêu rõ cách mã hóa giao dịch, cách tính support theo lớp và giới hạn của kết luận. Đối chiếu số liệu với [kết quả ứng dụng](applications-splice-results.md).
- [ ] Chạy **Run all** trên runtime Colab mới từ [notebook demo](../notebooks/demo.ipynb). Ghi commit và phiên bản Julia, đối chiếu output với báo cáo. Kiểm tra link công khai trong README bằng phiên chưa đăng nhập.
- [ ] Chuẩn bị bản ghép theo mẫu IEEE conference. Chuẩn hóa đánh số mục, bảng, hình, công thức và tài liệu tham khảo trong cả ba chương.

## Ghép bản nộp

- [ ] Nhận Chương 1 từ Đăng ([PR #12](https://github.com/DankDaPancake/CSC14004-group4-negfin/pull/12)) và Chương 2 cùng hình cuối từ Hiếu. Có thể dàn trang trước trong lúc hai phần này được chốt.
- [ ] Xuất `docs/Report.pdf` bằng tiếng Việt, 10–15 trang phần chính, chưa tính tham khảo và phụ lục. Kiểm mọi bảng và hình có caption, được dẫn trong văn bản, công thức có giải thích biến, và tài liệu tham khảo có bài negFIN gốc cùng ít nhất ba nguồn liên quan.
- [ ] Mở PR gồm bản Chương 3 đã sửa, bản báo cáo và các cập nhật notebook/README liên quan. Ghi bằng chứng Run all, kết quả kiểm tra link công khai và số trang phần chính.

**Bàn giao cho nhóm** gồm PR, bản báo cáo có thể đọc và chỉnh sửa tiếp, link Colab công khai và danh sách điểm còn chờ từ Đăng hoặc Hiếu.
