# FONT_SCALED
"""제안서용 그림 4종 생성 (인쇄용 PNG, 라이트 모드)."""
import sys, os, warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.feature_extraction.text import CountVectorizer

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
DATA, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

# 팔레트 (dataviz 기본 팔레트, 라이트)
SURF, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0"
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
NEUTRAL = "#b9b8b1"
SEQ = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

plt.rcParams.update({
    "font.family": "Malgun Gothic", "axes.unicode_minus": False,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "font.size": 12,
})

B = pd.read_pickle(f"{DATA}/B.pkl"); A = pd.read_pickle(f"{DATA}/A.pkl"); M = pd.read_pickle(f"{DATA}/M.pkl")
tax = (pd.read_csv(f"{DATA}/collect_u8.csv", encoding="utf-8-sig", usecols=["학명", "분류체계"], low_memory=False)
       .dropna().drop_duplicates("학명").set_index("학명")["분류체계"])
g2l = {}
for sp, t in tax.items():
    parts = [p for p in t.split(" > ") if p != sp]; g = sp.split()[0]
    if g not in g2l or len(parts) > len(g2l[g]): g2l[g] = parts


import json
NCBI = json.load(open(f"{DATA}/ncbi_genus_lineage.json", encoding="utf-8")) if os.path.exists(f"{DATA}/ncbi_genus_lineage.json") else {}
MICRO = ("세균", "균류", "미세조류")


def lineage(sp, grp):
    g = str(sp).split()[0]
    if grp in MICRO and NCBI.get(g):
        return [grp] + NCBI[g] + ["g:" + g]
    L = [p for p in str(tax.get(sp, "")).split(" > ") if p and p != sp] if sp in tax.index else g2l.get(g, [])
    return [grp] + L + ["g:" + g]


for d in (B, A, M):
    d.dropna(subset=["학명"], inplace=True)
    d["L"] = d.apply(lambda r: lineage(r["학명"], r["분류"]), axis=1)

# ---------- 그림 1: 계통-효능 지도 ----------
rows = [("다시마목\n(감태·곰피·대황)", "Laminariales"), ("모자반속", "g:Sargassum"), ("그물바탕말목", "Dictyotales"),
        ("갈파래목", "Ulvales"), ("사초과\n(좀보리사초 등)", "Cyperaceae"), ("장미목\n(해당화 등)", "Rosales"),
        ("방선균\nStreptomyces", "g:Streptomyces"), ("홍조식물문", "Rhodophyta"),
        ("어류", "척추동물(어류)"), ("무척추동물", "무척추동물")]
cols = [("ABTS\n항산화", B, "ABTS"), ("DPPH\n항산화", B, "DPPH"), ("콜라게나아제\n주름", B, "Collag"),
        ("포도상구균\n항균", A, "S.aureus"), ("NO\n항염", A, "NO"), ("PGE2\n항염", A, "PGE2"), ("DPP4\n혈당", M, "DPP4")]
mat = np.full((len(rows), len(cols)), np.nan); nmat = np.zeros_like(mat)
for i, (_, key) in enumerate(rows):
    for j, (_, d, c) in enumerate(cols):
        x = d[d[c].isin(["A", "B", "C"]) & d["L"].apply(lambda L: key in L)]
        if len(x) >= 10:
            mat[i, j] = (x[c] == "A").mean() * 100; nmat[i, j] = len(x)
avg = [(d[d[c].isin(["A", "B", "C"])][c] == "A").mean() * 100 for _, d, c in cols]

fig, ax = plt.subplots(figsize=(8.6, 6.2), dpi=220)
from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list("seq", SEQ)
im = ax.imshow(np.nan_to_num(mat, nan=-1), cmap=cmap, vmin=0, vmax=100, aspect="auto")
for i in range(len(rows)):
    for j in range(len(cols)):
        v = mat[i, j]
        if np.isnan(v):
            ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, color="#f0efec", zorder=2))
            ax.text(j, i, "자료\n부족", ha="center", va="center", fontsize=8.4, color=MUTED, zorder=3)
        else:
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=11.4, fontweight="bold",
                    color="white" if v >= 45 else INK, zorder=3)
for k in range(len(rows) + 1): ax.axhline(k - .5, color=SURF, lw=2, zorder=4)
for k in range(len(cols) + 1): ax.axvline(k - .5, color=SURF, lw=2, zorder=4)
ax.set_xticks(range(len(cols)), [c[0] for c in cols], fontsize=10.2)
ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=10.2)
ax.xaxis.tick_top(); ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
ax.set_xticks(range(len(cols)), [f"{c[0]}\n(평균 {a:.0f}%)" for c, a in zip(cols, avg)], fontsize=9.6)
cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02); cb.outline.set_visible(False)
cb.set_label("A등급 비율 (%)", color=INK2); cb.ax.tick_params(colors=INK2, length=0)
fig.text(0.01, 0.015, "자료: MBRIS 효능 등급 추출물 8,808건(중복 제거) 분석. 계통별 추출물 10건 미만은 '자료 부족'으로 표시.", fontsize=9.0, color=MUTED)
fig.suptitle("그림 2. 계통별 효능 A등급 비율 (계통–효능 지도)", x=0.01, ha="left", fontsize=14.4, fontweight="bold")
fig.tight_layout(rect=(0, 0.03, 1, 0.96))
fig.savefig(f"{OUT}/그림2_계통효능지도.png"); plt.close(fig)
print("fig1 done")

# ---------- 그림 2: 계통 깊이별 AUC ----------
def depth_tokens(L, lvl):
    if lvl == 0: return [L[0]]
    core = [t for t in L if not t.startswith("g:")]
    if lvl == 1: return core[:max(1, len(core) - 2)]
    if lvl == 2: return core[:max(1, len(core) - 1)]
    return L


def cv_auc(d, c, lvl):
    x = d[d[c].isin(["A", "B", "C"])]
    X = CountVectorizer(analyzer=lambda t: t).fit_transform(x["L"].apply(lambda L: depth_tokens(L, lvl)))
    y = (x[c] == "A").values.astype(int); g = x["학명"].values; p = np.zeros(len(y))
    for tr, te in GroupKFold(5).split(X, y, g):
        p[te] = LogisticRegression(max_iter=3000, class_weight="balanced").fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return roc_auc_score(y, p)


levels = ["대분류\n(7개 그룹)", "문~목", "과", "속"]
series = [("황색포도상구균 항균", A, "S.aureus", S1), ("PGE2 항염", A, "PGE2", S2),
          ("콜라게나아제 주름", B, "Collag", S3), ("인플루엔자 항바이러스", A, "H1N1", NEUTRAL)]
CURVES = {}
fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=220)
ax.axhline(0.5, color=MUTED, lw=1, ls=(0, (4, 3)))
ax.text(3.08, 0.515, "무작위 수준 0.5", va="bottom", fontsize=9.6, color=MUTED)
for name, d, c, col in series:
    v = [cv_auc(d, c, l) for l in range(4)]
    print(name, [round(a, 3) for a in v]); CURVES[c] = v
    ax.plot(range(4), v, color=col, lw=2, marker="o", ms=7, mec=SURF, mew=2, zorder=3)
    off = {"S.aureus": 0.018, "PGE2": -0.018}.get(c, 0)
    ax.text(3.08, v[-1] + off, f"{name} {v[-1]:.2f}", va="center", fontsize=10.2, color=INK2)
ax.set_xticks(range(4), levels); ax.set_xlim(-0.2, 4.4); ax.set_ylim(0.45, 1.0)
ax.set_ylabel("예측 정확도 (AUC)"); ax.set_xlabel("예측에 사용한 계통 정보의 깊이")
ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.suptitle("그림 2. 계통 정보 깊이에 따른 효능 예측 정확도", x=0.01, ha="left", fontsize=14.4, fontweight="bold")
fig.text(0.01, 0.01, "학습에 쓰지 않은 종을 맞히는 조건(종 단위 5겹 교차검증). 목 수준까지만 알아도 성능 대부분이 확보됨.", fontsize=9.0, color=MUTED)
fig.tight_layout(rect=(0, 0.04, 1, 0.95))
fig.savefig(f"{OUT}/_old_계통깊이별정확도.png"); plt.close(fig)
print("fig2 done")

# ---------- 그림 3: 연간 50주 모의 비교 ----------
res = []
for name, d, c in [("황색포도상구균\n항균", A, "S.aureus"), ("바실러스 세레우스\n항균", A, "B.cereus"),
                   ("NO\n항염", A, "NO"), ("PGE2\n항염", A, "PGE2"), ("ABTS\n항산화", B, "ABTS")]:
    x = d[d[c].isin(["A", "B", "C"])]
    X = CountVectorizer(analyzer=lambda t: t).fit_transform(x["L"])
    y = (x[c] == "A").values.astype(int); g = x["학명"].values; p = np.zeros(len(y))
    for tr, te in GroupKFold(5).split(X, y, g):
        p[te] = LogisticRegression(max_iter=3000, class_weight="balanced").fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    mic = x["분류"].isin(["세균", "균류", "미세조류"]).values
    pm, ym = p[mic], y[mic]; top = np.argsort(-pm)[:50]
    res.append((name, 50 * ym.mean(), int(ym[top].sum())))
print(res)
fig, ax = plt.subplots(figsize=(7.6, 4.6), dpi=220)
xs = np.arange(len(res)); w = 0.36
for k, (name, rnd, pred) in enumerate(res):
    ax.bar(k - w / 2 - 0.01, rnd, w, color=NEUTRAL, zorder=3)
    ax.bar(k + w / 2 + 0.01, pred, w, color=S1, zorder=3)
    ax.text(k - w / 2 - 0.01, rnd + 0.15, f"{rnd:.1f}", ha="center", va="bottom", fontsize=10.2, color=INK2)
    ax.text(k + w / 2 + 0.01, pred + 0.15, f"{pred}", ha="center", va="bottom", fontsize=10.8, fontweight="bold", color=INK)
    ratio = pred / rnd
    ax.text(k, max(rnd, pred) + 1.3, f"×{ratio:.0f}" if ratio >= 2 else f"×{ratio:.1f}", ha="center", fontsize=10.8,
            color=S1 if ratio >= 2 else MUTED, fontweight="bold")
ax.set_xticks(xs, [r[0] for r in res], fontsize=10.2)
ax.set_ylabel("A등급 자원 수 (건)"); ax.set_ylim(0, 11)
ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=NEUTRAL, label="임의로 50주 선택 (기대값)"), Patch(color=S1, label="예측 상위 50주 선택 (실제)")],
          loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False, fontsize=10.2)
fig.suptitle("그림 3. 연간 미생물 분양 한도 50주 안에서 확보되는 A등급 자원 수", x=0.01, ha="left", fontsize=14.4, fontweight="bold")
fig.text(0.01, 0.01, "미생물 추출물 대상 모의 비교. 예측은 해당 종을 학습에서 제외하고 산출. 항산화는 효과가 작아 해조류·염생식물 계통 안내로 대체.", fontsize=9.0, color=MUTED)
fig.tight_layout(rect=(0, 0.04, 1, 0.93))
fig.savefig(f"{OUT}/_old_분양한도모의비교.png"); plt.close(fig)
print("fig3 done")

# ---------- 그림 4: 서비스 환류 구조 ----------
fig, ax = plt.subplots(figsize=(8.6, 3.9), dpi=220)
ax.set_xlim(0, 10); ax.set_ylim(0.35, 4.95); ax.axis("off")
boxes = {
    "data": (0.3, 3.3, "뱅크 효능 데이터", "효능 등급 추출물 8,808건\n실측 A/B/C 등급"),
    "model": (3.6, 3.3, "계통 기반 예측", "같은 계통의 시험 결과로\n미시험 자원의 효능 가능성 산출"),
    "show": (6.9, 3.3, "① 효능 가능성 표시\n② 목적별 추천", "실측과 예측을 구분 표시\n분양 한도 안 후보 제시"),
    "parcel": (6.9, 0.5, "분양·활용", "이용자 실험\n기업 소재 개발"),
    "feed": (3.6, 0.5, "④ 성과·시험 환류", "성과보고서 효능 확인 항목\n뱅크 신규 시험 결과"),
    "bridge": (0.3, 0.5, "③ 기업 창구 연동", "Mbio-Bridge 소재 DB\n수요매칭 상담 첨부"),
}
W, H = 2.8, 1.55
for key, (x, y, t, s) in boxes.items():
    hi = key in ("model", "show", "feed", "bridge")
    ax.add_patch(FancyBboxPatch((x, y), W, H, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc="#eaf2fc" if hi else "#f0efec", ec=S1 if hi else NEUTRAL, lw=1.6))
    ax.text(x + W / 2, y + H - 0.38, t, ha="center", va="center", fontsize=11.4, fontweight="bold", color=INK)
    ax.text(x + W / 2, y + 0.45, s, ha="center", va="center", fontsize=9.6, color=INK2, linespacing=1.4)


def arrow(p, q, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, lw=1.6, color=INK2,
                                 connectionstyle=f"arc3,rad={rad}"))


arrow((0.3 + W, 4.07), (3.6, 4.07)); arrow((3.6 + W, 4.07), (6.9, 4.07))
arrow((6.9 + W / 2, 3.3), (6.9 + W / 2, 0.5 + H)); arrow((6.9, 1.27), (3.6 + W, 1.27))
arrow((3.6 + W / 2, 0.5 + H), (3.6 + W / 2, 3.3)); arrow((0.3 + W / 2, 3.3), (0.3 + W / 2, 0.5 + H))
ax.text(5.12, 2.45, "월 1회 재학습", ha="left", va="center", fontsize=9.6, color=S1, fontweight="bold")
ax.text(1.9, 2.45, "기업 대상 제공", ha="left", va="center", fontsize=9.6, color=INK2)
fig.suptitle("그림 4. 효능 내비게이터 서비스 구조와 성과 환류", x=0.01, ha="left", fontsize=14.4, fontweight="bold")
fig.text(0.01, 0.01, "파란 테두리는 이번 제안으로 새로 추가되는 기능.", fontsize=9.0, color=MUTED)
fig.tight_layout(rect=(0, 0.03, 1, 0.95))
fig.savefig(f"{OUT}/그림4_서비스구조.png"); plt.close(fig)
print("fig4 done")


# ---------- 요약 수치 (본문용) ----------
summ = {"ncbi_genera": len(NCBI)}
aucs = {}
for d, cols_ in ((B, B.columns[2:9]), (A, A.columns[2:20]), (M, M.columns[2:7])):
    for c in cols_:
        x = d[d[c].isin(["A", "B", "C"])]
        y = (x[c] == "A").values.astype(int)
        if y.sum() < 15: continue
        X = CountVectorizer(analyzer=lambda t: t).fit_transform(x["L"]); g = x["학명"].values; p = np.zeros(len(y))
        for tr, te in GroupKFold(5).split(X, y, g):
            p[te] = LogisticRegression(max_iter=3000, class_weight="balanced").fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
        aucs[c] = round(float(roc_auc_score(y, p)), 3)
summ["auc"] = aucs; summ["auc_mean"] = round(float(np.mean(list(aucs.values()))), 3); summ["n_assays"] = len(aucs)
summ["sim50"] = [(n.replace(chr(10), " "), round(float(r), 3), int(q)) for n, r, q in res]
st = A[A["학명"].str.startswith("Streptomyces") & A["S.aureus"].isin(["A", "B", "C"])]
mic = A[A["분류"].isin(MICRO) & A["S.aureus"].isin(["A", "B", "C"])]
summ["strep"] = {"extracts": int(len(st)), "species": int(st["학명"].nunique()), "A_rate": round(float((st["S.aureus"] == "A").mean()), 3),
                 "micro_base": round(float((mic["S.aureus"] == "A").mean()), 4)}
json.dump(summ, open(f"{OUT}/_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(summ, ensure_ascii=False))


# ---------- 그림 1: EDA (분양 현황과 A등급 희소성) ----------
banks = [("미세조류", 2020, 414, 194), ("추출물", 2017, 4461, 1350), ("미생물", 2018, 10522, 453), ("대사질환", 2025, 600, 2),
         ("유전자원", 2019, 12199, 253), ("화장품", 2022, 1900, 8), ("항생제", 2023, 2219, 5)]
rate = [(n, h, c / (h / 1000) / (2025 - y + 1)) for n, y, h, c in banks]
cat = {"미백·주름": (B, ["Tyros", "DOPA", "Collag", "Elas"]), "항산화": (B, ["DPPH", "ABTS", "ROS"]),
       "항균": (A, ["S.aureus", "B.cereus", "E.faecalis", "E.coli", "Salmonella", "P.aerug"]), "항염": (A, ["NO", "PGE2"]),
       "항암": (A, ["AGS위", "A549폐", "HCT116대장", "HepG2간", "MCF7유방", "HT1080피부", "HL60혈액"]),
       "항바이러스": (A, ["H1N1", "코로나", "A형간염"]), "대사질환": (M, ["DPP4", "aGlu", "ORO", "TG", "ACE"])}
pts = []
for k, (d, cs) in cat.items():
    for c in cs:
        x = d[c][d[c].isin(["A", "B", "C"])]
        pts.append((k, c, (x == "A").mean() * 100))
med = float(np.median([v for _, _, v in pts]))
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.6, 3.3), dpi=220, gridspec_kw={"width_ratios": [1.05, 1]})
names = [f"{n}  (보유 {h:,})" for n, h, _ in rate]
vals = [v for _, _, v in rate]
hl = {"미생물", "유전자원"}
yy = np.arange(len(rate))[::-1]
for yv, (n, h, v) in zip(yy, rate):
    a1.barh(yv, v, height=0.62, color=S1 if n in hl else NEUTRAL, zorder=3)
    a1.text(v + 1.2, yv, f"{v:.1f}", va="center", fontsize=9.6, color=INK if n in hl else INK2, fontweight="bold" if n in hl else None)
a1.set_yticks(yy, names, fontsize=9.6); a1.set_xlim(0, 90); a1.tick_params(length=0)
a1.grid(axis="x", color=GRID, lw=0.8); a1.set_axisbelow(True)
for s_ in ("top", "right", "left"): a1.spines[s_].set_visible(False)
a1.set_xlabel("보유 1천 점당 연간 분양 건수", fontsize=10.2)
a1.set_title("(가) 뱅크별 분양 활용도", loc="left", fontsize=12.0, fontweight="bold")
a1.text(43, 2.0, "보유 자원이 가장 많은\n미생물·유전자원은\n활용도가 낮음", fontsize=9.6, color=S1, va="center")
order = list(cat.keys())
for i, k in enumerate(order):
    xs_ = [v for kk, _, v in pts if kk == k]
    a2.scatter(xs_, [len(order) - 1 - i] * len(xs_), s=34, color=S1, edgecolor=SURF, linewidth=1.2, zorder=3, alpha=0.9)
a2.axvline(med, color=S2, lw=1.4, ls=(0, (4, 3)), zorder=2)
a2.text(med + 0.3, -0.55, f"중앙값 {med:.1f}%", color=S2, fontsize=9.6, fontweight="bold", va="bottom")
a2.set_yticks(range(len(order)), order[::-1], fontsize=10.2); a2.tick_params(length=0)
a2.set_xlim(-0.6, 15); a2.set_ylim(-0.75, len(order) - 0.3)
a2.grid(axis="x", color=GRID, lw=0.8); a2.set_axisbelow(True)
for s_ in ("top", "right", "left"): a2.spines[s_].set_visible(False)
a2.set_xlabel("시험별 A등급 비율 (%)", fontsize=10.2)
a2.set_title("(나) 효능 시험 30종의 A등급 비율", loc="left", fontsize=12.0, fontweight="bold")
yk = len(order) - 1 - order.index("항균")
a2.text(0.0, yk - 0.42, "살모넬라 0.0%·대장균 0.1%", fontsize=8.2, color=INK2, va="center", zorder=5, bbox=dict(boxstyle="square,pad=0.1", fc=SURF, ec="none"))
fig.suptitle("그림 1. 분양 활용 현황과 A등급 자원의 희소성", x=0.01, ha="left", fontsize=14.4, fontweight="bold")
fig.text(0.01, 0.01, "(가) 누적 분양(2025년 말) ÷ 보유 수(2026년 10월) ÷ 운영 연수. 자료: MBRIS 통계현황   (나) 효능 등급 추출물 8,808건, 점 하나가 시험 1종", fontsize=8.4, color=MUTED)
fig.tight_layout(rect=(0, 0.035, 1, 0.965))
fig.savefig(f"{OUT}/그림1_EDA_분양현황과A등급.png"); plt.close(fig)
summ["eda"] = {"median_A": round(med, 1), "bank_rate": {n: round(v, 1) for n, _, v in rate}}
json.dump(summ, open(f"{OUT}/_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("eda done", med)

# ---------- 그림 3: 예측 정확도 + 50주 모의 비교 (나란히) ----------
fig, (b1, b2) = plt.subplots(1, 2, figsize=(8.6, 3.25), dpi=220, gridspec_kw={"width_ratios": [1, 1.1]})
lab = {"S.aureus": ("항균(포도상구균)", S1, 0.024), "PGE2": ("항염(PGE2)", S2, -0.024), "Collag": ("주름(콜라게나아제)", S3, 0), "H1N1": ("항바이러스(H1N1)", NEUTRAL, 0)}
b1.axhline(0.5, color=MUTED, lw=1, ls=(0, (4, 3)))
b1.text(0.0, 0.515, "무작위 0.5", fontsize=9.0, color=MUTED, va="bottom")
for c, v in CURVES.items():
    nm, col, off = lab[c]
    b1.plot(range(4), v, color=col, lw=2, marker="o", ms=6, mec=SURF, mew=1.5, zorder=3)
    b1.text(3.12, v[-1] + off, f"{nm} {v[-1]:.2f}", va="center", fontsize=9.0, color=INK2)
b1.set_xticks(range(4), ["대분류", "문~목", "과", "속"], fontsize=9.6); b1.set_xlim(-0.25, 5.6); b1.set_ylim(0.45, 1.0)
b1.set_ylabel("AUC", fontsize=10.2); b1.tick_params(labelsize=8)
b1.grid(axis="y", color=GRID, lw=0.8); b1.set_axisbelow(True)
for s_ in ("top", "right"): b1.spines[s_].set_visible(False)
b1.set_title("(가) 계통 정보 깊이별 예측 정확도", loc="left", fontsize=12.0, fontweight="bold")
w = 0.36
short = ["포도상구균\n항균", "세레우스\n항균", "NO\n항염", "PGE2\n항염", "ABTS\n항산화"]
for k, (name, rnd, pred) in enumerate(res):
    b2.bar(k - w / 2 - 0.01, rnd, w, color=NEUTRAL, zorder=3)
    b2.bar(k + w / 2 + 0.01, pred, w, color=S1, zorder=3)
    b2.text(k - w / 2 - 0.01, rnd + 0.15, f"{rnd:.1f}", ha="center", va="bottom", fontsize=8.4, color=INK2)
    b2.text(k + w / 2 + 0.01, pred + 0.15, f"{pred}", ha="center", va="bottom", fontsize=9.6, fontweight="bold", color=INK)
    r_ = pred / rnd
    b2.text(k, max(rnd, pred) + 1.25, f"×{r_:.0f}" if r_ >= 2 else f"×{r_:.1f}", ha="center", fontsize=9.6, color=S1 if r_ >= 2 else MUTED, fontweight="bold")
b2.set_xticks(range(len(res)), short, fontsize=9.0); b2.set_ylim(0, 13.2); b2.tick_params(labelsize=8)
b2.set_ylabel("A등급 자원 수 (건)", fontsize=10.2)
b2.grid(axis="y", color=GRID, lw=0.8); b2.set_axisbelow(True)
for s_ in ("top", "right"): b2.spines[s_].set_visible(False)
from matplotlib.patches import Patch
b2.legend(handles=[Patch(color=NEUTRAL, label="임의 50주 (기대값)"), Patch(color=S1, label="예측 상위 50주 (실제)")],
          loc="upper center", bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=9.0, ncol=2)
b2.set_title("(나) 연간 미생물 한도 50주 안의 A등급 수", loc="left", fontsize=12.0, fontweight="bold")
fig.suptitle("그림 3. 계통 기반 예측의 정확도와 분양 한도 안에서의 효과", x=0.01, ha="left", fontsize=14.4, fontweight="bold")
fig.text(0.01, 0.01, "학습에 쓰지 않은 종을 맞히는 조건(종 단위 5겹 교차검증). (나)는 미생물 추출물 대상 모의 비교.", fontsize=8.4, color=MUTED)
fig.tight_layout(rect=(0, 0.035, 1, 0.965))
fig.savefig(f"{OUT}/그림3_예측정확도_모의비교.png"); plt.close(fig)
print("fig3 combined done")
