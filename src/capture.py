"""참고자료 페이지를 헤드리스 크롬으로 PDF 저장. 각 실행 후 해당 크롬 프로세스를 정리."""
import subprocess, sys, os, time, shutil

sys.stdout.reconfigure(encoding="utf-8")
OUT = sys.argv[1]
CH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PAGES = [
    ("01g_MBRIS_QnA목록", "https://www.mbris.kr/biobank/cust/qna.do"),
    ("16_KOSA_2026평균임금", "https://www.sw.or.kr/site/kipa/ex/board/View.do?cbIdx=304&bcIdx=64717&gubun=G"),
    ("01e_MBRIS_통계_보유자원", "https://www.mbris.kr/biobank/main/holdingRes.do"),
    ("01f_MBRIS_통계_분양현황", "https://www.mbris.kr/biobank/main/currentParcel.do"),
    ("01b_MBRIS_뱅크소개", "https://www.mbris.kr/biobank/about/introduceBioBank.do"),
    ("01_MBRIS_자원분양현황", "https://www.mbris.kr/pub/marine/statis/statParcels.do"),
    ("02_MBRIS_분양안내", "https://www.mbris.kr/biobank/about/guide.do"),
    ("03_MBRIS_성과현황", "https://www.mbris.kr/biobank/cust/performStatusBoard.do"),
    ("04_MBRIS_화장품효능뱅크검색", "https://www.mbris.kr/biobank/extractBeautyBank/search.do"),
    ("05_MBRIS_미생물뱅크검색", "https://www.mbris.kr/biobank/microOrganBank/search.do"),
    ("06_MbioBridge_주요소재DB", "https://www.mabik.re.kr/mbiob/prog/oceanBioMatr/kor/sub02_01/list.do"),
    ("07_MbioBridge_기업수요매칭", "https://www.mabik.re.kr/mbiob/prog/mtchgSrvcAply/kor/sub02_02/main.do"),
    ("08_PNAS2012_계통기반예측", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3465383/"),
    ("09_NAR2025_BacDive", "https://pmc.ncbi.nlm.nih.gov/articles/PMC11701647/"),
    ("10_NCI_NPNPD", "https://dtp.cancer.gov/organization/npb/npnpd_prefractionated_library.htm"),
    ("11_데일리안_호남권AI", "https://www.dailian.co.kr/news/view/1698072/"),
    ("12_푸드투데이_국감상용화", "https://www.foodtoday.or.kr/news/article.html?no=208667"),
    ("13_아시아경제_바이오데이터", "https://www.asiae.co.kr/article/2025123010000316334"),
    ("14_공공데이터_채집공간정보", "https://www.data.go.kr/data/15151832/fileData.do"),
    ("15_공공데이터_화장품효능", "https://www.data.go.kr/data/15163752/fileData.do"),
]
for name, url in PAGES:
    out = os.path.join(OUT, name + ".pdf")
    if os.path.exists(out) and os.path.getsize(out) > 5000:
        print("skip", name); continue
    prof = os.path.join(OUT, "prof_" + name[:3])
    cmd = [CH, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
           f"--user-data-dir={prof}", "--virtual-time-budget=5000", "--no-pdf-header-footer", f"--print-to-pdf={out}", url]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 60:
        if os.path.exists(out) and os.path.getsize(out) > 0:
            time.sleep(2); break
        time.sleep(1)
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    f"Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object {{ $_.CommandLine -like '*prof_{name[:3]}*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    shutil.rmtree(prof, ignore_errors=True)
    print(name, os.path.getsize(out) if os.path.exists(out) else "FAIL", f"{time.time()-t0:.0f}s", flush=True)
