import json
import numpy as np
from app.embeddings import OfflineLSA,similarity,chunks
from app.extraction import resume,job
from app.scoring import match
from app.analytics import learning,analytics
from app.config import DATA

def test_normalized_encoder():
    e=OfflineLSA();v=e.encode(['Python machine learning','SQL data analysis']);assert np.allclose(np.linalg.norm(v,axis=1),1)

def test_semantic_own_text():assert similarity('Build machine learning models','Build machine learning models',OfflineLSA())>.99

def test_empty_similarity_unknown():assert similarity('','anything',OfflineLSA()) is None

def test_out_of_vocabulary_unknown():assert similarity('xyzzzz qqqqq','Python',OfflineLSA()) is None

def test_chunks_cover_tail():assert 'TAIL' in chunks('word '*1000+'TAIL')[-1]

def test_explanations_grounded():
    p=resume('Skills\nPython, SQL\nProjects\nBuilt predictive models using Python.');j=job('Required: Python, SQL, Docker\nResponsibilities: Build predictive models.')
    result=match(p,j,OfflineLSA());assert result['missing_required']==['Docker'];assert set(result['matched_skills'])=={'Python','SQL','Machine Learning'};assert result['factors']['experience']['score'] is None
    assert abs(sum(v['weight'] for v in result['factors'].values())-1)<.001
    assert abs(sum(v['contribution'] or 0 for v in result['factors'].values())-result['overall'])<.1

def test_missing_not_perfect():
    result=match(resume('nothing recognizable'),job('Required Python experience'),OfflineLSA())
    assert result['factors']['skills']['score']==0;assert result['factors']['education']['score'] is None

def test_related_not_credited():
    result=match(resume('Skills\nAWS'),job('Required: Azure'),OfflineLSA());assert result['factors']['skills']['score']==0;assert result['partial_matches'][0]['skill']=='Azure'

def test_ranking():
    p=resume((DATA/'resume.sample.txt').read_text());good=job('Required: Python, SQL, Pandas, scikit-learn\nResponsibilities: Build predictive models.');bad=job('Required: Java, Docker, Redis\nResponsibilities: Maintain backend payment services.')
    e=OfflineLSA();assert match(p,good,e)['overall']>match(p,bad,e)['overall']

def test_counterfactual_name_invariance():
    a=resume('Jane Smith\nSkills\nPython, SQL\nProjects\nBuilt predictive models.');b=resume('John Jones\nSkills\nPython, SQL\nProjects\nBuilt predictive models.');j=job('Required: Python, SQL');e=OfflineLSA()
    assert match(a,j,e)['overall']==match(b,j,e)['overall']

def test_learning_uses_denominator():
    js=[{'structured':job('Required: Python, AWS')},{'structured':job('Required: Python\nPreferred: Docker')}]
    lessons=learning(resume('Skills\nPython'),js);aws=next(s for s in lessons if s['skill']=='AWS');assert aws['required_percent']==50;assert aws['coverage_gain']==25
    docker=next(s for s in lessons if s['skill']=='Docker');assert docker['coverage_gain']==0;assert docker['priority']=='Low'

def test_no_jobs():assert learning(resume('Skills\nPython'),[])==[];assert analytics([])['count']==0

def test_cooccurrence():
    js=[{'title':'Test','location':'Remote','structured':job('Required: Python, SQL'),'is_sample':True}];a=analytics(js);assert a['cooccurrence']['matrix']==[[1,1],[1,1]];assert a['skills'][0]['percent']==100
