"""Equal factor priors, explicit unknowns, auditable evidence, no probabilistic claims."""
from .embeddings import similarity,get_encoder
from .extraction import BY_NAME
VERSION='equal-prior-v1'
FACTORS=['skills','semantic','experience','education','projects']
DEGREES={'associate':1,'bachelors':2,'masters':3,'doctorate':4}

def match(profile,job,encoder=None):
    encoder=encoder or get_encoder(); owned=set(profile['skills']);required=set(job['required_skills']);preferred=set(job['preferred_skills']);targets=required|preferred
    matched=sorted(targets&owned);missing=sorted(targets-owned)
    # All explicitly required skills have equal value; preferences are surfaced, not scored as requirements.
    skill_score=len(required&owned)/len(required) if required else (len(preferred&owned)/len(preferred) if preferred else None)
    yrs=profile['years_experience']; need=job['years_experience']
    experience=None if need is None or yrs is None else (1 if need==0 else min(1,yrs/need))
    pd=profile['degree'];jd=job['degree_required']
    education=None if jd is None or pd is None else (1.0 if DEGREES[pd]>=DEGREES[jd] else 0.0)
    values={'skills':skill_score,'semantic':similarity(profile['semantic_text'],job['semantic_text'],encoder),'experience':experience,'education':education,'projects':similarity('\n'.join(profile['projects']),job['semantic_text'],encoder)}
    active={k:v for k,v in values.items() if v is not None};n=len(active)
    overall=round(100*sum(active.values())/n,1) if n else None
    # Similar related evidence never counts as an explicitly demonstrated skill.
    partial=[]
    for skill in missing:
        cousins=[s for s in owned if BY_NAME[s]['category']==BY_NAME[skill]['category']]
        if cousins:
            partial.append({'skill':skill,'related_skills':sorted(cousins),'reason':'Same taxonomy category; prerequisite proximity only, no proficiency inferred.'})
    evidence=[e for e in profile['skill_evidence'] if e['skill'] in matched]
    strong=[k for k,v in active.items() if v>=.75];weak=[k for k,v in active.items() if v<.5]
    explanation=('Detected overlap: '+', '.join(matched)+'. ' if matched else 'No explicit target skills detected. ')+('Required skills not detected: '+', '.join(sorted(required-owned))+'. ' if required-owned else 'All extracted required skills were detected. ')+f'{n} of 5 score factors were available; unknown factors are excluded and weights renormalized.'
    factors={k:{'score':round(v*100,1) if v is not None else None,'weight':round(1/n,4) if v is not None and n else 0,'contribution':round(v*100/n,2) if v is not None and n else None} for k,v in values.items()}
    return {'overall':overall,'factors':factors,'coverage':round(100*n/5),'matched_skills':matched,'missing_skills':missing,'missing_required':sorted(required-owned),'missing_preferred':sorted(preferred-owned),'partial_matches':partial,'evidence':evidence,'strong_areas':strong,'weak_areas':weak,'explanation':explanation,'model':encoder.name,'score_version':VERSION,'notice':'Compatibility index, not hiring probability. Equal factor weights are an uncalibrated neutral baseline. Low coverage makes comparisons uncertain.'}
