"""MBRIS 구전/문헌 전통지식 목록 수집 (4,118건, pageUnit=100, 요청 간 1초)."""
import re, sys, time, html, csv, urllib.request, urllib.parse

sys.stdout.reconfigure(encoding="utf-8")
OUT = sys.argv[1]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128"
URL = "https://www.mbris.kr/pub/info/traditionalN/oralLiterSearch.do"


def fetch(page):
    data = urllib.parse.urlencode({"pageIndex": page, "pageUnit": 100, "searchChk": "O"}).encode()
    req = urllib.request.Request(URL, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


rows, page, pages = [], 1, 1
while page <= pages:
    s = fetch(page)
    if page == 1:
        pages = (int(re.search(r"총\s*([\d,]+)건", s).group(1).replace(",", "")) + 99) // 100
    seg = s[s.find("구전/문헌 조사 - 번호"):]
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", seg, re.S)[1:]:
        c = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip() for t in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(c) >= 6 and c[0].isdigit():
            rows.append(c[:6])
    print(page, "/", pages, len(rows), flush=True)
    page += 1
    time.sleep(1)

with open(f"{OUT}/oral_tk.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["번호", "학명", "국명", "구분", "이용용도", "이용지식"])
    w.writerows(rows)
print("DONE", len(rows))
