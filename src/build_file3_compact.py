"""파일 3(참고문헌 및 참고자료 묶음) 압축판 조립.

- 새로 캡처한 MBRIS 화면(CAP)과 기존 파일 3의 문헌·기사 쪽(OLD)에서 필요한 부분만 잘라 쪽당 2~4건씩 배치
- 개인 연락처(이메일·전화)는 가림
실행: python build_file3_compact.py <기존 파일3.pdf> <캡처 폴더> <부록 폴더(method.pdf)> <출력 pdf>
"""
import io
import os
import re
import sys

import fitz
from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter

sys.stdout.reconfigure(encoding="utf-8")
OLD, CAP, APP, OUT = sys.argv[1:5]
WORK = os.path.join(os.path.dirname(OUT), "compact_work")
os.makedirs(WORK, exist_ok=True)
FONT = r"C:\Windows\Fonts\malgun.ttf"
FONTB = r"C:\Windows\Fonts\malgunbd.ttf"
src = fitz.open(OLD)
W, H = 595, 842
M = 36  # 여백


def redact(doc, pno, pats):
    """쪽 안의 이메일·전화번호 같은 개인 연락처를 가린다."""
    p = doc[pno]
    for w in p.get_text("words"):
        if any(re.search(x, w[4]) for x in pats):
            p.add_redact_annot(fitz.Rect(w[:4]) + (-1, -1, 1, 1), fill=(1, 1, 1))
    p.apply_redactions()


PATS = [r"@[A-Za-z0-9.-]+\.(kr|com|net)", r"^\d{2,3}-\d{3,4}-\d{4}$", r"^\(cju"]
for pno in (27, 29, 31, 32, 33):
    redact(src, pno, PATS)
# 본문 제목행의 담당자·전화·이메일 값(KOSA)도 가림
for w in src[29].get_text("words"):
    if w[4] in ("김경희", "02-2188-6908"):
        src[29].add_redact_annot(fitz.Rect(w[:4]) + (-1, -1, 1, 1), fill=(1, 1, 1))
src[29].apply_redactions()

out = fitz.open()


def new_page(title, sub=""):
    pg = out.new_page(width=W, height=H)
    pg.insert_font("kr", FONT)
    pg.insert_font("krb", FONTB)
    pg.insert_text((M, 46), title, fontname="krb", fontsize=14)
    if sub:
        pg.insert_text((M, 62), sub, fontname="kr", fontsize=8.5, color=(0.4, 0.4, 0.4))
    return pg


def caption(pg, y, text, size=8.6):
    pg.insert_text((M, y), text, fontname="krb", fontsize=size)


def place_img(pg, pil, rect, border=True):
    buf = io.BytesIO()
    pil.convert("RGB").save(buf, "PNG", optimize=True)
    pg.insert_image(rect, stream=buf.getvalue())
    if border:
        pg.draw_rect(rect, color=(0.75, 0.75, 0.75), width=0.5)


def crop(name, y0, y1, x0=0, x1=1100):
    return Image.open(os.path.join(CAP, name)).crop((x0, y0, x1, y1))


def fit_w(img, width):
    return width / img.size[0] * img.size[1]


def place_pdf(pg, pno, clip, rect):
    """기존 쪽의 일부만 170dpi 그림으로 잘라 붙인다(파일 크기 절약)."""
    pix = src[pno].get_pixmap(dpi=170, clip=clip)
    pg.insert_image(rect, stream=pix.tobytes("png"))
    pg.draw_rect(rect, color=(0.75, 0.75, 0.75), width=0.5)


CW = W - 2 * M  # 523

# ── P2. 통계현황 ──────────────────────────────────────────
pg = new_page("1. MBRIS 해양바이오뱅크 통계현황 (화면 캡처)", "출처: MBRIS 통계현황(currentParcel.do, holdingRes.do) · 캡처 2026-10-22 (보유자원 수치는 10-12 수집값과 동일)")
y = 78
caption(pg, y + 8, "분양현황 — 뱅크별·산학연 누적 분양 (기준일자 2025.12.31.)")
a = crop("currentParcel.png", 270, 370)
b = crop("currentParcel.png", 1000, 1590)
ha, hb = fit_w(a, CW) * 0.0 + 0, fit_w(b, CW)
place_img(pg, b, fitz.Rect(M, y + 14, M + CW, y + 14 + hb))
y += 14 + hb + 22
caption(pg, y, "보유자원 (화면 기준일자 2026.10.22., 2026.10.12. 수집값과 수치 동일)")
c = crop("holdingRes.png", 270, 995)
hc = min(fit_w(c, CW), H - M - y - 10)
place_img(pg, c, fitz.Rect(M, y + 6, M + hc / fit_w(c, CW) * CW, y + 6 + hc))

# ── P3. 분양 안내 + 성과현황 ──────────────────────────────
pg = new_page("2. MBRIS 분양 안내와 성과현황 (화면 캡처)", "출처: MBRIS 분양 안내(guide.do), 성과현황(performStatusBoard.do) · 캡처 2026-10-22 (0건은 10-21에도 확인)")
y = 78
caption(pg, y + 8, "분양 안내 — 분양승인기준(시행령 제17조)과 회당·연간 분양 한도")
a = crop("guide.png", 1360, 1935)
ha = fit_w(a, CW)
place_img(pg, a, fitz.Rect(M, y + 14, M + CW, y + 14 + ha))
y += 14 + ha + 18
caption(pg, y, "분양 안내 — 유의사항(만족도 조사, 6개월 후 성과보고서 제출)")
b = crop("guide.png", 2535, 2960)
hb = fit_w(b, CW)
place_img(pg, b, fitz.Rect(M, y + 6, M + CW, y + 6 + hb))
y += 6 + hb + 18
caption(pg, y, "성과현황 게시판 — 등록된 게시물 없음(총 0건)")
c = crop("performStatusBoard.png", 270, 905)
hc = min(fit_w(c, CW), H - M - y - 10)
place_img(pg, c, fitz.Rect(M, y + 6, M + CW * hc / fit_w(c, CW), y + 6 + hc))

# ── P4. 공지 + 전략 ───────────────────────────────────────
pg = new_page("3. MBRIS 공지와 운영 전략 (화면 캡처)", "출처: MBRIS 공지(2026.8.21., 2026.1.8.), 뱅크 소개 중 전략 · 공지 캡처 2026-10-12, 전략 캡처 2026-10-22")
y = 78
for k, (pno, cap) in enumerate([(9, "공지 2026.8.21. — 접수 월 3회, 수령 접수 마감 후 7~10 근무일"), (10, "공지 2026.1.8. — 누리집 리뉴얼, 효능 검색으로 명칭 변경")]):
    x = M + k * (CW / 2 + 6)
    pg.insert_text((x, y + 8), cap, fontname="krb", fontsize=7.6)
    pix = src[pno].get_pixmap(dpi=140)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bb = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 18 else 0).getbbox()
    im = im.crop((max(0, bb[0] - 6), max(0, bb[1] - 6), min(im.width, bb[2] + 6), min(im.height, bb[3] + 6)))
    bw = CW / 2 - 6
    bh = 330
    sc = min(bw / im.width, bh / im.height)
    iw, ih = im.width * sc, im.height * sc
    r = fitz.Rect(x + (bw - iw) / 2, y + 14, x + (bw - iw) / 2 + iw, y + 14 + ih)
    place_img(pg, im, r)
y2 = y + 14 + 330 + 22
caption(pg, y2, "뱅크 소개 — 전략: 수요자 맞춤형 분양 서비스(수요자 기반 정보 구축 및 제공)")
c = crop("introduceBioBank.png", 1165, 1530)
place_img(pg, c, fitz.Rect(M, y2 + 6, M + CW, y2 + 6 + fit_w(c, CW)))

# ── P5. Q&A + 효능 검색 ───────────────────────────────────
pg = new_page("4. MBRIS Q&A 게시판과 효능 검색 화면 (화면 캡처)", "출처: MBRIS Q&A(qna.do), 화장품자원 효능 검색 · Q&A 캡처 2026-10-22, 효능 검색 캡처 2026-10-12")
y = 78
caption(pg, y + 8, "Q&A 게시판 — 총 12건(1/2쪽). 시스템 테스트·보안 점검 문의 2건 제외 후 10건 분석")
a = crop("qna.png", 270, 1745)
ha = fit_w(a, CW * 0.62)
place_img(pg, a, fitz.Rect(M, y + 14, M + CW * 0.62, y + 14 + ha))
bx = M + CW * 0.62 + 10
pg.insert_text((bx, y + 22), "공개 게시글 본문 발췌", fontname="krb", fontsize=7.8)
ex = [("2024-05-13 「질문」(추출물바이오뱅크)", "활성자원만 따로 분류되어있는건 무슨 기준인건가요? 효능이 나와있는 자원만 분류해두신건지 궁금합니다. 그리고 활성자원에서 추출물이 어느 종에서 추출된건지 정보를 받고싶으면 어떻게 해야하나요?"),
      ("2024-07-30 「추출물 활성자원 관련 질문」", "추출물 활성자원의 종을 확인하고 싶습니다.")]
yy = y + 36
for t, body in ex:
    pg.insert_text((bx, yy), t, fontname="krb", fontsize=6.8)
    rc = fitz.Rect(bx, yy + 3, W - M, yy + 120)
    pg.insert_textbox(rc, body, fontname="kr", fontsize=7.2, lineheight=1.45)
    yy += 80 if len(body) > 60 else 40
ys = y + 190
pg.insert_text((bx, ys), "화장품자원 효능 검색 화면", fontname="krb", fontsize=7.8)
pg.insert_text((bx, ys + 11), "시험된 자원의 등급(A·B·C)만 조회", fontname="kr", fontsize=7.2)
clip = fitz.Rect(40, 60, 455, 705)
bw = W - M - bx
place_pdf(pg, 19, clip, fitz.Rect(bx, ys + 17, bx + bw, ys + 17 + bw * clip.height / clip.width))

# ── P6. Mbio-Bridge ───────────────────────────────────────
def stack_nat(pg, y, items, k=1.08):
    """items 를 같은 배율(k)로 붙인다. 쪽 폭을 넘으면 그 조각만 줄인다."""
    for pno, clip in items:
        w = min(clip.width * k, CW)
        h = w * clip.height / clip.width
        place_pdf(pg, pno, clip, fitz.Rect(M, y, M + w, y + h))
        y += h + 4
    return y


def stack(pg, y, items, width):
    """items: [(pno, clip)] 를 같은 축척으로 위에서 아래로 붙인다."""
    for pno, clip in items:
        h = width * clip.height / clip.width
        place_pdf(pg, pno, clip, fitz.Rect(M, y, M + width, y + h))
        y += h + 4
    return y


pg = new_page("5. Mbio-Bridge 해양바이오 주요소재 소개와 기업수요 매칭 (화면 캡처)", "출처: 국립해양생물자원관 Mbio-Bridge · 주요소재 캡처 2026-10-22, 기업수요 매칭 캡처 2026-10-12")
y = 78
caption(pg, y + 8, "해양바이오 주요소재 소개 — 총 6건, 소재명 모두 '샘플 데이터' (캡처 2026-10-22)")
mb = crop("mbioDB.png", 220, 1020, 40, 1460)
hm = fit_w(mb, CW)
place_img(pg, mb, fitz.Rect(M, y + 14, M + CW, y + 14 + hm))
y = y + 14 + hm + 16
caption(pg, y, "기업수요 매칭 — 온라인 상담 신청 후 담당자가 확인하여 답변 또는 개별 연락")
hh = H - M - y - 8
cl = fitz.Rect(40, 150, 580, 650)
stack(pg, y + 6, [(22, cl)], min(CW, hh * cl.width / cl.height))

# ── P7. 학술 문헌 (텍스트) ─────────────────────────────────
pg = new_page("6. 학술 문헌 (서지 정보와 초록 원문)", "원문은 DOI로 확인 가능. 원문 사이트의 자동 접근 차단으로 서지 정보와 초록을 정리하여 수록함")
y = 80
for pno, head in ((23, "참고자료 3"), (24, "참고자료 4")):
    t = src[pno].get_text()
    title = re.sub(r"\s+", " ", t.split("서지 정보")[0]).strip()
    bib = re.sub(r"\s+", " ", t.split("서지 정보")[1].split("초록 (원문)")[0]).strip()
    ab = re.sub(r"\s+", " ", t.split("초록 (원문)")[1]).strip()
    r1 = fitz.Rect(M, y, W - M, y + 40)
    pg.insert_textbox(r1, title, fontname="krb", fontsize=10.5, lineheight=1.3)
    y += 32
    r2 = fitz.Rect(M, y, W - M, y + 60)
    pg.draw_rect(fitz.Rect(M - 4, y - 3, W - M + 4, y + 50), color=(0.75, 0.75, 0.75), fill=(0.97, 0.97, 0.97), width=0.5)
    pg.insert_textbox(r2, bib, fontname="kr", fontsize=7.6, lineheight=1.4)
    y += 58
    pg.insert_text((M, y), "초록 (원문)", fontname="krb", fontsize=8.6)
    r3 = fitz.Rect(M, y + 5, W - M, y + 260)
    rest = pg.insert_textbox(r3, ab, fontname="kr", fontsize=8.2, lineheight=1.45)
    y = r3.y1 - rest + 22 if rest > 0 else r3.y1 + 10

# ── P8. NCI + KOSA ────────────────────────────────────────
pg = new_page("7. 해외 사례와 인건비 산정 근거", "NCI NPNPD(2026-10-12 조회) · 한국인공지능·소프트웨어산업협회 「2026년 적용 SW기술자 평균임금 공표」(2025.12.19.)")
y = 78
caption(pg, y + 8, "NCI NPNPD — 천연물 분획 라이브러리, 23만 점 이상의 추출물 저장소를 연구 커뮤니티에 제공")
w1 = CW * 0.55
cl1 = fitz.Rect(30, 80, 582, 440)
h1 = w1 * cl1.height / cl1.width
place_pdf(pg, 25, cl1, fitz.Rect(M, y + 14, M + w1, y + 14 + h1))
y = y + 14 + h1 + 8
cl2 = fitz.Rect(30, 352, 432, 560)
w2 = CW * 0.62
place_pdf(pg, 26, cl2, fitz.Rect(M, y, M + w2, y + w2 * cl2.height / cl2.width))
y = y + w2 * cl2.height / cl2.width + 18
caption(pg, y, "SW기술자 평균임금 — ① IT기획자 월 11,853,218원, ⑨ 응용SW개발자 월 7,754,124원 (담당자 연락처는 가림)")
stack(pg, y + 6, [(29, fitz.Rect(30, 100, 580, 182)), (29, fitz.Rect(30, 450, 580, 762))], CW * 0.8)

# ── P9. 기사 ──────────────────────────────────────────────
pg = new_page("8. 언론 보도 (근거 문장 부분)", "데일리안(2026.10.6.) · 아시아경제(2025.12.30.) · 푸드투데이(2026.10.10.) · 기자 연락처는 가림")
y = 78
caption(pg, y + 8, "데일리안 「섬·연안 생물 유용물질 선별 빨라진다」")
y = stack_nat(pg, y + 14, [(27, fitz.Rect(20, 155, 452, 187)), (27, fitz.Rect(20, 530, 452, 754))]) + 14
caption(pg, y, "아시아경제 「AI로 바이오 소재 발굴·국산화 가속…국가 바이오데이터 700만건 구축」")
y = stack_nat(pg, y + 6, [(33, fitz.Rect(160, 118, 452, 162)), (33, fitz.Rect(160, 262, 452, 398))]) + 14
caption(pg, y, "푸드투데이 「[2026 국감] 해양바이오 연구과제 31건 중 상용화 7건…사업화 지원 시급」")
stack_nat(pg, y + 6, [(31, fitz.Rect(40, 172, 560, 230)), (31, fitz.Rect(40, 618, 412, 666)), (32, fitz.Rect(40, 362, 412, 397))])

# ── P10. 공공데이터포털 ───────────────────────────────────
pg = new_page("9. 공공데이터포털 공개 자료", "국립해양생물자원관_해양생물 채집 공간정보 · 해양생물 화장품효능 (캡처 2026-10-12)")
y = 78
for pno, y1, cap in ((35, 680, "국립해양생물자원관_해양생물 채집 공간정보 — 학명·분류체계·채집 위치 (계통 정보 입력 자료)"),
                     (36, 597, "국립해양생물자원관_해양생물 화장품효능 — 200여 종 미백·주름개선·항산화 효능 정보")):
    caption(pg, y + 8, cap)
    cl = fitz.Rect(40, 140, 575, y1)
    h = 350 if pno == 35 else 300
    wbox = h * cl.width / cl.height
    place_pdf(pg, pno, cl, fitz.Rect(M, y + 14, M + wbox, y + 14 + h))
    y += 14 + h + 18

out.subset_fonts()
out.save(os.path.join(WORK, "evidence.pdf"), garbage=4, deflate=True)
print("증거 쪽", len(out))

# ── 목차(문서 맨 앞) + 부록 ────────────────────────────────
import shutil
import subprocess
import time

npg = {k: len(fitz.open(os.path.join(APP, k + ".pdf"))) for k in ("method", "appB", "appC", "appD")}
EVID = [("2", "MBRIS 통계현황", "뱅크별·산학연 누적 분양, 보유자원", "국립해양생물자원관 MBRIS (2025.12.31. · 2026.10.12.)", "1~3, 23"),
        ("3", "MBRIS 분양 안내 · 성과현황", "분양승인 기준, 회당·연간 한도, 6개월 후 성과보고서 제출, 성과현황 게시판 0건", "MBRIS (2026.10.21.~22. 확인)", "9, 10, 22"),
        ("4", "MBRIS 공지 · 운영 전략", "분양 접수 기간·수령 일자, 누리집 리뉴얼, 수요자 맞춤형 분양 서비스", "공지 2026.8.21. · 2026.1.8.", "4, 9, 19"),
        ("5", "MBRIS Q&A · 효능 검색", "Q&A 게시판 12건과 공개 게시글 발췌, 화장품자원 효능 검색 화면", "MBRIS (2026.10.12. · 10.22.)", "4, 7"),
        ("6", "Mbio-Bridge", "해양바이오 주요소재 소개(6건), 기업수요 매칭", "국립해양생물자원관", "6"),
        ("7", "학술 문헌", "Saslis-Lagoudakis 외(2012), Schober 외(2025) 서지 정보와 초록", "PNAS 109(39) · Nucleic Acids Res 53(D1)", "11, 15, 16"),
        ("8", "해외 사례 · 인건비 근거", "NCI 천연물 분획 라이브러리, 2026년 적용 SW기술자 평균임금", "미국 국립암연구소 · 한국인공지능·소프트웨어산업협회(2025.12.19.)", "17, 21"),
        ("9", "언론 보도", "호남권생물자원관 AI 시스템, 국가 바이오데이터 구축, 해양바이오 상용화 국감 지적", "데일리안 · 아시아경제 · 푸드투데이", "18, 24, 25"),
        ("10", "공공데이터포털", "해양생물 채집 공간정보, 해양생물 화장품효능", "국립해양생물자원관 (공공데이터포털)", "분석 입력 자료")]
APPX = [("method", "부록 A", "분석 방법과 결과 요약", "제안서 수치의 산출 근거", "5, 8, 12~14, 20"),
        ("appB", "부록 B", "재현 정보와 사용한 공개 자료 목록", "자료 9종 · 실행 환경 · 순서", ""),
        ("appC", "부록 C", "결과 표", "시험별 A등급·AUC, 계통-효능 지도, 50주 모의, 미시험 현황", "12~14"),
        ("appD", "부록 D", "분석 코드 전문", "7개 파일, 줄 번호 표기", "")]
start = 2 + len(out)
appx_rows = []
for key, tag, name, desc, fn in APPX:
    end = start + npg[key] - 1
    appx_rows.append((f"{start}" if end == start else f"{start}~{end}", tag, name, desc, fn))
    start = end + 1
dash = "<span class='na'>–</span>"
tr = ""
for i, (pg_, name, desc, src_, fn) in enumerate(EVID):
    grp = f"<td class='grp' rowspan='{len(EVID)}'>근거<br>자료</td>" if i == 0 else ""
    tr += f"<tr>{grp}<td class='pg'>{pg_}</td><td><b>{name}</b><div class='desc'>{desc}</div></td><td class='src'>{src_}</td><td class='fn'>{fn or dash}</td></tr>"
for i, (pg_, tag, name, desc, fn) in enumerate(appx_rows):
    grp = f"<td class='grp ap' rowspan='{len(appx_rows)}'>부록</td>" if i == 0 else ""
    tr += f"<tr class='aprow'>{grp}<td class='pg'>{pg_}</td><td><b>{tag}. {name}</b></td><td class='src'>{desc}</td><td class='fn'>{fn or dash}</td></tr>"
TOC_HTML = f"""<!doctype html><html><head><meta charset='utf-8'><style>
@page{{size:A4;margin:20mm 16mm 18mm 16mm}}
body{{font-family:'Malgun Gothic',sans-serif;color:#111;margin:0}}
h1{{font-size:18pt;margin:0 0 4px;letter-spacing:-0.3px}}
.sub{{color:#666;font-size:8.8pt;margin:0 0 14px}}
table{{border-collapse:collapse;width:100%;font-size:8.8pt}}
thead th{{background:#2a5d9f;color:#fff;font-weight:700;padding:7px 6px;border:1px solid #2a5d9f;font-size:9pt}}
td{{border:1px solid #cfd6df;padding:6px 7px;vertical-align:middle;line-height:1.38}}
tbody tr:nth-child(even) td:not(.grp){{background:#f6f8fb}}
td.grp{{background:#eaf1fa;color:#2a5d9f;font-weight:700;text-align:center;width:42px;font-size:9pt}}
td.grp.ap{{background:#eef2ec;color:#3f6b3a}}
tr.aprow td:not(.grp){{background:#fbfcfa}}
td.pg{{text-align:center;font-weight:700;width:44px;color:#222}}
td.fn{{text-align:center;width:100px;color:#333;white-space:nowrap}}
td.src{{color:#555;font-size:8.1pt;width:140px}}
.desc{{color:#555;font-size:8.1pt;margin-top:1px}}
.na{{color:#b5b5b5}}
.note{{margin-top:12px;padding:8px 11px;background:#f7f7f5;border-left:3px solid #9aa3ad;font-size:8.2pt;color:#555;line-height:1.6}}
</style></head><body>
<h1>[파일 3] 참고문헌 및 참고자료 묶음</h1>
<p class='sub'>부문 3 활용 성과 촉진 아이디어 제안서 「효능 내비게이터」의 근거 자료 · 화면 캡처 2026-10-12 · 2026-10-22</p>
<table><thead><tr><th>구분</th><th>쪽</th><th>자료</th><th>출처 · 기준일</th><th>본문 각주</th></tr></thead><tbody>{tr}</tbody></table>
<div class='note'>※ 본문 각주 번호를 따라 해당 쪽에서 원문을 확인할 수 있음<br>
※ 학술 논문은 원문 사이트의 자동 접근 차단으로 서지 정보와 초록을 정리하여 수록함<br>
※ 개인 연락처(이메일·전화)는 가림 처리함</div>
</body></html>"""
hp, tp = os.path.join(WORK, "toc.html"), os.path.join(WORK, "toc.pdf")
open(hp, "w", encoding="utf-8").write(TOC_HTML)
if os.path.exists(tp):
    os.remove(tp)
CH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
prof = os.path.join(WORK, "prof_toc")
subprocess.Popen([CH, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--no-pdf-header-footer",
                  f"--print-to-pdf={tp}", "file:///" + hp.replace("\\", "/")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
t0 = time.time()
while time.time() - t0 < 90 and not (os.path.exists(tp) and os.path.getsize(tp) > 0):
    time.sleep(1)
time.sleep(2)
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { $_.CommandLine -like '*prof_toc*' } | "
                "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
shutil.rmtree(prof, ignore_errors=True)

w = PdfWriter()
for path in [os.path.join(WORK, "toc.pdf"), os.path.join(WORK, "evidence.pdf")] + [os.path.join(APP, k + ".pdf") for k in ("method", "appB", "appC", "appD")]:
    for pgx in PdfReader(path).pages:
        w.add_page(pgx)
w.add_metadata({"/Title": "파일3 참고문헌 및 참고자료 묶음"})
with open(OUT, "wb") as f:
    w.write(f)
print("저장", OUT, len(w.pages), "쪽")

# ── 쪽 번호 (모든 쪽 하단 가운데) ──────────────────────────
doc = fitz.open(OUT)
total = len(doc)
for i, page in enumerate(doc, 1):
    r = page.rect
    label = f"- {i} -"
    tw = fitz.get_text_length(label, fontname="helv", fontsize=9)
    page.insert_text(((r.width - tw) / 2, r.height - 18), label, fontname="helv", fontsize=9, color=(0.35, 0.35, 0.35))
tmp = OUT + ".tmp.pdf"
doc.save(tmp, garbage=3, deflate=True)
doc.close()
os.replace(tmp, OUT)
print("쪽 번호 추가", total, "쪽")
