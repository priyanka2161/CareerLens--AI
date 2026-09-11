from datetime import datetime,timezone
import uuid
from sqlalchemy import create_engine,Column,String,Float,Boolean,ForeignKey,JSON,DateTime,Index,UniqueConstraint,event
from sqlalchemy.orm import declarative_base,sessionmaker
from .config import DATABASE_URL
engine=create_engine(DATABASE_URL,connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite') else {},pool_pre_ping=True)
if DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine,'connect')
    def foreign_keys(connection,record): connection.execute('PRAGMA foreign_keys=ON')
SessionLocal=sessionmaker(bind=engine,expire_on_commit=False)
Base=declarative_base()
def uid(): return str(uuid.uuid4())
class User(Base):
    __tablename__='users'
    id=Column(String,primary_key=True,default=uid)
    token_hash=Column(String,unique=True,nullable=False,index=True)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Resume(Base):
    __tablename__='resumes'
    id=Column(String,primary_key=True,default=uid)
    user_id=Column(String,ForeignKey('users.id',ondelete='CASCADE'),nullable=False,index=True)
    structured=Column(JSON,nullable=False)
    filename=Column(String,nullable=False)
    created_at=Column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
class Job(Base):
    __tablename__='jobs'
    id=Column(String,primary_key=True,default=uid)
    user_id=Column(String,ForeignKey('users.id',ondelete='CASCADE'),nullable=True,index=True)
    title=Column(String,nullable=False,index=True)
    company=Column(String,default='User posting')
    location=Column(String,default='Unspecified',index=True)
    structured=Column(JSON,nullable=False)
    salary_min=Column(Float,nullable=True)
    salary_max=Column(Float,nullable=True)
    currency=Column(String,nullable=True)
    salary_period=Column(String,nullable=True)
    source=Column(String,default='user_import')
    is_sample=Column(Boolean,default=False,nullable=False)
class Skill(Base):
    __tablename__='skills'
    name=Column(String,primary_key=True)
    category=Column(String,nullable=False)
    aliases=Column(JSON,nullable=False)
class ResumeSkill(Base):
    __tablename__='resume_skills'
    resume_id=Column(String,ForeignKey('resumes.id',ondelete='CASCADE'),primary_key=True)
    skill_name=Column(String,ForeignKey('skills.name'),primary_key=True)
    evidence=Column(String,nullable=False)
class JobSkill(Base):
    __tablename__='job_skills'
    job_id=Column(String,ForeignKey('jobs.id',ondelete='CASCADE'),primary_key=True)
    skill_name=Column(String,ForeignKey('skills.name'),primary_key=True)
    required=Column(Boolean,nullable=False)
class MatchResult(Base):
    __tablename__='match_results'
    id=Column(String,primary_key=True,default=uid)
    resume_id=Column(String,ForeignKey('resumes.id',ondelete='CASCADE'),nullable=False,index=True)
    job_id=Column(String,ForeignKey('jobs.id',ondelete='CASCADE'),nullable=False,index=True)
    result=Column(JSON,nullable=False)
    __table_args__=(UniqueConstraint('resume_id','job_id'),)
class Recommendation(Base):
    __tablename__='recommendations'
    id=Column(String,primary_key=True,default=uid)
    resume_id=Column(String,ForeignKey('resumes.id',ondelete='CASCADE'),nullable=False,index=True)
    role_filter=Column(String,nullable=False,default='')
    data=Column(JSON,nullable=False)
    __table_args__=(UniqueConstraint('resume_id','role_filter'),)
Index('ix_resume_skill_name', ResumeSkill.skill_name)
Index('ix_job_skill_name', JobSkill.skill_name)
