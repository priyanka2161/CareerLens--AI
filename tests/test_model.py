import os
import pytest
from app.embeddings import MiniLM,similarity
@pytest.mark.model
@pytest.mark.skipif(os.getenv('RUN_MODEL_TESTS')!='1',reason='Set RUN_MODEL_TESTS=1 after downloading the pinned model')
def test_transformer_paraphrase():
    e=MiniLM()
    anchor='Developed predictive models using scikit-learn.'
    related=similarity(anchor,'Experience building machine learning models.',e)
    unrelated=similarity(anchor,'Preparing restaurant menus and coordinating dining room service.',e)
    assert related is not None and unrelated is not None and related>unrelated
