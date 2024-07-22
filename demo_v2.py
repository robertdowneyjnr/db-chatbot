import os
import logging
from dotenv import load_dotenv
from functools import lru_cache
from sqlparse import parse
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from langchain_community.llms.google_palm import GooglePalm
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.prompts import SemanticSimilarityExampleSelector
from langchain.vectorstores import Qdrant
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.callbacks.manager import AsyncCallbackManager
from langchain.callbacks.streaming_stdout import AsyncStreamingStdOutCallbackHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
api_key = os.getenv('GOOGLE_API_KEY')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')

# Initialize LLM
llm = GooglePalm(google_api_key=api_key, temperature=0.2)

# Connect to database
try:
    db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}",
                              sample_rows_in_table_info=3)
except Exception as e:
    logger.error(f"Database connection failed: {e}")
    raise

# Initialize embedding model
model = SentenceTransformer('all-mpnet-base-v2')


@lru_cache(maxsize=1000)
def cached_embed(text):
    return model.encode(text)


# Initialize vector store
client = QdrantClient("localhost", port=6333)
vector_store = Qdrant(client=client, collection_name="t_shirt_qa", embedding_function=cached_embed)


# Generate dynamic few-shot examples
def generate_examples(db):
    tables = db.get_tables()
    examples = []
    for table in tables:
        columns = db.get_columns(table)
        examples.append({
            'Question': f"What is the total number of {table}?",
            'SQLQuery': f"SELECT COUNT(*) FROM `{table}`",
            'SQLResult': "Result of the SQL query",
            'Answer': f"The total number of {table} is [result]."
        })
    return examples


few_shots = generate_examples(db)

# Create example selector
example_selector = SemanticSimilarityExampleSelector(
    vectorstore=vector_store,
    k=2,
)

# Create prompt template
system_template = """You are an AI assistant expert in SQL and MySQL databases. Your task is to translate natural language questions into SQL queries, execute them, and provide clear answers based on the results."""
human_template = """Given the following question about a MySQL database, generate a SQL query to answer it, then interpret the results:
Question: {question}
Database schema: {schema}
"""

chat_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template(human_template)
])


# Query validation function
def validate_query(query):
    parsed = parse(query)[0]
    if parsed.get_type() != 'SELECT':
        raise ValueError("Only SELECT queries are allowed")
    # Add more checks as needed


# Feedback recording function
def record_feedback(question, generated_query, actual_query, feedback):
    # Store this information in a database or file for later analysis
    logger.info(f"Feedback recorded for question: {question}")
    pass


# Set up async callback manager
async_callback_manager = AsyncCallbackManager([AsyncStreamingStdOutCallbackHandler()])

# Create SQLDatabaseChain
async_chain = SQLDatabaseChain.from_llm(
    llm,
    db,
    verbose=True,
    prompt=chat_prompt,
    callback_manager=async_callback_manager
)


# Example usage
async def main():
    question = "How many white Nike t-shirts do we have in stock?"
    try:
        result = await async_chain.arun(question)
        logger.info(f"Question: {question}")
        logger.info(f"Answer: {result}")

        # Here you would typically get user feedback and the correct query if the generated one was wrong
        user_feedback = "Correct"  # This would come from user input
        correct_query = None  # This would be provided by the user if the generated query was incorrect

        record_feedback(question, async_chain.last_query, correct_query, user_feedback)
    except Exception as e:
        logger.error(f"Error processing question: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())