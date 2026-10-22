"""hwpx를 한글로 열어 hwp·pdf로 저장하고 쪽 그림을 만든다."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
from pyhwpx import Hwp
import fitz

src, out_base, png_dir = sys.argv[1], sys.argv[2], sys.argv[3]
hwp = Hwp(visible=False)
hwp.open(src)
print("pages", hwp.PageCount)
hwp.save_as(out_base + ".hwp", "HWP")
hwp.save_as(out_base + ".pdf", "PDF")
hwp.quit()
os.makedirs(png_dir, exist_ok=True)
d = fitz.open(out_base + ".pdf")
for i, p in enumerate(d):
    p.get_pixmap(dpi=80).save(os.path.join(png_dir, f"p{i + 1}.png"))
print("pdf pages", d.page_count)
