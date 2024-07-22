# retriever.py
from langchain_core.retrievers import BaseRetriever
from langchain.schema import Document
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from config import load_config
from typing import List, Any
import os
from langchain import OpenAI
from database import connect_to_database
from pydantic import Field


class CustomSQLDatabaseRetriever(BaseRetriever):
    database: Any = Field(default=None)
    llm: Any = Field(default=None)
    prompt: PromptTemplate = Field(default=None)
    chain: LLMChain = Field(default=None)

    def __init__(self, database: Any, llm: Any):
        super().__init__()
        self.database = database
        self.llm = llm

        # Create a prompt template
        template = """
        Given the following database schema:
        {schema}

        Determine if the following question is relevant to this database:
        {question}

        Answer with 'Yes' if it's relevant, or 'No' if it's not relevant.
        Explanation:
        """

        self.prompt = PromptTemplate(
            input_variables=["schema", "question"],
            template=template,
        )

        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def get_relevant_documents(self, query: str) -> List[Document]:
        # Get detailed schema information
        detailed_schema = self._get_detailed_schema()

        result = self.chain.run(schema=detailed_schema, question=query)

        if "Yes" in result:
            return [Document(page_content=query, metadata={"relevant": True, "schema": detailed_schema})]
        else:
            return []

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        return self.get_relevant_documents(query)

    def _get_detailed_schema(self) -> str:
        """Helper method to get detailed schema information."""
        '''schema_info = []
        for table in self.database.get_table_names():
            columns = self.database.get_columns(table)
            schema_info.append(f"Table: {table}\nColumns: {', '.join(columns)}")'''
        return self.database.get_table_info()


def create_retriever(db):
    config = load_config()
    os.environ['OPENAI_API_KEY'] = config['api_key']
    llm = OpenAI(temperature=0.1, max_tokens=500)
    return CustomSQLDatabaseRetriever(database=db, llm=llm)