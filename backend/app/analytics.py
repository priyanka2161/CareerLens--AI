from collections import Counter
from itertools import combinations
from .extraction import BY_NAME

def analytics(jobs):
    total=len(jobs);counts=Counter();roles={};locations={};pairs=Counter();salaries=[]
    for j in jobs:
        s=set(j['structured']['required_skills']+j['structured']['preferred_skills']);counts.update(sorted(s))
        roles.setdefault(j['title'],Counter()).update(sorted(s));locations.setdefault(j['location'],Counter()).update(sorted(s));pairs.update(combinations(sorted(s),2))
        if j.get('salary_min') is not None and j.get('salary_max') is not None:
            salaries.append({'title':j['title'],'midpoint':(j['salary_min']+j['salary_max'])/2,'years':j['structured']['years_experience'],'skills':sorted(s),'currency':j.get('currency'),'period':j.get('salary_period')})
    top=[s for s,_ in counts.most_common(15)]
    matrix=[[counts[a] if a==b else pairs.get(tuple(sorted((a,b))),0) for b in top] for a in top]
    return {'count':total,'sample_count':sum(j.get('is_sample',False) for j in jobs),'source_label':'Authored demo + user-imported postings; not representative of the job market','skills':[{'skill':s,'count':c,'percent':round(100*c/total,1) if total else 0,'category':BY_NAME[s]['category']} for s,c in counts.most_common()],'by_role':{r:dict(c) for r,c in roles.items()},'by_location':{r:dict(c) for r,c in locations.items()},'role_distribution':dict(Counter(j['title'] for j in jobs)),'cooccurrence':{'skills':top,'matrix':matrix,'meaning':'Number of postings mentioning both skills, not causation or proof of prerequisites.'},'salary':salaries}

def learning(profile,jobs):
    owned=set(profile['skills']);allskills=set(s for j in jobs for s in j['structured']['required_skills']+j['structured']['preferred_skills']);n=len(jobs)
    out=[]
    for skill in allskills-owned:
        required=sum(skill in j['structured']['required_skills'] for j in jobs)
        mentioned=sum(skill in j['structured']['required_skills']+j['structured']['preferred_skills'] for j in jobs)
        # Exact marginal improvement in required-skill coverage, averaged over all jobs.
        gain=sum(1/len(j['structured']['required_skills']) for j in jobs if skill in j['structured']['required_skills'])/n if n else 0
        near=any(BY_NAME[s]['category']==BY_NAME[skill]['category'] for s in owned)
        out.append({'skill':skill,'required_percent':round(required/n*100,1),'mentioned_percent':round(mentioned/n*100,1),'coverage_gain':round(gain*100,2),'priority':'High' if required/n>=.3 else 'Medium' if required else 'Low','related_foundation':near,'reason':f'Required in {required} of {n} selected postings. Learning this skill could add {gain*100:.1f} percentage points of mean required-skill coverage; it does not guarantee proficiency or a job.'})
    return sorted(out,key=lambda x:(-x['coverage_gain'],-x['mentioned_percent'],-int(x['related_foundation']),x['skill']))
