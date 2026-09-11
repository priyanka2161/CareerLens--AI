import os,tempfile
from pathlib import Path
TEST_DIR=tempfile.TemporaryDirectory(prefix='careerlens-tests-')
os.environ['DATABASE_URL']='sqlite:///'+str(Path(TEST_DIR.name)/'test.db')
os.environ['EMBEDDING_BACKEND']='lsa-demo'
import pytest
from fastapi.testclient import TestClient
from app.main import app,limits
from app import models as m
from app.extraction import TAXONOMY,job
from app.config import DATA
import json
@pytest.fixture
def client():
    m.Base.metadata.drop_all(m.engine);limits.clear()
    with TestClient(app) as c:
        with m.SessionLocal() as db:
            for r in json.loads((DATA/'jobs.sample.json').read_text()):
                db.add(m.Job(**{k:v for k,v in r.items() if k!='text'},structured=job(r['text'])))
            db.commit()
        yield c
@pytest.fixture
def auth(client):
    return {'Authorization':'Bearer '+client.post('/session').json()['token']}
