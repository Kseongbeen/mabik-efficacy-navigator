# -*- coding: utf-8 -*-
"""부문3 공식 양식(hwpx로 변환본)에 제안서 본문을 채워 새 hwpx로 저장한다.

- 원본 양식은 건드리지 않는다.
- 각 항목의 [작성 가이드라인] 행은 삭제하고 남은 칸에 본문을 넣는다.
- 글자·문단 모양은 양식 header.xml 끝에 새로 추가해서 쓴다.
- 줄 배치 정보(linesegarray)는 지운다. 한글이 열 때 다시 계산한다.
"""
import datetime, html, json, os, random, re, struct, sys, zipfile
import xml.dom.minidom

FORM, FIG, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
S = json.load(open(os.path.join(FIG, "_summary.json"), encoding="utf-8"))
random.seed(11)

# ── 새 글자 모양(76~) ──────────────────────────────────────────
#   (id, 크기, 글꼴번호, 굵게, 자간, 색)
CHARS = [
    (76, 1100, 3, True, -5, "#000000"),   # □ 소제목 (맑은 고딕 굵게)
    (77, 1050, 7, False, -4, "#000000"),  # ○ 본문 (휴먼명조)
    (78, 1000, 7, False, -4, "#000000"),  # - 세부 (휴먼명조)
    (79, 900, 3, False, -6, "#000000"),   # 표 본문
    (80, 900, 3, True, -6, "#000000"),    # 표 머리글
    (81, 850, 3, False, -5, "#595959"),   # 그림 아래 주석
    (82, 1050, 7, True, -4, "#000000"),   # ○ 본문 강조
    (83, 1000, 3, False, -5, "#000000"),  # 표지 칸 본문
    (84, 1050, 3, True, -5, "#000000"),   # 표지 아이디어명
]
C_SQ, C_O, C_D, C_T, C_TH, C_CAP, C_OB, C_CV, C_CVB = 76, 77, 78, 79, 80, 81, 82, 83, 84

#   (id, 정렬, 왼쪽, 첫줄(음수=내어쓰기), 위, 아래, 줄간격%)
PARAS = [
    (76, "LEFT", 0, 0, 420, 80, 145),      # □
    (77, "JUSTIFY", 1700, -1100, 50, 0, 145),  # ○
    (78, "JUSTIFY", 2900, -900, 20, 0, 140),   # -
    (79, "LEFT", 0, 0, 0, 0, 130),          # 표 칸
    (80, "CENTER", 0, 0, 0, 0, 130),        # 표 머리글 칸
    (81, "CENTER", 0, 0, 160, 120, 110),    # 그림
    (82, "LEFT", 0, 0, 0, 0, 160),          # 표지 칸
]
P_SQ, P_O, P_D, P_TL, P_TC, P_IMG, P_CV = 76, 77, 78, 79, 80, 81, 82

CELL_W = 48190  # 본문 폭
INNER_W = 47600


def esc(t):
    return html.escape(t, quote=False)


def char_xml(cid, h, font, bold, sp, color):
    b = "<hh:bold/>" if bold else ""
    f = font
    return (f'<hh:charPr id="{cid}" height="{h}" textColor="{color}" shadeColor="none" useFontSpace="0" useKerning="0" '
            f'symMark="NONE" borderFillIDRef="4"><hh:fontRef hangul="{f}" latin="{f}" hanja="{f}" japanese="{f}" other="{f}" '
            f'symbol="{f}" user="{f}"/><hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
            f'<hh:spacing hangul="{sp}" latin="{sp}" hanja="{sp}" japanese="{sp}" other="{sp}" symbol="{sp}" user="{sp}"/>'
            f'<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
            f'<hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>{b}'
            f'<hh:underline type="NONE" shape="SOLID" color="#000000"/><hh:strikeout shape="NONE" color="#000000"/>'
            f'<hh:outline type="NONE"/><hh:shadow type="NONE" color="#C0C0C0" offsetX="10" offsetY="10"/></hh:charPr>')


def para_xml(pid, align, left, intent, prev, nxt, ls):
    def mg(k):
        return (f'<hh:margin><hc:intent value="{intent * k}" unit="HWPUNIT"/><hc:left value="{left * k}" unit="HWPUNIT"/>'
                f'<hc:right value="0" unit="HWPUNIT"/><hc:prev value="{prev * k}" unit="HWPUNIT"/>'
                f'<hc:next value="{nxt * k}" unit="HWPUNIT"/></hh:margin><hh:lineSpacing type="PERCENT" value="{ls}" unit="HWPUNIT"/>')
    return (f'<hh:paraPr id="{pid}" tabPrIDRef="0" condense="0" fontLineHeight="0" snapToGrid="0" suppressLineNumbers="0" checked="0">'
            f'<hh:align horizontal="{align}" vertical="BASELINE"/><hh:heading type="NONE" idRef="0" level="0"/>'
            f'<hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="KEEP_WORD" widowOrphan="0" keepWithNext="0" '
            f'keepLines="0" pageBreakBefore="0" lineWrap="BREAK"/><hh:autoSpacing eAsianEng="0" eAsianNum="0"/>'
            f'<hp:switch><hp:case hp:required-namespace="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar">{mg(1)}</hp:case>'
            f'<hp:default>{mg(2)}</hp:default></hp:switch>'
            f'<hh:border borderFillIDRef="4" offsetLeft="0" offsetRight="0" offsetTop="0" offsetBottom="0" connect="0" ignoreMargin="0"/></hh:paraPr>')


def P(runs, pp):
    if isinstance(runs, str):
        runs = [(runs, C_O)]
    body = "".join(f'<hp:run charPrIDRef="{c}"><hp:t>{esc(t)}</hp:t></hp:run>' for t, c in runs)
    return f'<hp:p id="0" paraPrIDRef="{pp}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">{body}</hp:p>'


def SQ(t):
    return P([("□ " + t, C_SQ)], P_SQ)


def O(t, bold=None):
    if bold:
        return P([("○ ", C_O), (bold, C_OB), (" " + t, C_O)], P_O)
    return P([("○ " + t, C_O)], P_O)


def D(t):
    return P([("- " + t, C_D)], P_D)


def NOTE(t):
    return P([(t, C_CAP)], P_IMG)


_z = [50]


def _cell(text, col, row, width, head):
    bf = "9" if head else "8"
    pp, ch = (P_TC, C_TH) if head else (P_TL, C_T)
    paras = "".join(f'<hp:p id="0" paraPrIDRef="{pp}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
                    f'<hp:run charPrIDRef="{ch}"><hp:t>{esc(line)}</hp:t></hp:run></hp:p>' for line in str(text).split("\n"))
    return (f'<hp:tc name="" header="{1 if head else 0}" hasMargin="1" protect="0" editable="0" dirty="0" borderFillIDRef="{bf}">'
            f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" '
            f'linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{paras}</hp:subList>'
            f'<hp:cellAddr colAddr="{col}" rowAddr="{row}"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
            f'<hp:cellSz width="{width}" height="900"/><hp:cellMargin left="280" right="280" top="170" bottom="170"/></hp:tc>')


def T(rows, ratio):
    tot = sum(ratio)
    widths = [int(INNER_W * r / tot) for r in ratio]
    widths[-1] = INNER_W - sum(widths[:-1])
    trs = "".join("<hp:tr>" + "".join(_cell(v, ci, ri, widths[ci], ri == 0) for ci, v in enumerate(row)) + "</hp:tr>"
                  for ri, row in enumerate(rows))
    _z[0] += 1
    tbl = (f'<hp:tbl id="{random.randint(10**9, 2*10**9)}" zOrder="{_z[0]}" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" '
           f'textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="{len(rows)}" '
           f'colCnt="{len(rows[0])}" cellSpacing="0" borderFillIDRef="8" noAdjust="0">'
           f'<hp:sz width="{INNER_W}" widthRelTo="ABSOLUTE" height="{900 * len(rows)}" heightRelTo="ABSOLUTE" protect="0"/>'
           f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" '
           f'horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
           f'<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="280" right="280" top="170" bottom="170"/>{trs}</hp:tbl>')
    return (f'<hp:p id="0" paraPrIDRef="{P_IMG}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="{C_T}">{tbl}<hp:t/></hp:run></hp:p>')


_images = []


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def IMG(fname, width_mm):
    path = os.path.join(FIG, fname)
    wpx, hpx = png_size(path)
    idx = len(_images) + 1
    _images.append((f"image{idx}", path))
    org_w, org_h = wpx * 75, hpx * 75
    cur_w = min(int(width_mm * 283.465), INNER_W)
    cur_h = int(cur_w * hpx / wpx)
    sx, sy = cur_w / org_w, cur_h / org_h
    _z[0] += 1
    pic = (f'<hp:pic id="{random.randint(10**9, 2*10**9)}" zOrder="{_z[0]}" numberingType="PICTURE" textWrap="TOP_AND_BOTTOM" '
           f'textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" href="" groupLevel="0" instid="{random.randint(10**8, 10**9)}" reverse="0">'
           f'<hp:offset x="0" y="0"/><hp:orgSz width="{org_w}" height="{org_h}"/><hp:curSz width="{cur_w}" height="{cur_h}"/>'
           f'<hp:flip horizontal="0" vertical="0"/><hp:rotationInfo angle="0" centerX="{cur_w // 2}" centerY="{cur_h // 2}" rotateimage="1"/>'
           f'<hp:renderingInfo><hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>'
           f'<hc:scaMatrix e1="{sx:.6f}" e2="0" e3="0" e4="0" e5="{sy:.6f}" e6="0"/>'
           f'<hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/></hp:renderingInfo>'
           f'<hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="{org_w}" y="0"/><hc:pt2 x="{org_w}" y="{org_h}"/><hc:pt3 x="0" y="{org_h}"/></hp:imgRect>'
           f'<hp:imgClip left="0" right="{org_w}" top="0" bottom="{org_h}"/><hp:inMargin left="0" right="0" top="0" bottom="0"/>'
           f'<hp:imgDim dimwidth="{org_w}" dimheight="{org_h}"/>'
           f'<hc:img binaryItemIDRef="image{idx}" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/><hp:effects/>'
           f'<hp:sz width="{cur_w}" widthRelTo="ABSOLUTE" height="{cur_h}" heightRelTo="ABSOLUTE" protect="0"/>'
           f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" '
           f'horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
           f'<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:shapeComment>{esc(fname)}</hp:shapeComment></hp:pic>')
    return (f'<hp:p id="0" paraPrIDRef="{P_IMG}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="{C_T}">{pic}<hp:t/></hp:run></hp:p>')


# ── 수치 ─────────────────────────────────────────────────────
auc = S["auc"]
sim = {n.split()[0]: (r, q) for n, r, q in S["sim50"]}
def f2(x): return f"{x:.2f}"
AUC_SA, AUC_PG, AUC_DP = auc["S.aureus"], auc["PGE2"], auc["DPPH"]
AUC_MEAN, N_ASSAY = S["auc_mean"], S["n_assays"]
AUC_VIR = (auc["H1N1"], auc["A형간염"])
r_sa, q_sa = sim["황색포도상구균"]; r_bc, q_bc = sim["바실러스"]; r_no, q_no = sim["NO"]; r_pg, q_pg = sim["PGE2"]; r_ab, q_ab = sim["ABTS"]
ST = S["strep"]
BASE = ST["micro_base"]

# ── 본문 ─────────────────────────────────────────────────────
SEC1 = [
    SQ("보유 자원이 가장 많은 뱅크의 활용도가 가장 낮음"),
    O("보유 1천 점당 연간 분양 건수는 미세조류 78.1건 / 추출물 33.6건인 반면 미생물 5.4건 / 유전자원 3.0건으로 각 1만 점이 넘는 가장 큰 자원 풀의 활용도가 가장 낮음 (그림 1-가)"),
    O("화장품소재 뱅크(2022년 개설)와 항생제소재 뱅크(2023년 개설)의 2025년 말 누적 분양은 각각 8건과 5건에 그침"),
    O("해양바이오뱅크 누적 분양 2,265건 가운데 기업은 263건(11.6%)으로 산업화 수요자의 이용이 낮음 (MBRIS 통계현황)"),
    SQ("미시험 자원은 효능을 판단할 정보가 없음"),
    O("2026년 1월 누리집 개편으로 효능 검색이 도입되었으나 이미 시험된 자원의 등급을 조회하는 기능에 한정됨"),
    O("해양미생물 바이오뱅크 분양 목록 10,516주 가운데 4,610주는 효능 시험이 이루어진 종에 속하지 않으며 이 중 4,525주가 분양 가능 상태임"),
    O("기업용 창구인 Mbio-Bridge의 해양바이오 주요소재 DB는 6건이며 모두 샘플 데이터로 표시되고 기업수요 매칭은 담당자 상담 방식으로 운영됨"),
    O("이용자도 같은 어려움을 묻고 있음. 뱅크 Q&A 실질 문의 10건 중 4건이 활성자원의 종 정보와 선정 기준에 관한 질문임 (2023~2024)"),
    D("“활성자원만 따로 분류되어 있는 건 무슨 기준인가요 … 어느 종에서 추출된 건지 정보를 받고 싶으면 어떻게 해야 하나요” (2024년 5월 문의)"),
    SQ("효능이 우수한 자원은 드물어 임의로 고르기 어려움"),
    O(f"효능 등급이 붙은 추출물 8,808건의 시험 30종에서 A등급 비율 중앙값은 {S['eda']['median_A']}%이며 살모넬라와 대장균 항균은 0.1% 이하임 (그림 1-나)"),
    IMG("그림1_EDA_분양현황과A등급.png", 152),
    SQ("분양 한도와 소요 기간 때문에 잘못 고른 비용이 큼"),
    O("미생물 분양은 회당 20점과 연간 50점으로 제한되고 신청은 월 3회(10일 단위) 접수하여 접수 마감 후 7~10 근무일 뒤에 자원을 받음 (분양 안내 / 2026년 8월 공지)"),
    O(f"미생물 추출물의 황색포도상구균 항균 A등급 비율은 {BASE * 100:.1f}%로 연간 한도 50주를 임의로 고르면 기대 A등급은 {r_sa:.1f}건에 불과함"),
    SQ("분양 성과가 다음 선택으로 돌아오지 않음"),
    O("분양 6개월 후 성과보고서 제출이 의무이나 성과현황 공개 게시판은 0건으로 이용자와 뱅크 모두 참고할 수 없음"),
    SQ("원인 정리"),
    O("효능 데이터가 ① 미시험 자원으로 확장되지 않고 ② 이용자의 목적과 연결되지 않으며 ③ 분양 결과로 갱신되지 않음"),
]

SEC2 = [
    SQ("뱅크 효능 데이터 분석 결과 효능은 생물 계통을 따라 모여 있음"),
    O("같은 계통의 생물은 생합성 경로를 공유하여 비슷한 물질을 만드는 경향이 있음 (화학분류학)"),
    O("효능 등급 추출물 8,808건을 계통별로 집계한 결과 다시마목은 항산화(ABTS) A등급 비율 89%로 평균의 7배이고 "
      f"사초과와 그물바탕말목은 항염(PGE2) 72%이며 방선균은 항균 {ST['A_rate'] * 100:.0f}%로 미생물 평균의 {ST['A_rate'] / BASE:.0f}배임"),
    IMG("그림2_계통효능지도.png", 142),
    SQ("계통 정보만으로 처음 보는 종의 효능을 예측할 수 있음"),
    O("학습에 쓰지 않은 종을 맞히는 방식(종 단위 5겹 교차검증)으로 검증함"),
    O(f"예측 정확도(AUC)는 항균 {f2(AUC_SA)} / 항염(PGE2) {f2(AUC_PG)} / 항산화(DPPH) {f2(AUC_DP)}이며 {N_ASSAY}개 시험 평균 {f2(AUC_MEAN)}임"),
    O("목 수준의 계통만 알아도 성능 대부분이 확보되어 종 동정이 불완전한 자원에도 적용 가능함"),
    O(f"항바이러스 시험은 {f2(min(AUC_VIR))}~{f2(max(AUC_VIR))}로 예측력이 낮아 서비스 표시 대상에서 제외함"),
    SQ("연간 분양 한도 50주 모의 비교 (미생물 추출물 대상)"),
    O(f"예측 상위 50주를 고르면 항균 A등급이 {r_sa:.1f}건에서 {q_sa}건으로 / 바실러스 세레우스 항균은 {r_bc:.1f}건에서 {q_bc}건으로 / "
      f"항염(NO)은 {r_no:.1f}건에서 {q_no}건으로 늘어남"),
    O(f"항산화(ABTS)는 {r_ab:.1f}건에서 {q_ab}건으로 차이가 작아 미생물보다 해조류·염생식물 계통 정보로 안내함"),
    IMG("그림3_예측정확도_모의비교.png", 152),
    SQ("국내외 사례와 우리 뱅크 적용 방안"),
    T([["사례", "주요 내용", "우리 뱅크 적용"],
       ["계통 기반 유용식물 예측 연구\n(PNAS 2012)", "약 2만 종 계통수에서 약용식물이 특정 가지에 모여 있음을 밝히고 다른 지역의 유용식물 예측에 활용",
        "뱅크 효능 등급으로 해양 생물의 효능 집중 계통을 직접 산출하여 검색과 추천에 활용"],
       ["BacDive (독일 DSMZ)", "약 10만 균주의 표준화된 표현형 정보를 통합 검색과 API로 제공", "뱅크 균주 정보에 효능 가능성 정보를 더하고 외부 플랫폼과 연동"],
       ["천연물 분획 라이브러리\n(미국 NCI)", "2019년부터 50만 점 이상의 천연물 분획을 연구자에게 무상 제공",
        "뱅크도 무상 분양 체계를 갖추었으나 무엇을 고를지 안내하는 기능이 없어 이를 보완"],
       ["섬·연안 생물 후보물질 선별\n(국립호남권생물자원관 2026)", "섬·연안 식물의 후보물질과 유전자 우선순위를 연구용으로 산출",
        "본 제안은 분양 검색과 추천과 성과 환류에 직접 연결된다는 점에서 차별됨"]], [26, 40, 34]),
    SQ("개선 방향"),
    O("선진 사례는 표준화된 데이터를 이용자가 고르기 쉬운 형태로 제공하고 외부와 연동하는 공통점이 있음"),
    O("우리 뱅크는 표준화된 효능 데이터를 이미 갖추었으므로 선택 지원과 연동 기능을 더하는 것이 가장 효과적임"),
    O("이는 뱅크가 전략으로 제시한 수요자 맞춤형 분양 서비스(수요자 기반 정보 구축 및 제공)를 구체화하는 방향임"),
]

SEC3 = [
    SQ("서비스 구성: 효능 내비게이터"),
    IMG("그림4_서비스구조.png", 120),
    T([["기능", "내용", "해결 문제", "성과 지표 (현재 → 목표)"],
       ["① 효능 가능성 표시", "모든 자원에 시험별 효능 정보 표시. 실측 등급과 예측 가능성(근거 계통 포함)을 구분", "미시험 자원 정보 부재", "미시험 미생물 표시 비율 0% → 40%(1,866주). 시험 축적에 따라 확대"],
       ["② 목적별 추천", "목적 효능과 자원 유형과 수량을 입력하면 분양 한도 안 후보 제시 후 장바구니 연결", "효능 자원 희소와 임의 선택", "연간 한도 안 항균 A등급 1건 이상 확보 확률 36% → 99%"],
       ["③ 기업 창구 연동", "Mbio-Bridge 소재 DB를 계통별 효능 정보로 채우고 수요매칭 상담에 추천 결과 첨부", "기업 창구와 효능 데이터 단절", "기업 분양 비중 11.6% → 20% (3년)"],
       ["④ 성과·시험 환류", "성과보고서에 효능 확인 항목 추가. 월 1회 예측 갱신. 내부 시험 우선순위 제공", "성과 미축적", "효능 확인 회신 0건 → 시범 기간 분양 건의 50%"]],
      [17, 39, 17, 27]),
    SQ("화면 구성 예시"),
    IMG("그림5_화면시안.png", 166),
    SQ("오인 방지 원칙"),
    O("실측 등급과 예측 정보는 색과 문구를 달리하여 구분하고 예측은 참고 정보임을 명시함"),
    O("같은 계통에서 시험된 종이 3종 미만이거나 추출물이 10건 미만이면 예측을 표시하지 않음"),
    O("예측력이 낮은 시험(항바이러스 등)은 표시하지 않고 예측 성능을 정기적으로 공개함"),
    SQ("단계별 추진 계획"),
    T([["단계", "기간", "주요 내용", "수행 주체"],
       ["1단계 데이터 정비", "1~3개월", "뱅크 간 중복 자원번호 통합과 분류 정보 보완 / 성과보고서 항목 추가", "뱅크 운영 부서\n위탁 기관"],
       ["2단계 시범 운영", "4~6개월", "미생물 뱅크와 효능 뱅크에 ①② 기능 적용 / 항균·항염 시험부터 표시", "위탁 개발 기관"],
       ["3단계 효과 검증", "7~12개월", "추천 경유 분양과 일반 분양을 6개월간 비교(효능 확인율 / 기존 만족도 조사 / 기업 비중). 효능 확인율이 2배 이상이면 전 뱅크로 확대", "뱅크 운영 부서"],
       ["4단계 확대", "2년 차", "Mbio-Bridge 연동과 외부 API 제공 / 균주 유전자 서열과 채집 환경 정보를 더한 예측 고도화", "뱅크\n협력 기관"]],
      [19, 12, 51, 18]),
    SQ("예상 한계와 대응"),
    O("계통 정보만 사용하는 경량 모델로 별도 고성능 장비 없이 기존 서버에서 운영 가능함", "예산·설비:"),
    D("뱅크 보유 데이터와 공개 데이터만 사용하므로 데이터 구매 비용이 없음"),
    D("소요 인력은 데이터 정비 2인월 / 화면·추천 기능 개발 4인월 / 사업관리 1인월로 총 7인월이며 직접인건비는 약 5,840만 원임 (2026년 SW기술자 평균임금 응용SW개발자 월 775만 원과 IT기획자 월 1,185만 원 기준. 제경비와 기술료는 SW사업 대가산정 가이드에 따라 가산)"),
    O("데이터 담당 1인이 월 1회 갱신을 수행하도록 자동화 절차를 함께 제공함", "인력:"),
    O("예측 정보는 참고 정보로만 제공하며 분양 승인 기준(해양수산생명자원법 시행령 제17조)에 영향을 주지 않음. 성과보고서 항목 추가는 기존 의무 제출 양식 안에서 가능함", "법·제도:"),
    O("효능 등급이 3단계이고 시험관 내 결과라는 한계가 있음. 같은 종도 채집 시기에 따라 등급이 달라지는 사례가 있어 4단계에서 채집 환경 정보를 더해 보완함", "데이터 한계:"),
]

SEC4 = [
    SQ("유용성"),
    O(f"연간 미생물 한도 50주 안에서 항균 A등급을 1건 이상 얻을 확률이 36%에서 99% 이상으로 높아짐. 임의로 고르면 첫 A등급까지 평균 6회 신청(연간 한도 기준 약 2.4년)이 필요하나 추천 목록은 첫 신청에서 기대 2건 이상임 (2항 모의 비교)", "분양 성과 향상:"),
    O("효능 등급 추출물 8,808건의 시험 결과가 미시험 분양 가능 자원 4,525주의 선택 근거로 쓰임", "보유 데이터의 가치 확대:"),
    O("무엇을 분양받아야 하는지에 대한 진입 장벽을 낮춤. 기업 분양 비중 11.6%를 3년 안에 20%로 높이는 것을 목표로 하며 3단계에서 실제 효과를 측정함", "기업 이용 확대:"),
    O("반복되는 추천 상담을 추천 결과 제공으로 대체하고 뱅크 내부 시험 순서를 근거에 따라 정하여 같은 수의 A등급 자원을 찾는 데 필요한 시험 수를 줄임", "행정 효율:"),
    SQ("파급력"),
    O("성과보고와 신규 시험이 쌓일수록 예측이 정교해지는 순환 구조로 일회성 기능이 아님", "지속성:"),
    O("뱅크 안에서는 유전자원 12,199점과 미세조류로 같은 방식을 넓히고 뱅크 밖에서는 국립생물자원관·국립낙동강생물자원관·국립호남권생물자원관 등 생물자원 분양 기관과 국가바이오데이터통합플랫폼에 API로 연동하여 국가 차원의 소재 탐색 기반으로 확장 가능함", "확산 가능성:"),
    O("Mbio-Bridge의 공동연구 신청과 미활용 특허 나눔 사업과 연계하여 분양에서 기술사업화까지 이어지는 경로를 만듦", "연계 사업:"),
    O("뱅크 전략인 수요자 맞춤형 분양 서비스를 구체화하고 해양바이오 연구성과의 낮은 상용화율과 소재 DB 고도화 필요성에 대한 지적에 대응함", "정책 부합:"),
]

REFS = [
    ("해양바이오뱅크 소개·통계현황·분양 안내·공지·Q&A·성과현황·검색 화면 (화면 캡처)", "국립해양생물자원관 MBRIS", "2026"),
    ("Mbio-Bridge 해양바이오 주요소재 DB·기업수요 매칭 (화면 캡처)", "국립해양생물자원관", "2026"),
    ("Phylogenies reveal predictive power of traditional medicine in bioprospecting", "PNAS 109(39)", "2012"),
    ("BacDive in 2025: the core database for prokaryotic strain data", "Nucleic Acids Research 53(D1)", "2025"),
    ("NCI Program for Natural Products Discovery Prefractionated Library", "미국 국립암연구소", "2023"),
    ("섬·연안 생물 유용물질 선별 빨라진다", "데일리안", "2026"),
    ("2026년 적용 SW기술자 평균임금 공표", "한국인공지능·소프트웨어산업협회", "2025"),
    ("[2026 국감] 해양바이오 연구과제 31건 중 상용화 7건", "푸드투데이", "2026"),
    ("AI로 바이오 소재 발굴·국산화 가속…국가 바이오데이터 700만 건 구축", "아시아경제", "2025"),
    ("해양생물 채집 공간정보 / 해양생물 화장품효능", "공공데이터포털", "2025"),
]

IDEA = "효능 내비게이터: 계통 기반 효능 예측으로 미시험 분양 자원의 활용 가능성을 찾아 주는 검색·추천 서비스"
SUMMARY = "미시험 분양 자원에 효능 가능성을 표시하고 연간 분양 한도 안에서 성과 가능성이 높은 자원을 추천하는 검색 서비스 도입"
OVERVIEW = ("뱅크는 8,800여 건의 추출물 효능 시험 결과를 보유하고 있으나 미시험 자원에는 효능 정보가 없어 이용자가 근거 없이 자원을 고르고 있음. "
            "효능이 생물 계통을 따라 모여 있다는 점을 활용하여 미시험 자원의 효능 가능성을 검색 화면에 표시하고 목적별 추천과 성과 환류 체계를 함께 구축하는 제안임")
KEYWORDS = "#효능예측   #미시험자원   #목적별추천   #성과환류   #분양활성화"
assert len(SUMMARY) <= 100 and len(OVERVIEW) <= 200, (len(SUMMARY), len(OVERVIEW))


# ── 양식 수정 ────────────────────────────────────────────────
def strip_seg(x):
    return re.sub(r"<hp:linesegarray>.*?</hp:linesegarray>", "", x, flags=re.S)


def tables(sec):
    out, i = [], 0
    while True:
        i = sec.find("<hp:tbl ", i)
        if i < 0: return out
        # 중첩 표를 고려해 짝 맞추기
        depth, j = 0, i
        while True:
            a = sec.find("<hp:tbl ", j + 1); b = sec.find("</hp:tbl>", j + 1)
            if a != -1 and a < b:
                depth += 1; j = a
            else:
                if depth == 0:
                    out.append((i, b + len("</hp:tbl>"))); break
                depth -= 1; j = b
        i = b + 1


def cell_paras(runs_list, pp=P_CV):
    return "".join(f'<hp:p id="0" paraPrIDRef="{pp}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
                   + "".join(f'<hp:run charPrIDRef="{c}"><hp:t>{esc(t)}</hp:t></hp:run>' for t, c in runs) + "</hp:p>"
                   for runs in runs_list)


def set_cell(tbl, col, row, inner):
    m = re.search(r'(<hp:tc [^>]*>\s*<hp:subList [^>]*>)(.*?)(</hp:subList>\s*<hp:cellAddr colAddr="%d" rowAddr="%d"/>)' % (col, row), tbl, re.S)
    # 비탐욕 매칭이 앞 칸부터 잡히지 않도록 해당 칸의 tc 시작을 다시 찾음
    end = tbl.find(f'<hp:cellAddr colAddr="{col}" rowAddr="{row}"/>')
    tc_start = tbl.rfind("<hp:tc ", 0, end)
    sub_start = tbl.find(">", tbl.find("<hp:subList ", tc_start)) + 1
    sub_end = tbl.rfind("</hp:subList>", 0, end)
    return tbl[:sub_start] + inner + tbl[sub_end:]


def fill_cover(t):
    t = set_cell(t, 1, 1, cell_paras([[(IDEA, C_CVB)]]))
    t = set_cell(t, 1, 2, cell_paras([[(SUMMARY, C_CV)]]))
    t = set_cell(t, 1, 3, cell_paras([[(OVERVIEW, C_CV)]]))
    t = set_cell(t, 2, 4, cell_paras([[("■ 자원 정보·검색 서비스", C_CVB)]]))
    t = set_cell(t, 1, 5, cell_paras([[("■ 성과 환류·관리", C_CVB)]]))
    t = set_cell(t, 1, 7, cell_paras([[(KEYWORDS, C_CV)]]))
    return t


def fill_section_box(t, body):
    # 가이드라인 행 삭제
    first_tr = t.find("<hp:tr>"); first_tr_end = t.find("</hp:tr>") + len("</hp:tr>")
    t = t[:first_tr] + t[first_tr_end:]
    t = t.replace('rowCnt="2"', 'rowCnt="1"', 1).replace('rowAddr="1"', 'rowAddr="0"')
    t = t.replace('treatAsChar="1"', 'treatAsChar="0"', 1).replace('pageBreak="CELL"', 'pageBreak="TABLE"', 1)
    t = re.sub(r'(<hp:sz width="\d+" widthRelTo="ABSOLUTE" height=")\d+', r"\g<1>3000", t, count=1)
    t = re.sub(r'(<hp:cellSz width="\d+" height=")\d+', r"\g<1>3000", t)
    t = t.replace('vertAlign="CENTER"', 'vertAlign="TOP"', 1)
    t = re.sub(r'(<hp:tc [^>]*borderFillIDRef=")\d+', r"\g<1>2", t, count=1)
    sub_start = t.find(">", t.find("<hp:subList ")) + 1
    sub_end = t.find("</hp:subList>")
    return t[:sub_start] + "".join(body) + t[sub_end:]


def fill_refs(t):
    rows = re.findall(r"<hp:tr>.*?</hp:tr>", t, re.S)
    head, proto = rows[0], rows[1]
    new_rows = [head]
    for k, (name, src, yr) in enumerate(REFS, 1):
        r = proto
        for col, val in enumerate([str(k), name, src, yr]):
            r = set_cell(r, col, 1, cell_paras([[(val, C_T)]], pp=P_TC if col in (0, 3) else P_TL))
        r = re.sub(r'rowAddr="\d+"', f'rowAddr="{k}"', r)
        new_rows.append(r)
    body = "".join(new_rows)
    s0 = t.find("<hp:tr>"); s1 = t.rfind("</hp:tr>") + len("</hp:tr>")
    t = t[:s0] + body + t[s1:]
    return re.sub(r'rowCnt="\d+"', f'rowCnt="{len(new_rows)}"', t, count=1)


def check_boxes(t):
    return t.replace("<hp:t>□ </hp:t>", "<hp:t>■ </hp:t>").replace("<hp:t>□</hp:t>", "<hp:t>■</hp:t>")


def main():
    zin = zipfile.ZipFile(FORM)
    sec = strip_seg(zin.read("Contents/section0.xml").decode("utf-8"))
    hdr = zin.read("Contents/header.xml").decode("utf-8")

    # header: 글자·문단 모양 추가
    cp = "".join(char_xml(*c) for c in CHARS)
    pp = "".join(para_xml(*p) for p in PARAS)
    hdr = hdr.replace("</hh:charProperties>", cp + "</hh:charProperties>", 1)
    hdr = re.sub(r'<hh:charProperties itemCnt="(\d+)"', lambda m: f'<hh:charProperties itemCnt="{int(m.group(1)) + len(CHARS)}"', hdr, 1)
    hdr = hdr.replace("</hh:paraProperties>", pp + "</hh:paraProperties>", 1)
    hdr = re.sub(r'<hh:paraProperties itemCnt="(\d+)"', lambda m: f'<hh:paraProperties itemCnt="{int(m.group(1)) + len(PARAS)}"', hdr, 1)

    T_ = tables(sec)
    assert len(T_) == 9, len(T_)
    parts = []
    bodies = {3: SEC1, 4: SEC2, 5: SEC3, 6: SEC4}
    prev = 0
    for k, (a, b) in enumerate(T_):
        parts.append(sec[prev:a])
        t = sec[a:b]
        if k == 1: t = fill_cover(t)
        elif k in bodies:
            # 표를 감싼 문단 통째로 본문 문단들로 교체
            ps = parts[-1].rfind("<hp:p ")
            head_part = parts[-1][:ps]
            parts[-1] = head_part
            pe = sec.find("</hp:p>", b) + len("</hp:p>")
            parts.append("".join(bodies[k])); prev = pe
            continue
        elif k == 7: t = fill_refs(t)
        elif k == 8: t = check_boxes(t)
        parts.append(t); prev = b
    parts.append(sec[prev:])
    sec = "".join(parts)
    # 3·4항 앞의 쪽 나눔 제거 (분량 절약)
    for h in ("2. 현황 분석 및 벤치마킹", "3. 개선 방안 및 적용 계획", "4. 기대효과 및 파급력"):
        k = sec.find(h); ps = sec.rfind("<hp:p ", 0, k)
        sec = sec[:ps] + sec[ps:k].replace('pageBreak="1"', 'pageBreak="0"', 1) + sec[k:]
    assert "[작성 가이드라인]" not in sec
    xml.dom.minidom.parseString(sec.encode("utf-8")); xml.dom.minidom.parseString(hdr.encode("utf-8"))

    hpf = zin.read("Contents/content.hpf").decode("utf-8")
    items = "".join(f'<opf:item id="{i}" href="BinData/{i}.png" media-type="image/png" isEmbeded="1"/>' for i, _ in _images)
    hpf = hpf.replace('<opf:item id="section0"', items + '<opf:item id="section0"', 1)
    prv = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", sec)))[:1000]

    zout = zipfile.ZipFile(OUT, "w")
    for info in zin.infolist():
        n = info.filename
        data = {"Contents/section0.xml": sec.encode("utf-8"), "Contents/header.xml": hdr.encode("utf-8"),
                "Contents/content.hpf": hpf.encode("utf-8"), "Preview/PrvText.txt": prv.encode("utf-8")}.get(n) or zin.read(n)
        comp = zipfile.ZIP_STORED if n == "mimetype" else zipfile.ZIP_DEFLATED
        zout.writestr(zipfile.ZipInfo(n, date_time=datetime.datetime.now().timetuple()[:6]), data, compress_type=comp)
    for iid, path in _images:
        zout.write(path, f"BinData/{iid}.png", compress_type=zipfile.ZIP_STORED)
    zout.close()
    print("saved", OUT, "images", len(_images))


if __name__ == "__main__":
    main()
