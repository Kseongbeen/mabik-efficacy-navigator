"""학명으로 추출물 뱅크를 검색해 각 추출물의 상세 JSON(채집일·좌표·용매·전 효능등급)을 수집."""
import re, sys, time, json, urllib.request, urllib.parse

sys.stdout.reconfigure(encoding="utf-8")
OUT, SPECIES = sys.argv[1], sys.argv[2]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128", "X-Requested-With": "XMLHttpRequest"}
BANKS = ["extractBank", "extractBeautyBank", "extractAntiBac", "extractMtblsmDiss"]


def get(url, data=None):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data else None, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


# 일반 추출물 뱅크는 학명 검색이 되므로 그걸로 maresId 수집
ids = set()
page = 1
while True:
    s = get("https://www.mbris.kr/biobank/extractBank/search.do",
            {"pageIndex": page, "pageUnit": 100, "searchCnd": "sp", "searchWrd": SPECIES})
    found = re.findall(r'maresId="(MRS\d+)"', s)
    ids.update(found)
    total = int(re.search(r"총 ([\d,]+)건", s).group(1).replace(",", ""))
    print("list page", page, "total", total, "ids", len(ids), flush=True)
    if page * 100 >= total:
        break
    page += 1
    time.sleep(1)

rows = []
for i, mid in enumerate(sorted(ids)):
    d = json.loads(get(f"https://www.mbris.kr/biobank/extractBank/openMaresPopDetail.ajax?maresId={mid}&maresTyp=EXT"))
    rows.append(d)
    if i % 20 == 0:
        print("detail", i, len(ids), flush=True)
    time.sleep(1)

with open(f"{OUT}/detail_{SPECIES.replace(' ', '_')}.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False)
print("DONE", len(rows))
