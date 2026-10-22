"""파일 3 부록(분석 방법·결과, 재현 방법, 코드 전문) 쪽을 만든다.

입력: 제출_참고자료/결과/*.json·csv (분석코드가 만든 값), 분석코드/*.py, README.md
출력: OUT 폴더의 method.pdf, repro.pdf, code.pdf
실행: python build_appendix.py <제출_참고자료 폴더> <출력 폴더>
"""
import csv
import html
import json
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
PKG, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
CH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
RES = os.path.join(PKG, "결과")
M = json.load(open(os.path.join(RES, "model_summary.json"), encoding="utf-8"))
E = json.load(open(os.path.join(RES, "eda.json"), encoding="utf-8"))
LABEL = {r["assay"]: r["label"] for r in csv.DictReader(open(os.path.join(RES, "assay_A_rates.csv"), encoding="utf-8-sig"))}
ARATE = {r["assay"]: float(r["A_pct"]) for r in csv.DictReader(open(os.path.join(RES, "assay_A_rates.csv"), encoding="utf-8-sig"))}

CSS = """<style>
@page{size:A4;margin:18mm 0 20mm 0}
body{font-family:'Malgun Gothic',sans-serif;color:#111;margin:0}
.pg{padding:0 20mm;page-break-after:always}
h1{font-size:19px;margin:0 0 12px} h2{font-size:14.5px;margin:16px 0 7px}
table{border-collapse:collapse;width:100%;font-size:11.5px;margin:4px 0} td,th{border:1px solid #999;padding:4px 7px;vertical-align:top}
th{background:#eee} p{font-size:12px;line-height:1.65;margin:5px 0} li{font-size:12px;line-height:1.7}
pre{font-family:Consolas,'D2Coding',monospace;font-size:8.3px;line-height:1.28;white-space:pre-wrap;word-break:break-all;margin:0}
.code{padding:12mm 12mm;page-break-after:always} .muted{color:#666;font-size:11px}
</style>"""


def html_to_pdf(name, body):
    hp = os.path.join(OUT, name + ".html")
    pp = os.path.join(OUT, name + ".pdf")
    if os.path.exists(pp):
        os.remove(pp)
    open(hp, "w", encoding="utf-8").write("<!doctype html><html><head><meta charset='utf-8'>" + CSS + "</head><body>" + body + "</body></html>")
    prof = os.path.join(OUT, "prof_" + name)
    p = subprocess.Popen([CH, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--no-pdf-header-footer",
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


auc = M["auc"]
auc_sd = M["auc_sd"]
auc_rows = "".join(f"<tr><td>{LABEL.get(k, k)}</td><td style='text-align:center'>{v:.3f}</td><td style='text-align:center'>±{auc_sd[k]:.3f}</td></tr>"
                   for k, v in sorted(auc.items(), key=lambda x: -x[1]))
sim_rows = "".join(f"<tr><td>{n}</td><td style='text-align:center'>{r:.2f}</td><td style='text-align:center'>{q:.1f} ({lo}~{hi})</td></tr>" for n, r, q, lo, hi in M["sim50"])
st = M["strep"]
mb = M["microbe_bank"]
hm = M["heatmap"]


def hcell(row, col):
    i, j = hm["rows"].index(row), hm["cols"].index(col)
    n = hm["n"][i][j]
    return round(hm["A_pct"][i][j] * n / 100) / n * 100, n  # 저장값의 이중 반올림 방지


kel = hcell("감태속·대황속 (Ecklonia·Eisenia)", "ABTS 항산화")
lam = hcell("다시마목 전체 (미역·다시마 포함)", "ABTS 항산화")
cyp = hcell("사초과 (좀보리사초 등)", "PGE2 항염")
dic = hcell("그물바탕말목", "PGE2 항염")
hit1 = M["sim50"][0][2] / 50
lo1 = M['sim50'][0][3] / 50
hi1 = M['sim50'][0][4] / 50
p_lo = 1 - (1 - lo1) ** 50
base = E["microbe_baseline"]["S.aureus"]
sec = E["sector_pct"]

method = html_to_pdf("method", f"""<div class='pg'><h1>부록 A. 분석 방법과 결과 요약</h1>
<p class='muted'>본문 수치는 모두 공개 자료에서 분석 코드로 다시 계산한 값이며(재현 정보는 부록 B, 결과 표 전체는 부록 C, 코드는 부록 D).</p>
<h2>1. 사용 데이터 (모두 공개 자료, 2026-10-12 수집)</h2>
<ul><li>MBRIS 효능 등급 목록: 화장품 화면 6,015건(7개 시험) / 항균·항염·항암·항바이러스 화면 6,189건(18개 시험) / 대사질환 화면 600건(5개 시험). 일반 추출물 4,112건이 두 화면에 함께 표시되므로 자원번호 기준 중복을 제거한 고유 추출물은 {E['unique_extracts']:,}건이며 시험은 {E['n_assays']}종임</li>
<li>MBRIS 통계현황: 뱅크별 보유 수(2026-10-12 기준)와 뱅크별 누적 분양·기관 유형별 분양(2025-12-31 기준)</li>
<li>MBRIS 해양미생물 바이오뱅크 분양 목록 {mb['total']:,}주(누리집 보유자원 통계 10,522주와 6주 차이가 있으며 분석은 목록에서 조회된 {mb['total']:,}주 기준임) / 해양미세조류 바이오뱅크 목록 / 추출물 뱅크 4,461건 목록(분류체계 포함)</li>
<li>공공데이터포털 국립해양생물자원관 해양생물 채집 공간정보(학명·분류체계) / 해양생물 화장품효능</li>
<li>미생물·미세조류 속(genus)의 계통 정보: NCBI Taxonomy(문·강·목·과), {M['ncbi_genera']}개 속</li></ul>
<h2>2. 방법</h2>
<ul><li>입력: 생물 대분류(세균·균류·미세조류·기타)와 계통(문·강·목·과·속). 종명은 사용하지 않음</li>
<li>모델: 시험별 로지스틱 회귀(클래스 가중치 균형). 목표 변수는 해당 시험 A등급 여부. A등급이 15건 이상인 {M['n_assays']}개 시험만 평가</li>
<li>검증: 종 단위 5겹 교차검증. 같은 종의 추출물이 학습과 평가에 동시에 들어가지 않도록 종을 무작위로 5겹에 배정하며, 배정을 바꿔 {M['reps']}회 반복한 평균을 보고함</li>
<li>연간 분양 한도 모의 비교: 미생물 추출물만 대상으로 교차검증 예측값 상위 50건의 실제 A등급 수(반복 평균과 최소~최대)와 임의 선택 기대값(50 × A등급 비율)을 비교</li>
<li>표시 기준: 같은 속에서 시험된 미생물 종이 3종 이상이고 그 추출물이 10건 이상일 때만 예측 표시</li></ul>
<h2>3. 문제 진단 EDA</h2><table><tr><th>뱅크</th><th>개설</th><th>보유</th><th>누적 분양</th><th>1천 점당 연간 분양</th></tr>
<tr><td>미세조류</td><td>2020</td><td>414</td><td>194</td><td>{E['bank_rate_per_1000_per_year']['미세조류']}</td></tr>
<tr><td>추출물</td><td>2017</td><td>4,461</td><td>1,350</td><td>{E['bank_rate_per_1000_per_year']['추출물']}</td></tr>
<tr><td>미생물</td><td>2018</td><td>10,522</td><td>453</td><td>{E['bank_rate_per_1000_per_year']['미생물']}</td></tr>
<tr><td>대사질환</td><td>2025</td><td>600</td><td>2</td><td>{E['bank_rate_per_1000_per_year']['대사질환']}</td></tr>
<tr><td>유전자원</td><td>2019</td><td>12,199</td><td>253</td><td>{E['bank_rate_per_1000_per_year']['유전자원']}</td></tr>
<tr><td>화장품</td><td>2022</td><td>1,900</td><td>8</td><td>{E['bank_rate_per_1000_per_year']['화장품']}</td></tr>
<tr><td>항생제</td><td>2023</td><td>2,219</td><td>5</td><td>{E['bank_rate_per_1000_per_year']['항생제']}</td></tr></table>
<p>산출: 누적 분양(2025년 말) ÷ 보유 수(2026년 10월) ÷ 운영 연수(개설 연도~2025). 보유 수는 현재값이므로 과거 보유가 적었던 뱅크의 활용도는 다소 낮게 계산됨. 효능 정보 유무와 분양률의 인과관계는 이 자료로 판단하지 않음(일반 추출물에도 효능 등급이 있어 경로가 겹침).</p>
<p>시험 {E['n_assays']}종의 A등급 비율 중앙값 {E['A_pct_median']:.1f}%, 최대 {E['A_pct_max'][1]:.1f}%({E['A_pct_max'][0]}). 살모넬라 {ARATE['Salmonella']:.2f}%, 대장균 {ARATE['E.coli']:.2f}%. 누적 분양 {E['sector_total']:,}건 중 학교 {sec['학교']}%(1,565건), 연구소 {sec['연구소']}%(437건), 기업 {sec['기업']}%(263건).</p>
<p>이용자 체감 지표: 미생물 추출물의 황색포도상구균 항균 A등급 비율은 {base['A_pct']:.2f}%(n={base['n']:,})이므로 연간 한도 50주를 임의로 고르면 기대 A등급은 {base['expected_A_in_50']:.2f}건, 1건 이상 얻을 확률은 1-(1-{base['A_pct'] / 100:.4f})^50 = {E['P_at_least_1_A_random50'] * 100:.0f}%임. 예측 상위 50주의 10회 반복 적중은 평균 {M['sim50'][0][2]:.1f}건({hit1 * 100:.0f}%), 최소 {M['sim50'][0][3]}건({lo1 * 100:.0f}%)~최대 {M['sim50'][0][4]}건({hi1 * 100:.0f}%)이며, 1건 이상 얻을 확률은 평균 기준 1-(1-{hit1:.2f})^50 > 99.9%, 최소 기준 1-(1-{lo1:.2f})^50 = {p_lo * 100:.1f}%임. 첫 A등급까지 기대 신청 횟수는 회당 20점 기준 1/(1-(1-{base['A_pct'] / 100:.4f})^20) = {E['first_A_expected_requests_20per']}회.</p>
<p>표시 가능 범위: 해양미생물 분양 목록 {mb['total']:,}주 중 효능 시험이 이루어진 종에 속하지 않는 균주 {mb['untested']:,}주(분양 가능 {mb['untested_available']:,}주). 이 중 표시 기준(같은 속 시험 종 3종 이상, 추출물 10건 이상)을 충족하는 균주 {mb['display_ok']:,}주({mb['display_ok_pct_of_untested']}%).</p>
<p>인력·비용: 데이터 정비 2인월 + 화면·추천 개발 4인월(응용SW개발자 월 7,754,124원) + 사업관리 1인월(IT기획자 월 11,853,218원) = 직접인건비 58,377,962원. 2026년 적용 SW기술자 평균임금 기준.</p>
<h2>4. 결과 요약</h2>
<table style='width:100%'><tr><th>항목</th><th>결과</th></tr><tr><td>예측 정확도(AUC)</td><td>황색포도상구균 {M['auc']['S.aureus']:.3f} · PGE2 {M['auc']['PGE2']:.3f} · DPPH {M['auc']['DPPH']:.3f} · 평가한 {M['n_assays']}개 시험 평균 {M['auc_mean']:.3f} (시험별 값은 부록 C 표 1)</td></tr><tr><td>50주 모의 비교</td><td>황색포도상구균 임의 {M['sim50'][0][1]:.2f}건 → 예측 상위 평균 {M['sim50'][0][2]:.1f}건({M['sim50'][0][3]}~{M['sim50'][0][4]}건) · ABTS는 {M['sim50'][4][1]:.2f}건 → {M['sim50'][4][2]:.1f}건으로 개선 없음 (전체는 부록 C 표 3)</td></tr></table>
<p>시험별 변동은 A등급 수가 적은 시험일수록 큼(예: 바실러스 세레우스).</p>

<p>방선균(Streptomyces): 추출물 {st['extracts']}건 / {st['species']}종 중 황색포도상구균 A등급 비율 {st['A_rate'] * 100:.1f}% (미생물 추출물 평균 {st['micro_base'] * 100:.2f}%, {st['A_rate'] / st['micro_base']:.0f}배).</p>
<p>계통-효능 지도: 감태속·대황속(Ecklonia·Eisenia) 추출물 {kel[1]}건의 ABTS 항산화 A등급 비율 {kel[0]:.0f}%, 다시마목 전체(미역·다시마 포함) {lam[1]}건은 {lam[0]:.0f}%. 사초과 PGE2 항염 {cyp[0]:.0f}%(n={cyp[1]}), 그물바탕말목 {dic[0]:.0f}%(n={dic[1]}). 전체 값은 부록 C 표 2에 수록.</p>
<h2>5. 한계</h2>
<ul><li>효능 등급은 3단계이며 고정 농도의 시험관 내 결과임</li><li>같은 생물이 뱅크별로 다른 번호로 중복 등록되어 있어 검증은 종 단위로 분리함</li>
<li>같은 종도 채집 시기에 따라 등급이 달라짐. 예: 괭생이모자반(Sargassum horneri) 70% 에탄올 추출물의 PGE2 항염 등급이 2021년 5월 채집분은 C, 6월 채집분은 A (MBRIS 추출물 상세 정보 30건, 부록 B 자료 목록)</li>
<li>예측 상위 50주의 적중 수는 교차검증에서 종을 겹에 배정하는 방식에 따라 달라지므로 {M['reps']}회 반복의 평균과 범위로 표기함</li>
<li>같은 목이라도 속에 따라 효능이 달라 계통 단위를 세분하여 해석함(예: 다시마목 전체와 감태속·대황속의 차이)</li>
<li>암세포 시험 A등급은 일반 세포독성일 수 있어 서비스 근거에서 제외함</li></ul></div>""")
print("method.pdf", method)

# ── 재현 방법 + 코드 전문 ─────────────────────────────────
readme = open(os.path.join(PKG, "README.md"), encoding="utf-8").read()
repro = html_to_pdf("repro", f"<div class='pg'><h1>부록 B. 재현 방법</h1><pre style='font-size:11px;line-height:1.55'>{html.escape(readme)}</pre></div>")
code_dir = os.path.join(PKG, "분석코드")
files = [os.path.join(code_dir, f) for f in ("common.py", "figstyle.py", "01_eda_분양현황과A등급.py", "02_계통기반예측.py")]
files += [os.path.join(code_dir, "수집", f) for f in ("scrape_mbris.py", "ncbi_lineage.py")]
parts = []
for fp in files:
    rel = os.path.relpath(fp, PKG).replace("\\", "/")
    parts.append(f"<div class='code'><h2 style='font-size:13px'>부록 C. 코드 전문 — {html.escape(rel)}</h2><pre>{html.escape(open(fp, encoding='utf-8').read())}</pre></div>")
code = html_to_pdf("code", "".join(parts))
print("repro.pdf", repro, "| code.pdf", code)
