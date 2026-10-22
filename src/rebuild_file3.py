"""파일 3을 갱신한다: 새 목차 + 기존 참고자료 쪽(캡처·문헌) + 새 부록(A 분석 방법·결과, B 재현 방법).

실행: python rebuild_file3.py <기존 파일3.pdf> <그림 폴더(_summary.json 포함)> <부록 폴더(method/repro/code.pdf)> <작업 폴더> <출력 pdf>
"""
import os
import sys

from pypdf import PdfReader, PdfWriter

sys.stdout.reconfigure(encoding="utf-8")
OLD, FIG, APP, WORK, OUT = sys.argv[1:6]
os.makedirs(WORK, exist_ok=True)

# build_file3.py 의 목차 부분만 실행(ITEMS·html_to_pdf·목차 생성)
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "build_file3.py"), encoding="utf-8").read()
src = src[:src.index('auc = S["auc"]')]
old_item = '("부록", "분석 방법 및 재현 정보 (제안서 수치의 산출 근거)", "제안팀 분석", "2026", ["@METHOD"])'
assert old_item in src
src = src.replace(old_item, '("부록", "A. 분석 방법·결과 / B. 재현 방법 (제안서 수치의 산출 근거)", "공개 자료 기반 분석", "2026", ["@METHOD"])')
sys.argv = ["x", "", FIG, OUT, WORK]
exec(compile(src, "build_file3_head", "exec"))

old = PdfReader(OLD)
start = [i for i, p in enumerate(old.pages) if "부록. 분석 방법" in (p.extract_text() or "") or "부록 A. 분석 방법" in (p.extract_text() or "")][0]
w = PdfWriter()
for pg in PdfReader(toc).pages:
    w.add_page(pg)
for p in old.pages[1:start]:
    w.add_page(p)
for name in ("method", "repro"):
    for pg in PdfReader(os.path.join(APP, name + ".pdf")).pages:
        w.add_page(pg)
w.add_metadata({"/Title": "파일3 참고문헌 및 참고자료 묶음"})
with open(OUT, "wb") as f:
    w.write(f)
print("저장", OUT, len(w.pages), "쪽 (기존 부록 시작 쪽 인덱스", start, ")")
