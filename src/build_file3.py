"""파일3: 참고문헌·참고자료 묶음 PDF (목차 + 문헌 요약 + 화면 캡처 + 분석 방법)."""
import json, os, re, subprocess, sys, time, shutil, html
from pypdf import PdfReader, PdfWriter

sys.stdout.reconfigure(encoding="utf-8")
CAP, FIG, OUT, WORK = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(WORK, exist_ok=True)
S = json.load(open(os.path.join(FIG, "_summary.json"), encoding="utf-8"))
CH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def abstract(pmcid):
    import urllib.request
    u = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=PMCID:{pmcid}&resultType=core&format=json"
    d = json.loads(urllib.request.urlopen(u, timeout=60).read().decode("utf-8"))["resultList"]["result"][0]
    return d


CSS = """<style>
body{font-family:'Malgun Gothic',sans-serif;color:#111;margin:0}
.pg{padding:22mm 20mm;page-break-after:always}
h1{font-size:20px;margin:0 0 14px} h2{font-size:15px;margin:18px 0 8px}
table{border-collapse:collapse;width:100%;font-size:12px} td,th{border:1px solid #999;padding:6px 8px;vertical-align:top}
th{background:#eee} .muted{color:#666;font-size:11px} p{font-size:12.5px;line-height:1.7}
.box{border:1px solid #bbb;padding:10px 12px;font-size:12px;line-height:1.7;background:#fafafa}
li{font-size:12.5px;line-height:1.75}
</style>"""

ITEMS = [
    ("1", "해양바이오뱅크 소개·통계현황·분양 안내·공지·Q&A·성과현황·검색 화면 (화면 캡처)", "국립해양생물자원관 MBRIS", "2026",
     ["01b_MBRIS_뱅크소개", "01e_MBRIS_통계_보유자원", "01f_MBRIS_통계_분양현황", "01_MBRIS_자원분양현황", "01c_MBRIS_공지_분양접수기간_202608", "01d_MBRIS_공지_누리집개편_202601",
      "01g_MBRIS_QnA목록", "02_MBRIS_분양안내", "03_MBRIS_성과현황", "04_MBRIS_화장품효능뱅크검색", "05_MBRIS_미생물뱅크검색"]),
    ("2", "Mbio-Bridge 해양바이오 주요소재 DB·기업수요 매칭 (화면 캡처)", "국립해양생물자원관", "2026", ["06_MbioBridge_주요소재DB", "07_MbioBridge_기업수요매칭"]),
    ("3", "Phylogenies reveal predictive power of traditional medicine in bioprospecting", "PNAS 109(39)", "2012", ["@PMC3465383"]),
    ("4", "BacDive in 2025: the core database for prokaryotic strain data", "Nucleic Acids Research 53(D1)", "2025", ["@PMC11701647"]),
    ("5", "NCI Program for Natural Products Discovery Prefractionated Library", "미국 국립암연구소", "2023", ["10_NCI_NPNPD"]),
    ("6", "섬·연안 생물 유용물질 선별 빨라진다", "데일리안", "2026", ["11_데일리안_호남권AI"]),
    ("7", "2026년 적용 SW기술자 평균임금 공표", "한국인공지능·소프트웨어산업협회", "2025", ["16_KOSA_2026평균임금"]),
    ("8", "[2026 국감] 해양바이오 연구과제 31건 중 상용화 7건", "푸드투데이", "2026", ["12_푸드투데이_국감상용화"]),
    ("9", "AI로 바이오 소재 발굴·국산화 가속…국가 바이오데이터 700만 건 구축", "아시아경제", "2025", ["13_아시아경제_바이오데이터"]),
    ("10", "해양생물 채집 공간정보 / 해양생물 화장품효능", "공공데이터포털", "2025", ["14_공공데이터_채집공간정보", "15_공공데이터_화장품효능"]),
    ("부록", "분석 방법 및 재현 정보 (제안서 수치의 산출 근거)", "제안팀 분석", "2026", ["@METHOD"]),
]


def html_to_pdf(name, body):
    hp = os.path.join(WORK, name + ".html"); pp = os.path.join(WORK, name + ".pdf")
    open(hp, "w", encoding="utf-8").write("<!doctype html><html><head><meta charset='utf-8'>" + CSS + "</head><body>" + body + "</body></html>")
    prof = os.path.join(WORK, "prof_" + name)
    p = subprocess.Popen([CH, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}",
                          "--no-pdf-header-footer", f"--print-to-pdf={pp}", "file:///" + hp.replace("\\", "/")],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 60 and not (os.path.exists(pp) and os.path.getsize(pp) > 0):
        time.sleep(1)
    time.sleep(2)
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    f"Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object {{ $_.CommandLine -like '*prof_{name}*' }} | "
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(prof, ignore_errors=True)
    return pp


# 목차
rows = "".join(f"<tr><td style='text-align:center'>{n}</td><td>{html.escape(t)}</td><td>{html.escape(s)}</td><td style='text-align:center'>{y}</td></tr>"
               for n, t, s, y, _ in ITEMS)
toc = html_to_pdf("00_목차", f"""<div class='pg'><h1>[파일 3] 참고문헌 및 참고자료 묶음</h1>
<p class='muted'>부문 3 활용 성과 촉진 아이디어 제안서 「효능 내비게이터」 근거 자료 · 화면 캡처 기준일 2026-10-12</p>
<table><tr><th style='width:9%'>연번</th><th>자료명</th><th style='width:27%'>출처</th><th style='width:12%'>발행연도</th></tr>{rows}</table>
<p class='muted'>※ 학술 논문 2건은 원문 사이트의 자동 접근 차단으로 서지 정보와 초록을 정리하여 수록함. 원문은 DOI로 확인 가능.</p></div>""")


def paper_page(pmcid, no):
    d = abstract(pmcid)
    ab = re.sub(r"<[^>]+>", "", d.get("abstractText", ""))
    j = d.get("journalInfo", {})
    cite = f"{d.get('authorString', '')} ({d.get('pubYear')}). {d['title']} {j.get('journal', {}).get('title', '')} {j.get('volume', '')}({j.get('issue', '')}):{d.get('pageInfo', '')}. doi:{d.get('doi')}"
    return html_to_pdf(f"paper_{pmcid}", f"""<div class='pg'><h1>참고자료 {no}. {html.escape(d['title'])}</h1>
<div class='box'><b>서지 정보</b><br>{html.escape(cite)}<br>PMCID: {pmcid} · https://doi.org/{d.get('doi')}</div>
<h2>초록 (원문)</h2><p>{html.escape(ab)}</p></div>""")


auc = S["auc"]; sim = S["sim50"]; st = S["strep"]
auc_rows = "".join(f"<tr><td>{k}</td><td style='text-align:center'>{v:.3f}</td></tr>" for k, v in sorted(auc.items(), key=lambda x: -x[1]))
sim_rows = "".join(f"<tr><td>{n}</td><td style='text-align:center'>{r:.2f}</td><td style='text-align:center'>{q}</td></tr>" for n, r, q in sim)
method = html_to_pdf("method", f"""<div class='pg'><h1>부록. 분석 방법 및 재현 정보</h1>
<h2>1. 사용 데이터 (모두 공개 자료, 2026-10-12 수집)</h2>
<ul><li>MBRIS 효능 등급 목록: 화장품 화면 6,015건(7개 시험) / 항균·항염·항암·항바이러스 화면 6,189건(18개 시험) / 대사질환 화면 600건(5개 시험). 일반 추출물 4,112건이 두 화면에 함께 표시되므로 중복을 제거한 고유 추출물은 8,808건임</li><li>MBRIS 통계현황: 뱅크별 보유 수(2026-10-12 기준)와 뱅크별 누적 분양·기관 유형별 분양(2025-12-31 기준)</li>
<li>MBRIS 해양미생물 바이오뱅크 분양 목록 10,516주(누리집 보유자원 통계 10,522주와 6주 차이가 있으며, 효능 예측 분석은 목록에서 조회된 10,516주 기준임) / 해양미세조류 바이오뱅크 421주 목록 / 추출물 뱅크 4,461건 목록</li>
<li>공공데이터포털 국립해양생물자원관 해양생물 채집 공간정보 325,412건(분류체계 포함) / 해양생물 화장품효능 1,328건</li>
<li>미생물·미세조류 속(genus)의 계통 정보: NCBI Taxonomy (문·강·목·과), {S.get('ncbi_genera', 0)}개 속</li></ul>
<h2>2. 방법</h2>
<ul><li>입력: 생물 대분류(7개 그룹)와 계통(문·강·목·과·속). 종명은 사용하지 않음</li>
<li>모델: 시험별 로지스틱 회귀(클래스 가중치 균형). 목표 변수는 해당 시험 A등급 여부</li>
<li>검증: 종 단위 5겹 교차검증(GroupKFold). 같은 종의 추출물이 학습과 평가에 동시에 들어가지 않도록 분리하여 처음 보는 종에 대한 예측력을 측정</li>
<li>연간 분양 한도 모의 비교: 미생물 추출물만 대상으로 교차검증 예측값 상위 50건의 실제 A등급 수와 임의 선택 기대값(50 × A등급 비율)을 비교</li>
<li>근거 기준: 같은 속에서 시험된 종 3종 이상 그리고 추출물 10건 이상일 때만 예측 표시</li></ul>
<h2>3. 문제 진단 EDA</h2><table><tr><th>뱅크</th><th>개설</th><th>보유</th><th>누적 분양</th><th>1천 점당 연간 분양</th></tr><tr><td>미세조류</td><td>2020</td><td>414</td><td>194</td><td>78.1</td></tr><tr><td>추출물</td><td>2017</td><td>4,461</td><td>1,350</td><td>33.6</td></tr><tr><td>미생물</td><td>2018</td><td>10,522</td><td>453</td><td>5.4</td></tr><tr><td>대사질환</td><td>2025</td><td>600</td><td>2</td><td>3.3</td></tr><tr><td>유전자원</td><td>2019</td><td>12,199</td><td>253</td><td>3.0</td></tr><tr><td>화장품</td><td>2022</td><td>1,900</td><td>8</td><td>1.1</td></tr><tr><td>항생제</td><td>2023</td><td>2,219</td><td>5</td><td>0.8</td></tr></table><p>산출: 누적 분양(2025년 말) ÷ 보유 수(2026년 10월) ÷ 운영 연수(개설 연도~2025). 보유 수는 현재값이므로 과거 보유가 적었던 뱅크의 활용도는 다소 낮게 계산됨. 효능 정보 유무와 분양률의 인과관계는 이 자료로 판단하지 않음(일반 추출물에도 효능 등급이 있어 경로가 겹침).</p><p>시험 30종의 A등급 비율 중앙값 {S['eda']['median_A']}% (최소 0.0% 살모넬라 / 최대 13.5% 지방축적 억제). 뱅크 누적 분양 2,265건 중 기업 263건(11.6%) · 학교 1,565건 · 연구소 437건.</p><p>이용자 체감 지표: 연간 한도 50주를 임의로 고르면 황색포도상구균 항균 A등급을 1건 이상 얻을 확률은 1-(1-0.009)^50 = 36%이고 예측 상위 50주(실측 적중 6건, 12%)를 쓰면 1-(1-0.12)^50 > 99%임. 첫 A등급까지 기대 신청 횟수는 회당 20점 기준 1/(1-(1-0.009)^20) = 6.0회.</p><p>표시 가능 범위: 미시험 균주 4,610주 중 근거 기준(같은 속 시험 종 3종 이상, 추출물 10건 이상)을 충족하는 균주 1,866주(40.5%).</p><p>인력·비용: 데이터 정비 2인월 + 화면·추천 개발 4인월(응용SW개발자 월 7,754,124원) + 사업관리 1인월(IT기획자 월 11,853,218원) = 직접인건비 58,377,962원. 2026년 적용 SW기술자 평균임금 기준.</p><h2>4. 결과 요약</h2>
<table style='width:60%'><tr><th>시험</th><th>AUC</th></tr>{auc_rows}</table>
<p>시험 {S['n_assays']}개 평균 AUC {S['auc_mean']:.3f}</p>
<table><tr><th>목표 효능 (미생물 추출물)</th><th>임의 50건 기대 A</th><th>예측 상위 50건 실제 A</th></tr>{sim_rows}</table>
<p>방선균(Streptomyces): 추출물 {st['extracts']}건 / {st['species']}종 중 황색포도상구균 A등급 비율 {st['A_rate'] * 100:.1f}% (미생물 추출물 평균 {st['micro_base'] * 100:.2f}%)</p>
<h2>5. 한계</h2>
<ul><li>효능 등급은 3단계이며 고정 농도의 시험관 내 결과임</li><li>같은 생물이 뱅크별로 다른 번호로 중복 등록되어 있어 검증은 종 단위로 분리함</li>
<li>암세포 시험 A등급은 일반 세포독성일 수 있어 서비스 근거에서 제외함</li></ul></div>""")

w = PdfWriter()
for path in [toc]:
    for pg in PdfReader(path).pages: w.add_page(pg)
for n, t, s, y, files in ITEMS:
    for f in files:
        if f.startswith("@PMC"):
            path = paper_page(f[1:], n)
        elif f == "@METHOD":
            path = method
        else:
            path = os.path.join(CAP, f + ".pdf")
        r = PdfReader(path)
        lim = {"01g": 3, "16": 2, "01e": 2, "01f": 2, "01b": 2, "01c": 1, "01d": 1, "01": 2, "02": 3, "03": 1, "04": 2, "05": 1, "06": 1, "07": 1, "10": 2, "11": 2, "12": 2, "13": 2, "14": 1, "15": 1}.get(os.path.basename(path)[:3] if os.path.basename(path)[2] in "bcdefg" else os.path.basename(path)[:2], 3)
        for pg in r.pages[:lim]:
            w.add_page(pg)
w.add_metadata({"/Title": "파일3 참고문헌 및 참고자료 묶음"})
with open(OUT, "wb") as f:
    w.write(f)
print("saved", OUT, len(w.pages), "pages", os.path.getsize(OUT) // 1024, "KB")
