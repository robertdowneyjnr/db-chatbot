# retriever.py
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.retrievers import BaseRetriever
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from sqlalchemy import inspect
from typing import List, Any
from pydantic import Field


class SemanticSQLDatabaseRetriever(BaseRetriever):
    database: Any = Field(default=None)
    embeddings: OpenAIEmbeddings = Field(default=None)
    schema_store: Any = Field(default=None)

    def __init__(self, database: Any, embeddings: OpenAIEmbeddings):
        super().__init__()
        self.database = database
        self.embeddings = embeddings
        self.schema_store = self._create_schema_store()

    def _create_schema_store(self):
        schema_info = self._get_detailed_schema()
        return FAISS.from_texts(schema_info, self.embeddings)

    def get_relevant_documents(self, query: str) -> List[Document]:
        query_embedding = self.embeddings.embed_query(query)
        relevant_elements = self.schema_store.similarity_search_by_vector(query_embedding, k=3)
        return [Document(page_content=query,
                         metadata={"relevant_schema": [elem.page_content for elem in relevant_elements]})]

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        return self.get_relevant_documents(query)

    def _get_detailed_schema(self) -> List[str]:
        inspector = inspect(self.database._engine)
        schema_info = []
        for table_name in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            schema_info.append(f"Table: {table_name}, Columns: {', '.join(columns)}")
        return schema_info


def create_retriever(db):
    embeddings = OpenAIEmbeddings()
    return SemanticSQLDatabaseRetriever(database=db, embeddings=embeddings)