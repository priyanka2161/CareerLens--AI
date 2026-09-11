"""Isolated full API smoke run with the real pinned transformer and fictional data."""
import json,os,sys,tempfile,time
from pathlib import Path
scratch=tempfile.TemporaryDirectory(prefix='careerlens-smoke-')
os.environ['DATABASE_URL']='sqlite:///'+str(Path(scratch.name)/'smoke.db')
os.environ['EMBEDDING_BACKEND']='minilm'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.main import app
from app.models import Job,SessionLocal
from app.extraction import job
from app.config import DATA
from fastapi.testclient import TestClient
start=time.perf_counter()
with TestClient(app) as client:
    with SessionLocal() as db:
        for row in json.loads((DATA/'jobs.sample.json').read_text()):db.add(Job(**{k:v for k,v in row.items() if k!='text'},structured=job(row['text'])))
        db.commit()
    auth={'Authorization':'Bearer '+client.post('/session').json()['token']}
    resume=client.post('/demo/profile',headers=auth);assert resume.status_code==201
    result=client.get('/recommendations',headers=auth,params={'resume_id':resume.json()['id']})
    assert result.status_code==200,result.text
    data=result.json();assert len(data['jobs'])==18
    report={'backend':'minilm','database':'isolated SQLite smoke, not PostgreSQL runtime','postings_ranked':len(data['jobs']),'learning_skills':len(data['learning']),'top_jobs':[{'title':x['job']['title'],'score':x['match']['overall'],'coverage':x['match']['coverage']} for x in data['jobs'][:5]],'elapsed_seconds':round(time.perf_counter()-start,2),'data':'fictional samples; no accuracy claim'}
    print(json.dumps(report,indent=2))
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(report,indent=2)+'\n')
