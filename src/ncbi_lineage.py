"""미생물·미세조류 속(genus)의 NCBI Taxonomy 계통(문~과)을 받아 저장. 초당 3회 이하로 요청."""
import sys, time, json, re, urllib.request, urllib.parse
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
DATA = sys.argv[1]
B = pd.read_pickle(f"{DATA}/B.pkl"); A = pd.read_pickle(f"{DATA}/A.pkl"); M = pd.read_pickle(f"{DATA}/M.pkl")
mo = pd.read_csv(f"{DATA}/microOrganBank.csv", header=None, encoding="utf-8-sig")
ma = pd.read_csv(f"{DATA}/microAlgaeBank.csv", header=None, encoding="utf-8-sig")
gen = set()
for d in (B, A, M):
    x = d[d["분류"].isin(["세균", "균류", "미세조류"])]["학명"].dropna()
    gen |= set(x.str.split().str[0])
for d in (mo, ma):
    gen |= set(d[1].astype(str).str.extract(r"^([A-Z][a-z]+)")[0].dropna())
gen = sorted(gen)
print("genera", len(gen), flush=True)

E = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
def get(url):
    for k in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read().decode("utf-8")
        except Exception:
            time.sleep(2)
    return ""

ids = {}
for i, g in enumerate(gen):
    q = urllib.parse.quote(f"{g}[Scientific Name] AND genus[Rank]")
    s = get(f"{E}esearch.fcgi?db=taxonomy&term={q}&retmode=json")
    try:
        lst = json.loads(s)["esearchresult"]["idlist"]
        if lst: ids[g] = lst[0]
    except Exception:
        pass
    time.sleep(0.35)
    if i % 100 == 0: print("search", i, len(ids), flush=True)

json.dump(ids, open(f"{DATA}/ncbi_genus_ids.json", "w", encoding="utf-8"))
import xml.etree.ElementTree as ET
out = {}
items = list(ids.items())
for k in range(0, len(items), 100):
    chunk = items[k:k + 100]
    x = get(f"{E}efetch.fcgi?db=taxonomy&id={','.join(t for _, t in chunk)}&retmode=xml")
    try:
        root = ET.fromstring(x)
    except Exception:
        continue
    for tx in root.findall("Taxon"):
        name = tx.findtext("ScientificName")
        lin = {}
        for a in tx.findall("LineageEx/Taxon"):
            rk = a.findtext("Rank")
            if rk in ("phylum", "class", "order", "family"):
                lin[rk] = a.findtext("ScientificName")
        out[name] = [lin[r] for r in ("phylum", "class", "order", "family") if r in lin]
    time.sleep(0.4)
    print("fetch", k, len(out), flush=True)

json.dump(out, open(f"{DATA}/ncbi_genus_lineage.json", "w", encoding="utf-8"), ensure_ascii=False)
print("DONE", len(gen), len(ids), len(out))
