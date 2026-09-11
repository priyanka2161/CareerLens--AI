from sentence_transformers import SentenceTransformer
import os
model=SentenceTransformer(os.getenv('MODEL_NAME','sentence-transformers/all-MiniLM-L6-v2'),revision=os.getenv('MODEL_REVISION','c9745ed1d9f207416be6d2e6f8de32d1f16199bf'),trust_remote_code=False,device='cpu')
print('Model ready:',model.get_sentence_embedding_dimension())
