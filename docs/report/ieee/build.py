"""Sinh LaTeX IEEE từ docs/report/chapter{1,2,3}.md và (nếu có trình biên dịch) xuất docs/Report.pdf.

    python docs/report/ieee/build.py            # sinh generated/*.tex, biên dịch nếu có tectonic/latexmk
    python docs/report/ieee/build.py --tex-only # chỉ sinh .tex (để tải lên Overleaf)

Cần pandoc >= 3. Biên dịch cần tectonic, latexmk + xelatex hoặc xelatex + bibtex.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent
DOCS = REPORT.parent

# [n] trong danh mục tham khảo riêng của từng chương -> khóa trong refs.bib
REFMAP = {
    1: {"1": "negfin", "2": "spmf"},
    2: {},
    3: {"1": "negfin", "2": "retail", "3": "agrawal", "4": "brin", "5": "splice", "6": "dongli", "7": "shapiro"},
}


def find_pandoc():
    found = shutil.which("pandoc")
    if not found:
        local = Path.home() / "AppData/Local/Pandoc/pandoc.exe"  # winget --scope user trên Windows
        found = str(local) if local.exists() else None
    if not found:
        sys.exit("Không tìm thấy pandoc >= 3.")
    return found


def generate():
    pandoc = find_pandoc()
    out = HERE / "generated"
    out.mkdir(exist_ok=True)
    for n, refs in REFMAP.items():
        src = REPORT / f"chapter{n}.md"
        refmap = ",".join(f"{k}={v}" for k, v in refs.items())
        tex = subprocess.run(
            [pandoc, str(src), "-f", "markdown", "-t", "latex", "--wrap=preserve",
             "--lua-filter", str(HERE / "report.lua"), "-M", f"chapter={n}", "-M", f"refmap={refmap}"],
            check=True, capture_output=True, text=True, encoding="utf-8").stdout
        # [n] còn sót nghĩa là chương trích nguồn chưa có trong REFMAP
        leftover = re.findall(r"(?<![\w{])\[\d+\]", tex)
        if leftover:
            sys.exit(f"chapter{n}.md: trích dẫn chưa ánh xạ sang refs.bib: {sorted(set(leftover))}")
        # mọi bảng/hình phải được dẫn trong văn bản, mọi khóa \cite phải có trong refs.bib
        unreferenced = [l for l in re.findall(r"\\label\{((?:tab|fig):[^}]+)\}", tex) if f"\\ref{{{l}}}" not in tex]
        if unreferenced:
            sys.exit(f"chapter{n}.md: bảng/hình chưa được dẫn trong văn bản: {unreferenced}")
        orphan = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", tex)
        for f in orphan:
            if not (REPORT / "figures" / f).exists():
                sys.exit(f"chapter{n}.md: thiếu file hình docs/report/figures/{f}")
        bib = (HERE / "refs.bib").read_text(encoding="utf-8")
        missing = [k for k in re.findall(r"\\cite\{([^}]+)\}", tex) if f"{{{k}," not in bib]
        if missing:
            sys.exit(f"chapter{n}.md: khóa trích dẫn không có trong refs.bib: {missing}")
        header = f"% Sinh tự động từ docs/report/chapter{n}.md bởi build.py — sửa file Markdown, không sửa file này.\n"
        (out / f"chapter{n}.tex").write_text(header + tex, encoding="utf-8", newline="\n")
        print(f"generated/chapter{n}.tex")


def compile_pdf():
    tectonic, latexmk = shutil.which("tectonic"), shutil.which("latexmk")
    xelatex, bibtex = shutil.which("xelatex"), shutil.which("bibtex")
    # MiKTeX can provide latexmk.exe even when its Perl runtime is absent.
    latexmk_ready = latexmk and (sys.platform != "win32" or shutil.which("perl"))
    if tectonic:
        subprocess.run([tectonic, "main.tex"], cwd=HERE, check=True)
    elif latexmk_ready and xelatex:
        subprocess.run([latexmk, "-xelatex", "-interaction=nonstopmode", "main.tex"], cwd=HERE, check=True)
    elif xelatex and bibtex:
        tex = [xelatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
        for command in (tex, [bibtex, "main"], tex, tex):
            subprocess.run(command, cwd=HERE, check=True)
    else:
        print("Không có bộ biên dịch: tải docs/report/ieee/ lên Overleaf, chọn compiler XeLaTeX.")
        return
    pdf = DOCS / "Report.pdf"
    shutil.copyfile(HERE / "main.pdf", pdf)
    try:
        import pymupdf  # tùy chọn: pip install pymupdf
    except ImportError:
        print(f"{pdf.relative_to(DOCS.parent)} đã ghi (cài pymupdf để đếm trang)")
        return
    doc = pymupdf.open(pdf)
    refs = next((i + 1 for i, p in enumerate(doc) if "TÀI LIỆU THAM KHẢO" in p.get_text().upper()), None)
    print(f"{pdf.relative_to(DOCS.parent)}: {doc.page_count} trang; tài liệu tham khảo bắt đầu ở trang {refs}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tex-only", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows mặc định cp1252
    generate()
    if not args.tex_only:
        compile_pdf()
