"""파일 3 부록 B(재현 정보·데이터 목록), C(결과 표), D(분석 코드)를 PDF로 만든다.

실행: python build_appendix_bcd.py <제출_참고자료 폴더> <출력 폴더>
출력: appB.pdf, appC.pdf, appD.pdf
"""
import csv
import html
import json
import os
import shutil
import subprocess
import sys
import time

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

sys.stdout.reconfigure(encoding="utf-8")
PKG, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
CH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
RES, DATA, CODE = (os.path.join(PKG, d) for d in ("결과", "데이터", "분석코드"))
M = json.load(open(os.path.join(RES, "model_summary.json"), encoding="utf-8"))
E = json.load(open(os.path.join(RES, "eda.json"), encoding="utf-8"))

CSS = """<style>
@page{size:A4;margin:16mm 15mm 15mm 15mm}
body{font-family:'Malgun Gothic',sans-serif;color:#111;margin:0;font-size:10.5pt}
h1{font-size:15pt;margin:0 0 4px} .sub{color:#666;font-size:8.5pt;margin:0 0 10px}
h2{font-size:11.5pt;margin:14px 0 6px}
.sq{margin:8px 0 3px;font-weight:700;font-size:10.5pt}
.bo{margin:2px 0 2px 14px;text-indent:-12px;line-height:1.55;font-size:9.6pt}
.bd{margin:1px 0 1px 30px;text-indent:-10px;line-height:1.5;font-size:9.2pt;color:#333}
table{border-collapse:collapse;width:100%;font-size:8.4pt;margin:4px 0 6px}
th,td{border:1px solid #b9b8b1;padding:3px 6px;vertical-align:middle}
th{background:#eef3fa;font-weight:700} td.c{text-align:center} td.r{text-align:right}
tr{page-break-inside:avoid}
.file{margin:0 0 6px;padding:6px 9px;background:#f4f6f9;border-left:4px solid #2a78d6;font-size:9pt;page-break-after:avoid}
.file b{font-size:10pt}
""" + HtmlFormatter(style="friendly").get_style_defs(".code") + """
.code{border:1px solid #dde3ea;border-radius:3px;padding:5px 8px;margin:0 0 12px;background:#fbfcfd}
.code pre{margin:0;font-family:Consolas,'Malgun Gothic',monospace;font-size:7.2pt;line-height:1.28;white-space:pre-wrap}
.code pre span{font-family:inherit;line-height:inherit}
.code .linenos{color:#9aa3ad;padding-right:8px;background:transparent}
</style>"""


def to_pdf(name, body):
    hp, pp = os.path.join(OUT, name + ".html"), os.path.join(OUT, name + ".pdf")
    if os.path.exists(pp):
        os.remove(pp)
    open(hp, "w", encoding="utf-8").write("<!doctype html><html><head><meta charset='utf-8'>" + CSS + "</head><body>" + body + "</body></html>")
    prof = os.path.join(OUT, "prof_" + name)
    subprocess.Popen([CH, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--no-pdf-header-footer",
                      f"--print-to-pdf={pp}", "file:///" + hp.replace("\\", "/")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 90 and not (os.path.exists(pp) and os.path.getsize(pp) > 0):
        time.sleep(1)
    time.sleep(2)
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    f"Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object {{ $_.CommandLine -like '*prof_{name}*' }} | "
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(prof, ignore_errors=True)
    return pp


def rows_of(fn):
    p = os.path.join(DATA, fn)
    if fn.endswith(".json"):
        return len(json.load(open(p, encoding="utf-8")))
    for enc in ("utf-8-sig", "cp949"):
        try:
            with open(p, encoding=enc) as f:
                n = sum(1 for _ in csv.reader(f))
            return n - (1 if fn == "collect_taxonomy.csv" else 0)
        except Exception:
            continue


# ── 부록 B. 재현 정보와 데이터 목록 ────────────────────────
DATA_ROWS = [
    ("efficacy_cosmetic.csv", "화장품자원 효능 뱅크 표(시험 7종: 티로시나제·DOPA·콜라게나아제·엘라스타제·DPPH·ABTS·ROS)", "MBRIS extractBeautyBank", "건"),
    ("efficacy_antibac_inflam_cancer_virus.csv", "항생제자원 효능 뱅크 표(시험 18종: 항균 6·항염 2·항암 7·항바이러스 3)", "MBRIS extractAntiBac", "건"),
    ("efficacy_metabolic.csv", "대사질환자원 효능 뱅크 표(시험 5종: DPP4·α-글루코시다제·Oil Red O·중성지방·ACE)", "MBRIS extractMtblsmDiss", "건"),
    ("bank_microbe.csv", "해양미생물 바이오뱅크 분양 목록(자원번호·학명·분양 상태)", "MBRIS 미생물 뱅크", "주"),
    ("bank_microalgae.csv", "해양미세조류 바이오뱅크 목록", "MBRIS 미세조류 뱅크", "주"),
    ("bank_extract.csv", "추출물 뱅크 목록(자원번호·분류체계·채집지·채집일)", "MBRIS 추출물 뱅크", "건"),
    ("collect_taxonomy.csv", "학명별 분류체계(채집 공간정보에서 고유 학명만 추림)", "공공데이터포털 해양생물 채집 공간정보", "종"),
    ("ncbi_genus_lineage.json", "미생물·미세조류 속의 문·강·목·과", "NCBI Taxonomy E-utilities", "속"),
    ("detail_sargassum_horneri.json", "괭생이모자반 추출물 상세 정보(채집일·용매·시험별 등급)", "MBRIS 추출물 상세 조회", "건"),
]
drows = "".join(f"<tr><td>{fn}</td><td>{desc}</td><td>{src}</td><td class='r'>{rows_of(fn):,}{u}</td></tr>" for fn, desc, src, u in DATA_ROWS)
CODE_FILES = [("common.py", "공통: 공개 자료 읽기, 학명 정리, 계통 정보 만들기"),
              ("figstyle.py", "그림 공통 서식"),
              ("01_eda_분양현황과A등급.py", "분양 활용도, 시험별 A등급 비율, 미생물 기준선, 방선균 비교, 그림 1"),
              ("02_계통기반예측.py", "시험별 AUC, 계통 깊이별 AUC, 50주 모의 비교, 계통-효능 지도, 미시험 미생물 현황"),
              ("03_그림생성.py", "그림 2·3 (02번 결과를 읽어 그림)"),
              ("수집/scrape_mbris.py", "MBRIS 효능 뱅크 표 수집(수집 방법 기록)"),
              ("수집/ncbi_lineage.py", "NCBI Taxonomy 계통 수집(수집 방법 기록)")]
crows = "".join(f"<tr><td>{f}</td><td>{d}</td><td class='r'>{sum(1 for _ in open(os.path.join(CODE, f), encoding='utf-8'))}줄</td></tr>" for f, d in CODE_FILES)
b = f"""<h1>부록 B. 재현 정보와 데이터 목록</h1>
<p class='sub'>본문과 부록 A의 모든 수치는 아래 공개 자료와 부록 D의 코드로 다시 계산할 수 있음</p>
<div class='sq'>□ 재현 방법</div>
<div class='bo'>○ 환경: Python 3.12, pandas 3.0, numpy 2.4, scikit-learn 1.8, matplotlib 3.10 (그림에는 한글 글꼴 필요)</div>
<div class='bo'>○ 순서: 01_eda_분양현황과A등급.py → 02_계통기반예측.py(약 10분) → 03_그림생성.py</div>
<div class='bd'>- 경로는 코드 위치 기준 상대 경로이며 결과는 결과 폴더에 저장됨</div>
<div class='bd'>- 난수는 종을 교차검증 겹에 배정할 때만 쓰며 시드 0~9로 고정함</div>
<div class='bo'>○ 재현 확인: 코드와 자료를 새 폴더에 옮겨 처음부터 다시 실행한 결과가 제출 수치·그림과 같음을 확인함</div>
<div class='sq'>□ 사용한 공개 자료 (모두 2026-10-12 수집)</div>
<table><tr><th style='width:27%'>파일</th><th>내용</th><th style='width:22%'>출처</th><th style='width:11%'>규모</th></tr>{drows}</table>
<div class='bo'>○ MBRIS 통계현황 수치(보유자원 2026.10.12., 분양현황 2025.12.31.)는 01번 코드에 상수로 적음</div>
<div class='bo'>○ 효능 표의 열 순서는 MBRIS 표 머리글 순서와 같으며 시험 이름은 common.py의 ASSAYS에 있음</div>
<div class='sq'>□ 분석 코드 구성 (전문은 부록 D)</div>
<table><tr><th style='width:30%'>파일</th><th>역할</th><th style='width:10%'>분량</th></tr>{crows}</table>
<div class='sq'>□ 계통 정보 규칙</div>
<div class='bo'>○ 출처 우선순위: 추출물 뱅크 목록의 분류체계 → 채집 공간정보 분류체계 → 같은 속의 분류체계. 미생물·미세조류는 NCBI Taxonomy</div>
<div class='bo'>○ 계통-효능 지도의 어류·무척추동물은 문·강 수준 이름 목록으로 묶음(02번 코드의 FISH, INVERT)</div>
"""
pb = to_pdf("appB", b)

# ── 부록 C. 결과 표 ───────────────────────────────────────
ar = list(csv.DictReader(open(os.path.join(RES, "assay_A_rates.csv"), encoding="utf-8-sig")))
grp = {"B": "화장품", "A": "항균·항염·항암·항바이러스", "M": "대사질환"}
auc = M["auc"]
t1 = "".join(f"<tr><td>{grp[r['table']]}</td><td>{r['label']}</td><td class='r'>{int(r['n_graded']):,}</td><td class='r'>{float(r['A_pct']):.2f}%</td>"
             f"<td class='r'>{auc[r['assay']]:.3f}</td></tr>" if r["assay"] in auc else
             f"<tr><td>{grp[r['table']]}</td><td>{r['label']}</td><td class='r'>{int(r['n_graded']):,}</td><td class='r'>{float(r['A_pct']):.2f}%</td><td class='c'>-</td></tr>"
             for r in ar)
hm = M["heatmap"]
head = "".join(f"<th>{c}<br><span style='font-weight:400'>평균 {a:.0f}%</span></th>" for c, a in zip(hm["cols"], hm["avg"]))
body_rows = ""
for rname, vals, ns in zip(hm["rows"], hm["A_pct"], hm["n"]):
    cells = "".join(f"<td class='c'>{round(v * n / 100) / n * 100:.0f}%<br><span style='color:#777'>n={n}</span></td>" if v is not None
                    else "<td class='c' style='color:#999'>자료 부족</td>" for v, n in zip(vals, ns))
    body_rows += f"<tr><td>{rname}</td>{cells}</tr>"
sim = "".join(f"<tr><td>{n}</td><td class='r'>{r:.2f}</td><td class='r'>{q:.1f}</td><td class='c'>{lo}~{hi}</td></tr>" for n, r, q, lo, hi in M["sim50"])
mb = M["microbe_bank"]
c = f"""<h1>부록 C. 결과 표</h1>
<p class='sub'>02번 코드 실행 결과. AUC는 종 단위 5겹 교차검증 {M['reps']}회 반복 평균이며, A등급이 15건 미만인 시험은 평가하지 않음(-)</p>
<div class='sq'>□ 표 1. 시험 30종의 A등급 비율과 예측 정확도</div>
<table><tr><th>효능 뱅크</th><th>시험</th><th>등급 있는 추출물</th><th>A등급 비율</th><th>AUC</th></tr>{t1}</table>
<div class='bo'>○ A등급 비율 중앙값 {E['A_pct_median']:.1f}%, 평가한 {M['n_assays']}개 시험의 평균 AUC {M['auc_mean']:.3f}</div>
<div class='sq' style='page-break-before:always'>□ 표 2. 계통-효능 지도 전체 값 (A등급 비율과 추출물 수)</div>
<table><tr><th>계통</th>{head}</tr>{body_rows}</table>
<div class='bo'>○ 추출물이 10건 미만인 칸은 '자료 부족'으로 표시함</div>
<div class='sq'>□ 표 3. 연간 분양 한도 50주 모의 비교 (미생물 추출물)</div>
<table><tr><th>목표 효능</th><th>임의 50건 기대 A</th><th>예측 상위 50건 실제 A (평균)</th><th>최소~최대 ({M['reps']}회)</th></tr>{sim}</table>
<div class='sq'>□ 표 4. 해양미생물 바이오뱅크 미시험 현황</div>
<table><tr><th>분양 목록</th><th>효능 시험된 종에 속하지 않는 균주</th><th>그중 분양 가능</th><th>표시 기준 충족(같은 속 시험 종 3종 이상·추출물 10건 이상)</th></tr>
<tr><td class='r'>{mb['total']:,}주</td><td class='r'>{mb['untested']:,}주</td><td class='r'>{mb['untested_available']:,}주</td><td class='r'>{mb['display_ok']:,}주 ({mb['display_ok_pct_of_untested']}%)</td></tr></table>
"""
pc = to_pdf("appC", c)

# ── 부록 D. 분석 코드 ─────────────────────────────────────
fmt = HtmlFormatter(style="friendly", linenos="inline", cssclass="code")
parts = ["<h1>부록 D. 분석 코드</h1><p class='sub'>부록 B의 재현 방법에 쓰인 코드 전문. 수집 코드 2개는 자료를 모은 방법을 기록하기 위한 것임</p>"]
for f, desc in CODE_FILES:
    src = open(os.path.join(CODE, f), encoding="utf-8").read()
    n = src.rstrip("\n").count("\n") + 1
    parts.append(f"<div class='file'><b>{html.escape(f)}</b> &nbsp;·&nbsp; {html.escape(desc)} &nbsp;·&nbsp; {n}줄</div>"
                 + highlight(src, PythonLexer(), fmt))
pd_ = to_pdf("appD", "".join(parts))
print("B", pb, "| C", pc, "| D", pd_)
