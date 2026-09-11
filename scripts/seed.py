"""Idempotent sample ingestion; replace input JSON to ingest another compatible catalog."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.models import Base,engine,SessionLocal,Job,JobSkill,Skill
from app.extraction import job,TAXONOMY
from app.config import DATA

def main():
    Base.metadata.create_all(engine)
    source=Path(sys.argv[1]) if len(sys.argv)>1 else DATA/'jobs.sample.json'
    records=json.loads(source.read_text())
    if not isinstance(records,list):raise ValueError('Expected a list of postings')
    with SessionLocal() as db:
        for s in TAXONOMY:
            if not db.get(Skill,s['name']):db.add(Skill(name=s['name'],category=s['category'],aliases=s['aliases']))
        db.flush()
        for r in records:
            if not r.get('is_sample') or r.get('source')!='authored_demo':raise ValueError('Shared seed must be explicitly authored_demo. Import private real jobs through the authenticated API.')
            if db.get(Job,r['id']):continue
            structured=job(r['text']);j=Job(**{k:v for k,v in r.items() if k!='text'},structured=structured);db.add(j);db.flush()
            for s in structured['required_skills']+structured['preferred_skills']:db.add(JobSkill(job_id=j.id,skill_name=s,required=s in structured['required_skills']))
        db.commit()
    print(f'Loaded {len(records)} authored sample postings (idempotent).')
if __name__=='__main__':main()
