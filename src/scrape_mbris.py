"""MBRIS 효능 뱅크 목록 수집 (서버 렌더링 테이블, pageUnit=100, 요청 간 1초 대기)."""
import re, sys, time, html, csv, urllib.request, urllib.parse

sys.stdout.reconfigure(encoding="utf-8")
OUT = sys.argv[1]
BANKS = sys.argv[2:] or ["extractBeautyBank", "extractAntiBac", "extractMtblsmDiss"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128"


def fetch(bank, page):
    data = urllib.parse.urlencode({"pageIndex": page, "pageUnit": 100}).encode()
    req = urllib.request.Request(f"https://www.mbris.kr/biobank/{bank}/search.do", data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def cells(tr):
    tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
    return [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip() for t in tds]


for bank in BANKS:
    first = fetch(bank, 1)
    total = int(re.search(r"총 ([\d,]+)건", first).group(1).replace(",", ""))
    pages = (total + 99) // 100
    rows = []
    for p in range(1, pages + 1):
        s = first if p == 1 else fetch(bank, p)
        tbs = re.findall(r"<tbody[^>]*>(.*?)</tbody>", s, re.S)
        for tb in tbs:
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S):
                c = cells(tr)
                if any(x.startswith("MABIK") for x in c):
                    rows.append(c)
        print(bank, p, "/", pages, len(rows), flush=True)
        time.sleep(1)
    with open(f"{OUT}/{bank}.csv", "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)
    print("DONE", bank, total, len(rows), flush=True)
