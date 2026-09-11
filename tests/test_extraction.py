import pytest
from app.extraction import skill_evidence,resume,job,experience_duration
@pytest.mark.parametrize('variant',['ML','machine-learning','machine learning','predictive models'])
def test_ml_alias(variant):assert 'Machine Learning' in [s['skill'] for s in skill_evidence(variant)]
@pytest.mark.parametrize('variant',['sklearn','scikit learn','scikit-learn'])
def test_sklearn_alias(variant):assert skill_evidence(variant)[0]['skill']=='scikit-learn'
def test_word_boundaries():assert not skill_evidence('JavaScripture and SQLish were unrelated.')
def test_negation():assert 'AWS' not in [s['skill'] for s in skill_evidence('No experience with AWS.\nSkills: Python')]
def test_learning_is_not_proficiency():assert not skill_evidence('Currently learning Docker')
def test_overlap_not_double_counted():
    years,_=experience_duration(['Engineer Jan 2020 - Dec 2022','Consultant Jan 2021 - Dec 2023']);assert years==4

def test_dates_not_guessed():assert experience_duration(['2019 - 2022 Company'])[0] is None

def test_required_preferred():
    j=job('Required: Python, SQL\nPreferred: AWS, Docker')
    assert set(j['required_skills'])=={'Python','SQL'};assert set(j['preferred_skills'])=={'AWS','Docker'}
def test_inline_preferred():
    j=job('Required: Python. Preferred: AWS.');assert j['required_skills']==['Python'];assert j['preferred_skills']==['AWS']
def test_ambiguous_description():
    j=job('We seek a curious colleague to help our organization improve.');assert j['required_skills']==[];assert j['years_experience'] is None

def test_required_wins():
    j=job('Required: Python\nPreferred: Python, Docker');assert j['required_skills']==['Python'];assert j['preferred_skills']==['Docker']
def test_name_and_university_not_semantic():
    p=resume('Jane Sample\nEducation\nBachelor degree\nElite University\nProjects\nBuilt machine learning models using Python')
    assert 'Jane' not in p['semantic_text'];assert 'University' not in p['semantic_text'];assert p['name']=='Jane Sample'
def test_unknown_fields():
    p=resume('Skills\nPython, SQL');assert p['degree'] is None;assert p['years_experience'] is None

def test_optional_degree_not_penalized():assert job('Bachelor degree or equivalent experience. Python required.')['degree_required'] is None
