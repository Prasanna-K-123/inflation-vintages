import concurrent.futures,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IDS={2022:[1798312,1805838,1816066,1824772,1833536,1840945,1851273,1858724,1867095,1875824,1882801,1890750],
     2023:[1898820,1906436,1915936,1923709,1931707,1938980,1948574,1956659,1967118,1976688,1985492,1995548],
     2024:[2005313,2013793,2017771,2020447,2024761,2032780,2044604,2054203,2064700,2072719,2083704,2092477],
     2025:[2102267,2110779,2121843,2128387,2135927,2144511,2155476,2165974,2178447,2189186,2202940,2213736]}

def acquire():
    raw=ROOT/'data/raw';raw.mkdir(parents=True,exist_ok=True)
    jobs=[(f'{year}-{month:02d}',pid) for year,ids in IDS.items() for month,pid in enumerate(ids,1)]
    jobs.append(('2026-01_new_base',2227012))
    def get(job):
        month,pid=job;url=f'https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID={pid}&lang=2&reg=3';f=raw/f'source_{pid}.html'
        try:
            if not f.exists():
                with urllib.request.urlopen(url,timeout=30) as r:b=r.read()
                if b'Consumer Price' not in b and b'CONSUMER PRICE' not in b:raise ValueError('Not a CPI document')
                f.write_bytes(b)
            b=f.read_bytes()
            return {'reference_month':month,'prid':pid,'url':url,'file':str(f.relative_to(ROOT)),
                    'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'retrieved_utc_date':'2026-10-17'}
        except Exception as e:return {'reference_month':month,'prid':pid,'url':url,'error':type(e).__name__+': '+str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=[]
        for item in pool.map(get,jobs):results.append(item);print(json.dumps({k:item[k] for k in item if k in ['reference_month','bytes','error']}),flush=True)
    (ROOT/'data/source_manifest.json').write_text(json.dumps(results,indent=2)+'\n')
    return results

if __name__=='__main__':acquire()
