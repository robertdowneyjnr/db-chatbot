# vector_store.py
from embedding import embeddings
from few_shots import few_shots
from langchain_community.vectorstores import Chroma


def create_vector_store():
    # client = QdrantClient("localhost", port=6333)
    # return Qdrant(client=client, collection_name="t_shirt_qa", embedding_function=cached_embed)
    to_vectorize = [" ".join(example.values()) for example in few_shots()]
    vectorstore = Chroma.from_texts(to_vectorize, embeddings(), metadatas=few_shots())
    return vectorstore
