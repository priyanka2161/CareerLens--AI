"""Evaluate human labels when available. Provisional fixtures are smoke checks only."""
import argparse,json,sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from sklearn.metrics import precision_score,recall_score,ndcg_score
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.extraction import resume,job
from app.scoring import match
from app.config import DATA
p=argparse.ArgumentParser();p.add_argument('--data',default=str(DATA/'evaluation.json'));p.add_argument('--allow-provisional',action='store_true');p.add_argument('--threshold',type=float,default=60);p.add_argument('--output');args=p.parse_args()
rows=json.loads(Path(args.data).read_text());results=[];groups=defaultdict(list)
for r in rows:
    label=r.get('human_relevance')
    if label is None and args.allow_provisional:label=r.get('provisional_rubric_label')
    if label is None:continue
    if label not in [0,1,2,3]:raise ValueError('Relevance must be an integer from 0 to 3')
    m=match(resume(r['resume_text']),job(r['job_text']))
    item={'profile_id':r['profile_id'],'job_id':r['job_id'],'label':label,'score':m['overall'],'semantic':m['factors']['semantic']['score']};results.append(item);groups[r['profile_id']].append(item)
if not results:
    print('No human labels available. Populate human_relevance with independent 0–3 annotations. No accuracy claim can be made.');sys.exit(0)
y=[r['label']>=2 for r in results];pred=[(r['score'] or 0)>=args.threshold for r in results]
ndcgs=[ndcg_score([[x['label'] for x in g]],[[x['score'] or 0 for x in g]],k=min(3,len(g))) for g in groups.values() if len(g)>1 and any(x['label'] for x in g)]
sem=[r['semantic']/100 for r in results if r['semantic'] is not None]
report={'purpose':'Provisional smoke fixtures; NOT scientific evaluation' if args.allow_provisional else 'Human-labeled evaluation; inspect sample size and annotation process','count':len(results),'threshold':args.threshold,'precision':precision_score(y,pred,zero_division=0),'recall':recall_score(y,pred,zero_division=0),'ndcg_at_3':float(np.mean(ndcgs)) if ndcgs else None,'clipped_cosine_quantiles':dict(zip(['min','p25','median','p75','max'],np.quantile(sem,[0,.25,.5,.75,1]).tolist())) if sem else {},'false_positives':[r for r,a,b in zip(results,y,pred) if not a and b],'false_negatives':[r for r,a,b in zip(results,y,pred) if a and not b],'pairs':results,'limitations':['Tiny authored corpus, correlated templates, no held-out population estimate.','LSA is trained on the sample catalog: optimistic in-catalog behavior is expected.','Threshold is illustrative. Tune on validation data, never on the test set.']}
text=json.dumps(report,indent=2);print(text)
if args.output:Path(args.output).write_text(text+'\n')
