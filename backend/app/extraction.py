"""Conservative, evidence-preserving extraction; uncertainty is explicit."""
import json, re, unicodedata
from datetime import date
from .config import DATA
TAXONOMY = json.loads((DATA / 'skills.json').read_text())
BY_NAME = {s['name']: s for s in TAXONOMY}
PATTERNS = [(s, re.compile(r'(?<![\w+])(?:'+ '|'.join(re.escape(a) for a in sorted(s['aliases'],key=len,reverse=True)) +r')(?![\w+])', re.I)) for s in TAXONOMY]
HEADINGS = {'summary':'summary','profile':'summary','objective':'summary','skills':'skills','technical skills':'skills','core competencies':'skills','experience':'experience','work experience':'experience','professional experience':'experience','employment history':'experience','projects':'projects','project experience':'projects','education':'education','academic qualifications':'education','certifications':'certifications','certificates':'certifications'}
def clean(text):
    return '\n'.join(re.sub(r'[ \t]+',' ',line).strip() for line in unicodedata.normalize('NFKC',text).replace('\x00','').splitlines()).strip()
def sections(text):
    result={k:[] for k in set(HEADINGS.values())}; current='summary'
    for line in text.splitlines():
        h=line.strip(' :•-').lower()
        if h in HEADINGS: current=HEADINGS[h]; continue
        if line.strip(): result[current].append(line.strip())
    return result

def skill_evidence(text):
    found={}
    for line in text.splitlines():
        for skill,pattern in PATTERNS:
            for m in pattern.finditer(line):
                # Conservative scoped negation. Keep absence separate from evidence of proficiency.
                prefix=line[max(0,m.start()-55):m.start()].lower()
                if re.search(r'(?:\bno\b|\bnot\b|\bwithout\b|\black\w*\b|\blearning\b|\bwant to learn\b)[^.;:]*$',prefix): continue
                if skill['name']=='R' and m.group().lower()=='r' and not re.search(r'(?:skills|python|sql|languages|\bR\b[,/])',line): continue
                found.setdefault(skill['name'],{'skill':skill['name'],'category':skill['category'],'evidence':line[:700],'matched_text':m.group(),'confidence':'explicit'})
                break
    return list(found.values())

def degree(text):
    for name,pat in [('doctorate',r'\b(ph\.?d\.?|doctorate|doctoral)\b'),('masters',r'\b(master\w*|m\.?tech|m\.?sc|mba|m\.s\.)\b'),('bachelors',r'\b(bachelor\w*|b\.?tech|b\.?sc|b\.s\.)\b'),('associate',r'\b(associate|diploma)\b')]:
        if re.search(pat,text,re.I): return name
    return None

def explicit_years(text):
    m=re.search(r'(?<!\d)(\d{1,2})(?:\s*[-–]\s*\d{1,2})?\s*\+?\s*years?\s*(?:of\s+)?(?:professional\s+|relevant\s+|work\s+)?experience',text,re.I)
    return float(m.group(1)) if m else None

def experience_duration(lines):
    text='\n'.join(lines); years=explicit_years(text)
    if years is not None: return years,'explicit statement'
    months={'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
    pat=r'\b([A-Za-z]{3,9})\s+(\d{4})\s*[-–—]\s*(?:([A-Za-z]{3,9})\s+(\d{4})|(present|current))\b'
    intervals=[]; now=date.today(); limit=now.year*12+now.month
    for m in re.finditer(pat,text,re.I):
        a=months.get(m[1][:3].lower()); b=months.get((m[3] or '')[:3].lower())
        if not a or (not m[5] and not b): continue
        start=int(m[2])*12+a; end=limit if m[5] else int(m[4])*12+b
        if 1950*12 <= start <= end <= limit: intervals.append((start,end+1))
    if not intervals: return None,'not detected; year-only or ambiguous dates are not guessed'
    merged=[]
    for a,b in sorted(intervals):
        if merged and a<=merged[-1][1]: merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else: merged.append((a,b))
    return round(sum(b-a for a,b in merged)/12,1),'union of month-level employment intervals; may include internships'

def resume(text):
    text=clean(text); sec=sections(text); ev=skill_evidence(text)
    # Contact and education organization strings never enter semantic matching.
    years=explicit_years('\n'.join(sec['summary']+sec['experience']))
    source='explicit statement' if years is not None else ''
    if years is None: years,source=experience_duration(sec['experience'])
    first=next((l for l in text.splitlines() if l.strip()),'')
    name=first if re.fullmatch(r'[A-Za-z][A-Za-z .\'-]{2,70}',first) and len(first.split()) in range(2,5) and not skill_evidence(first) and first.lower() not in HEADINGS else None
    universities=[l for l in sec['education'] if re.search(r'\b(university|institute|college)\b',l,re.I)]
    semantic=[]
    for l in sec['summary']+sec['experience']+sec['projects']:
        if l==name or re.search(r'@|https?://|\b(university|college|gender|married|nationality|born|religion)\b',l,re.I): continue
        if skill_evidence(l) or re.search(r'\b(built|developed|analyzed|analysed|designed|trained|deployed|evaluated|managed)\b',l,re.I):
            l=re.sub(r'\b(?:19|20)\d{2}\b|\b\d+(?:\.\d+)?\s*years?\b','',l,flags=re.I)
            semantic.append(l)
    result={'name':name,'education':sec['education'],'degree':degree('\n'.join(sec['education'])),'university':universities,'skills':[e['skill'] for e in ev],'skill_evidence':ev,'projects':sec['projects'],'work_experience':sec['experience'],'certifications':sec['certifications'],'years_experience':years,'experience_source':source,'semantic_text':'\n'.join(semantic) or ', '.join(e['skill'] for e in ev),'warnings':['Extraction is heuristic. Review the JSON and source evidence; undetected does not mean absent.','Scanned PDFs require OCR before upload.']}
    for field,cat in [('programming_languages','languages'),('frameworks','frameworks'),('databases','databases'),('cloud_technologies','cloud'),('ml_technologies','ml')]: result[field]=[e['skill'] for e in ev if e['category']==cat]
    checks={'skills':bool(ev),'education':bool(sec['education']),'experience':bool(sec['experience']),'projects':bool(sec['projects']),'experience_duration':years is not None}
    result['health']={'score':round(100*sum(checks.values())/len(checks)),'checks':checks,'label':'Extraction completeness, not resume quality'}
    return result

def job(text):
    text=clean(text); required={};preferred={}; mode='required';responsibilities=[]
    for line in text.splitlines():
        chunks=re.split(r'(?i)(?=\b(?:preferred|nice[- ]to[- ]have|bonus|optional|not required)\s*[:;])',line)
        for chunk in chunks:
            if re.search(r'(?i)\b(preferred|nice[- ]to[- ]have|bonus|optional|not required)\b',chunk): mode='preferred'
            elif re.search(r'(?i)\b(required|must have|minimum|essential|responsibilities)\b',chunk): mode='required'
            for e in skill_evidence(chunk): (preferred if mode=='preferred' else required)[e['skill']]=e
        if re.search(r'(?i)responsibilit|\b(build|develop|analyze|analyse|deploy|design|maintain|evaluate)\b',line): responsibilities.append(line)
    for k in required: preferred.pop(k,None)
    education_lines=[l for l in text.splitlines() if re.search(r'(?i)degree|bachelor|master|phd|ph.d|b.tech',l)]
    mandatory_edu=[l for l in education_lines if not re.search(r'(?i)preferred|optional|equivalent|nice.to.have|not required',l)]
    years=explicit_years(text)
    if re.search(r'(?i)no (?:prior )?experience required|freshers? welcome|entry.level',text): years=0.0
    seniority=next((s for s in ['principal','lead','senior','junior','graduate','intern'] if re.search(r'\b'+s+r'\b',text,re.I)), 'unspecified')
    title=text.splitlines()[0][:150]
    return {'title':title,'required_skills':list(required),'preferred_skills':list(preferred),'skill_evidence':list(required.values())+list(preferred.values()),'years_experience':years,'education_requirements':education_lines,'degree_required':degree('\n'.join(mandatory_edu)),'responsibilities':responsibilities,'domain':next((s for s in ['finance','healthcare','marketing','sales'] if re.search(r'\b'+s+r'\b',text,re.I)),'unspecified'),'seniority':seniority,'semantic_text':'\n'.join(responsibilities) or text,'warnings':['Unqualified skill mentions are treated as required; review ambiguous phrasing. Alternative requirements (A or B) need manual review.'],'categories':{c:[e['skill'] for e in list(required.values())+list(preferred.values()) if e['category']==c] for c in ['languages','frameworks','tools','cloud','ml','databases']}}
