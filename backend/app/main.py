import hashlib,json,os,secrets,threading,time
from collections import defaultdict,deque
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI,Depends,HTTPException,UploadFile,File,Request,Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from pydantic import BaseModel,Field,field_validator
from sqlalchemy import select,or_,delete
from sqlalchemy.orm import Session
from . import models as m
from .config import DATA,MAX_BYTES,MAX_TEXT,EMBEDDING_BACKEND
from .extraction import resume,job,TAXONOMY
from .parsing import parse_file
from .scoring import match
from .embeddings import get_encoder,RequestEncoder
from .analytics import analytics,learning

@asynccontextmanager
async def lifespan(app):
    # Production deployment runs explicit schema bootstrap before serving.
    if os.getenv('AUTO_CREATE_SCHEMA','true').lower()=='true': m.Base.metadata.create_all(m.engine)
    with m.SessionLocal() as db:
        for s in TAXONOMY:
            if not db.get(m.Skill,s['name']): db.add(m.Skill(name=s['name'],category=s['category'],aliases=s['aliases']))
        db.commit()
    yield
class BodyLimit:
    """Bound buffering before multipart parsing, including requests without Content-Length."""
    def __init__(self,app): self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope['method'] not in ('POST','PUT','PATCH'):
            return await self.app(scope,receive,send)
        body=bytearray()
        while True:
            message=await receive()
            if message['type']=='http.disconnect': return
            body.extend(message.get('body',b''))
            if len(body)>MAX_BYTES+65536:
                from starlette.responses import JSONResponse
                return await JSONResponse({'detail':'Request exceeds upload limit.'},413)(scope,receive,send)
            if not message.get('more_body',False): break
        sent=False
        async def replay():
            nonlocal sent
            if not sent:
                sent=True
                return {'type':'http.request','body':bytes(body),'more_body':False}
            return await receive()
        await self.app(scope,replay,send)

app=FastAPI(title='CareerLens AI',version='1.0.0',lifespan=lifespan,root_path=os.getenv('API_ROOT_PATH',''))
origins=os.getenv('CORS_ORIGINS','http://localhost:5173,http://localhost:3000').split(',')
app.add_middleware(BodyLimit)
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=False,allow_methods=['GET','POST','DELETE'],allow_headers=['Authorization','Content-Type'])
limits=defaultdict(deque);limit_lock=threading.Lock()
@app.middleware('http')
async def guard(request:Request,call_next):
    from starlette.responses import JSONResponse
    length=request.headers.get('content-length')
    if length and (not length.isdigit() or int(length)>MAX_BYTES+65536): return JSONResponse({'detail':'Request exceeds upload limit.'},status_code=413)
    key=request.client.host if request.client else 'local';now=time.monotonic()
    with limit_lock:
        # Bound memory used by anonymous rate-limit entries.
        if len(limits)>10000: limits.clear()
        q=limits[key]
        while q and q[0]<now-60: q.popleft()
        blocked=len(q)>=120
        if not blocked:q.append(now)
    if blocked:return JSONResponse({'detail':'Too many requests. Retry in a minute.'},status_code=429)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff';response.headers['Cache-Control']='no-store'
    return response

def database():
    with m.SessionLocal() as db: yield db
DB=Annotated[Session,Depends(database)];bearer=HTTPBearer(auto_error=False)
def user(db:DB,credentials:Annotated[HTTPAuthorizationCredentials|None,Depends(bearer)]):
    if not credentials: raise HTTPException(401,'Create a session first.')
    token_hash=hashlib.sha256(credentials.credentials.encode()).hexdigest()
    u=db.scalar(select(m.User).where(m.User.token_hash==token_hash))
    if not u: raise HTTPException(401,'Invalid session.')
    return u
USER=Annotated[m.User,Depends(user)]
class TextInput(BaseModel):
    text:str=Field(min_length=30,max_length=MAX_TEXT)
    title:str|None=Field(default=None,max_length=150)
    location:str=Field(default='Unspecified',max_length=120)
    @field_validator('text')
    @classmethod
    def nonempty(cls,v):
        if len(v.strip())<30:raise ValueError('Provide at least 30 non-whitespace characters.')
        return v
class MatchInput(BaseModel):
    resume_id:str=Field(max_length=50)
    job_id:str=Field(max_length=50)

def own_resume(db,u,rid):
    r=db.get(m.Resume,rid)
    if not r or r.user_id!=u.id:raise HTTPException(404,'Resume not found in this session.')
    return r

def visible_jobs(db,u,role=''):
    stmt=select(m.Job).where(or_(m.Job.user_id==u.id,m.Job.is_sample.is_(True)))
    if role:stmt=stmt.where(m.Job.title.ilike('%'+role.replace('%','').replace('_','')+'%'))
    return db.scalars(stmt.order_by(m.Job.id)).all()

def as_job(j):return {c.name:getattr(j,c.name) for c in m.Job.__table__.columns if c.name!='user_id'}

def save_resume(text,filename,db,u):
    if len(db.scalars(select(m.Resume.id).where(m.Resume.user_id==u.id)).all())>=20:raise HTTPException(409,'Session limit: delete old resumes before uploading more.')
    data=resume(text)
    r=m.Resume(user_id=u.id,structured=data,filename=filename);db.add(r);db.flush()
    for e in data['skill_evidence']:db.add(m.ResumeSkill(resume_id=r.id,skill_name=e['skill'],evidence=e['evidence']))
    db.commit();return {'id':r.id,'filename':filename,'structured':data}

def save_job(text,db,u,title=None,location='Unspecified'):
    if len(db.scalars(select(m.Job.id).where(m.Job.user_id==u.id)).all())>=100:raise HTTPException(409,'Session limit: maximum 100 imported postings.')
    data=job(text);j=m.Job(user_id=u.id,title=title or data['title'],location=location,structured=data)
    db.add(j);db.flush()
    for s in data['required_skills']+data['preferred_skills']:db.add(m.JobSkill(job_id=j.id,skill_name=s,required=s in data['required_skills']))
    db.commit();return as_job(j)

def calculate(r,j,db,encoder=None):
    try:result=match(r.structured,j.structured,encoder)
    except Exception as exc:
        raise HTTPException(503,'Embedding model unavailable. Run scripts/download_model.py or explicitly select EMBEDDING_BACKEND=lsa-demo for the limited offline baseline.') from exc
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    insert=pg_insert if db.bind.dialect.name=='postgresql' else sqlite_insert
    stmt=insert(m.MatchResult).values(resume_id=r.id,job_id=j.id,result=result)
    db.execute(stmt.on_conflict_do_update(index_elements=['resume_id','job_id'],set_={'result':result}))
    return result

@app.get('/health')
def health(db:DB):
    from sqlalchemy import text
    db.execute(text('SELECT 1'))
    return {'status':'ok','embedding_backend':EMBEDDING_BACKEND,'model_ready':'checked on first match','data':'sample/user-imported only'}
@app.post('/session',status_code=201)
def create_session(db:DB):
    token=secrets.token_urlsafe(32);u=m.User(token_hash=hashlib.sha256(token.encode()).hexdigest());db.add(u);db.commit()
    return {'token':token,'notice':'Anonymous device session; save the token only on your trusted device. No account recovery.'}
@app.delete('/session',status_code=204)
def delete_session(db:DB,u:USER):
    db.delete(u);db.commit()
@app.get('/skills')
def skills():return TAXONOMY
@app.post('/resume/text',status_code=201)
def resume_text(body:TextInput,db:DB,u:USER):return save_resume(body.text,'Pasted resume',db,u)
@app.post('/resume/upload',status_code=201)
def resume_upload(db:DB,u:USER,file:UploadFile=File(...)):
    try: return save_resume(parse_file(file.file.read(MAX_BYTES+1),file.filename or ''),(file.filename or 'Resume')[:200],db,u)
    except ValueError as exc:raise HTTPException(422,str(exc))
@app.get('/resumes')
def resumes(db:DB,u:USER):return [{'id':r.id,'filename':r.filename,'structured':r.structured} for r in db.scalars(select(m.Resume).where(m.Resume.user_id==u.id).order_by(m.Resume.created_at.desc()))]
@app.delete('/resume/{rid}',status_code=204)
def remove_resume(rid:str,db:DB,u:USER):db.delete(own_resume(db,u,rid));db.commit()
@app.post('/job/analyze',status_code=201)
def analyze_job(body:TextInput,db:DB,u:USER):return save_job(body.text,db,u,body.title,body.location)
@app.post('/job/upload',status_code=201)
def job_upload(db:DB,u:USER,file:UploadFile=File(...)):
    try:return save_job(parse_file(file.file.read(MAX_BYTES+1),file.filename or '',True),db,u)
    except ValueError as exc:raise HTTPException(422,str(exc))
@app.post('/match')
def run_match(body:MatchInput,db:DB,u:USER):
    r=own_resume(db,u,body.resume_id);j=db.get(m.Job,body.job_id)
    if not j or (not j.is_sample and j.user_id!=u.id):raise HTTPException(404,'Job not found.')
    result=calculate(r,j,db);db.commit();return result
@app.get('/jobs')
def jobs(db:DB,u:USER,role:Annotated[str,Query(max_length=100)]=''):return [as_job(j) for j in visible_jobs(db,u,role)]
@app.get('/recommendations')
def recommendations(resume_id:str,db:DB,u:USER,role:Annotated[str,Query(max_length=100)]=''):
    r=own_resume(db,u,resume_id);js=visible_jobs(db,u,role);ranked=[]
    try: encoder=RequestEncoder(get_encoder()) if js else None
    except Exception as exc: raise HTTPException(503,'Embedding model unavailable. Download the model or explicitly select lsa-demo.') from exc
    for j in js:ranked.append({'job':as_job(j),'match':calculate(r,j,db,encoder)})
    ranked.sort(key=lambda x:-(x['match']['overall'] if x['match']['overall'] is not None else -1))
    lessons=learning(r.structured,[as_job(j) for j in js])
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    insert=pg_insert if db.bind.dialect.name=='postgresql' else sqlite_insert
    stmt=insert(m.Recommendation).values(resume_id=r.id,role_filter=role,data=lessons)
    db.execute(stmt.on_conflict_do_update(index_elements=['resume_id','role_filter'],set_={'data':lessons}))
    db.commit();return {'jobs':ranked,'learning':lessons,'count':len(js),'source':'Sample + user-imported postings, not live listings.'}
@app.get('/market/analytics')
def market(db:DB,u:USER,role:Annotated[str,Query(max_length=100)]=''):return analytics([as_job(j) for j in visible_jobs(db,u,role)])
@app.post('/demo/profile',status_code=201)
def demo_profile(db:DB,u:USER):return save_resume((DATA/'resume.sample.txt').read_text(),'Fictional sample resume',db,u)
