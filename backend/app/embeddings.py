"""Replaceable semantic encoders. Offline LSA is explicit, never a silent fallback."""
import json,re,threading
from typing import Protocol
import numpy as np
from .config import DATA,EMBEDDING_BACKEND,MODEL_NAME,MODEL_REVISION
class Encoder(Protocol):
    name:str
    def encode(self,texts:list[str])->np.ndarray: ...

def chunks(text,words=100):
    tokens=text.split()
    return [' '.join(tokens[i:i+words]) for i in range(0,len(tokens),80)] or ['']

class MiniLM:
    name='minilm'
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model=SentenceTransformer(MODEL_NAME,revision=MODEL_REVISION,trust_remote_code=False,device='cpu')
        self.lock=threading.Lock()
    def encode(self,texts):
        # Mean pooled overlapping short chunks avoid silent whole-resume truncation.
        all_chunks=[chunks(t) for t in texts];flat=[c for group in all_chunks for c in group]
        with self.lock: values=self.model.encode(flat,normalize_embeddings=True,show_progress_bar=False,batch_size=32)
        result=[];offset=0
        for group in all_chunks:
            v=values[offset:offset+len(group)].mean(axis=0);offset+=len(group)
            result.append(v/max(np.linalg.norm(v),1e-12))
        return np.array(result)

class OfflineLSA:
    name='lsa-demo'
    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        jobs=json.loads((DATA/'jobs.sample.json').read_text())
        corpus=[j['text'] for j in jobs]
        self.vectorizer=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,stop_words='english')
        matrix=self.vectorizer.fit_transform(corpus)
        self.svd=TruncatedSVD(n_components=min(12,matrix.shape[0]-1),random_state=42).fit(matrix)
    def encode(self,texts):
        v=self.svd.transform(self.vectorizer.transform(texts))
        return v/np.maximum(np.linalg.norm(v,axis=1,keepdims=True),1e-12)

_encoder=None
_init_lock=threading.Lock()
def get_encoder():
    global _encoder
    with _init_lock:
        if _encoder is None:
            if EMBEDDING_BACKEND=='lsa-demo': _encoder=OfflineLSA()
            elif EMBEDDING_BACKEND=='minilm': _encoder=MiniLM()
            else: raise ValueError('EMBEDDING_BACKEND must be minilm or lsa-demo')
        return _encoder

def similarity(a,b,encoder=None):
    if not a.strip() or not b.strip(): return None
    vectors=(encoder or get_encoder()).encode([a,b])
    if np.linalg.norm(vectors[0])<1e-10 or np.linalg.norm(vectors[1])<1e-10: return None
    return float(np.clip(vectors[0]@vectors[1],0,1))

class RequestEncoder:
    """Cache vectors only for one ranking request; no cross-user text retention."""
    def __init__(self,base):
        self.base=base;self.name=base.name;self.cache={}
    def encode(self,texts):
        missing=list(dict.fromkeys(t for t in texts if t not in self.cache))
        if missing:
            for t,v in zip(missing,self.base.encode(missing)): self.cache[t]=v
        return np.array([self.cache[t] for t in texts])
