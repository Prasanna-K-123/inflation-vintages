import calendar,hashlib,json,re
from datetime import datetime,timedelta,timezone
from pathlib import Path
from lxml import html
from header_columns import ordered_cells
ROOT=Path(__file__).resolve().parents[1]
IST=timezone(timedelta(hours=5,minutes=30))
MONTHS={name.lower():j for j,name in enumerate(calendar.month_name) if name}

def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n')

def shifted(month,offset):
    year,m=map(int,month.split('-'));n=year*12+m-1+offset
    return f'{n//12}-{n%12+1:02d}'

def normal(el):return ' '.join(' '.join(el.itertext()).split())

def publication(tree):
    els=tree.xpath('//*[contains(@class,"ReleaseDateSubHeaddateTime")]')
    found=[]
    for el in els:
        s=normal(el);m=re.search(r'(\d{1,2})\s+([A-Z]{3})\s+(\d{4})\s+(\d{1,2}):(\d{2})\s*(AM|PM)',s,re.I)
        if m:
            day,mon,year,hour,minute,ap=m.groups();h=int(hour)%12+(12 if ap.upper()=='PM' else 0)
            found.append(datetime(int(year),list(calendar.month_abbr).index(mon.title()),int(day),h,int(minute),tzinfo=IST).isoformat())
    if not found or len(set(found))!=1:raise ValueError('Missing/conflicting PIB publication time')
    return found[0]

def headline_candidates(tree,reference_month=None):
    result=[]
    for tr in tree.xpath('//tr'):
        els=tr.xpath('./th|./td');texts=[normal(x) for x in els]
        if not any(re.fullmatch(r'CPI\s*\(General\)',t,re.I) for t in texts):continue
        numeric=[];numeric_els=[]
        for t,x in zip(texts,els):
            if re.fullmatch(r'-?\d+(?:\.\d+)?',t):numeric.append(float(t));numeric_els.append(x)
        if len(numeric)!=9 or not all(abs(x)<50 for x in numeric):continue
        table=tr.xpath('ancestor::table[1]')[0];head=normal(table)
        ordered=ordered_cells(table,tr,numeric_els,reference_month)
        numeric=[float(normal(x)) for x in ordered]
        result.append({'numbers':numeric,'numeric_cells':[tree.getroottree().getpath(x) for x in ordered],
                       'row_xpath':tree.getroottree().getpath(tr),'header_excerpt':head[:650]})
    return result

def run():
    sources=json.loads((ROOT/'data/source_manifest.json').read_text())
    if len(sources)!=49 or any('error' in s for s in sources):raise ValueError('Source manifest incomplete')
    records=[];releases=[];audit=[]
    for source in sources:
        b=(ROOT/source['file']).read_bytes()
        if hashlib.sha256(b).hexdigest()!=source['sha256']:raise ValueError('Cached source bytes changed')
        tree=html.fromstring(b);pub=publication(tree);text=normal(tree)
        source_ref=source['reference_month']
        if source_ref.endswith('_new_base'):
            if not re.search(r'(?:Base|base)(?:\s+year)?\s*2024\s*=\s*100',text):raise ValueError('New base not documented')
            if '2.75' not in text or '2026' not in text:raise ValueError('New base headline absent')
            dump(ROOT/'reports/base_break.json',{'reference_month':'2026-01','published_at':pub,'source_url':source['url'],
                'source_sha256':source['sha256'],'base':2024,'first_published_headline_yoy':2.75,
                'use':'Measurement-break documentation only, not spliced into old-base forecast series',
                'backcast_rule':'2025 observations in base2024 first published2026 cannot enter2025 forecasts'})
            continue
        found=re.search(r'(?:for\s+the\s+month\s+of|month\s+of)\s*([A-Za-z]+)\s*,?\s*(20\d{2})',text,re.I)
        if not found:raise ValueError('Reference month absent: '+source_ref)
        month=f'{found.group(2)}-{MONTHS[found.group(1).lower()]:02d}'
        if month!=source_ref:raise ValueError(f'Reference mismatch {source_ref} vs {month}')
        if not re.search(r'2012\s*=\s*100',text):raise ValueError('Old base absent')
        candidates=headline_candidates(tree,month)
        if not candidates:raise ValueError('No explicit headline CPI9-value inflation row: '+month)
        vals={tuple(c['numbers']) for c in candidates}
        if len(vals)!=1:raise ValueError('Conflicting duplicate CPI tables: '+month)
        chosen=candidates[0];numbers=chosen['numbers']
        locator=chosen['numeric_cells']
        for offset,index,status in [(0,2,'provisional'),(-1,5,'final'),(-12,8,'prior_year_reference')]:
            records.append({'reference_month':shifted(month,offset),'published_at':pub,'value':numbers[index],
                'metric':'headline_yoy_percent','sector':'Combined','base':2012,'status':status,
                'release_reference_month':month,'source_url':source['url'],'source_file':source['file'],
                'source_sha256':source['sha256'],'cell_xpath':locator[index]})
        releases.append({'reference_month':month,'published_at':pub,'first_provisional':numbers[2],
                         'previous_month_final':numbers[5],'prior_year_as_reported':numbers[8],
                         'source_url':source['url'],'source_sha256':source['sha256']})
        audit.append({'reference_month':month,'duplicate_equivalent_rows':len(candidates),'chosen_row':chosen['row_xpath'],
                      'numbers_rural_urban_combined_for_current_previous_prior_year':numbers,
                      'header_excerpt':chosen['header_excerpt']})
    releases.sort(key=lambda x:x['reference_month']);records.sort(key=lambda x:(x['reference_month'],x['published_at']))
    expected=[f'{y}-{m:02d}' for y in range(2022,2026) for m in range(1,13)]
    if [r['reference_month'] for r in releases]!=expected:raise ValueError('Monthly archive gaps/duplicate release')
    times=[datetime.fromisoformat(r['published_at']) for r in releases]
    if not all(b>a for a,b in zip(times,times[1:])):raise ValueError('Release chronology')
    if len({(r['reference_month'],r['published_at'],r['metric'],r['base']) for r in records})!=len(records):raise ValueError('Duplicate vintage keys')
    corrections=[]
    for r,n in zip(releases,releases[1:]):
        if shifted(r['reference_month'],1)!=n['reference_month']:raise ValueError('Month adjacency')
        corrections.append({'reference_month':r['reference_month'],'provisional':r['first_provisional'],
                            'next_release_final':n['previous_month_final'],
                            'revision_percentage_points':round(n['previous_month_final']-r['first_provisional'],10)})
    dump(ROOT/'data/processed/vintages.json',records);dump(ROOT/'data/processed/releases.json',releases)
    dump(ROOT/'reports/extraction_audit.json',audit);dump(ROOT/'reports/revisions.json',corrections)
    result={'accepted_archive_months':48,'vintage_records':len(records),'source_documents':49,'base2012_first_release_range':['2022-01','2025-12'],
        'publication_time_zone':'IST +05:30; conservative PIB timestamp','all_source_hashes_checked':True,
        'duplicate_equivalent_source_rows_collapsed':sum(a['duplicate_equivalent_rows']-1 for a in audit),
        'reference_or_base_conflicts':0,'missing_months':0,'provisional_final_changes':sum(abs(r['revision_percentage_points'])>1e-10 for r in corrections),
        'max_abs_revision_percentage_points':max(abs(r['revision_percentage_points']) for r in corrections),
        'new_base_2024_separate':True,'forecast_metrics_computed':False,
        'limitation':'Publication-dated reconstructed vintages, not immutable contemporaneously archived snapshots',
        'input_use':'Official public statistical releases used as attributed research sources; no third-party raw-data relicensing'}
    dump(ROOT/'reports/data_audit.json',result);print(json.dumps(result,indent=2))
    for r in releases:print(r['reference_month'],r['published_at'],r['first_provisional'],r['previous_month_final'])

if __name__=='__main__':run()
