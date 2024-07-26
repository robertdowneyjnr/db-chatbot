# embeddings.py
from functools import lru_cache
from langchain_community.embeddings import HuggingFaceEmbeddings


def embeddings():
    model = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    return model
'''
@lru_cache(maxsize=1000)
def cached_embed(text):
    return model.encode(text)
'''



