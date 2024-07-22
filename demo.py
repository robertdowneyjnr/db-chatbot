from langchain_community.llms.google_palm import GooglePalm
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.prompts import SemanticSimilarityExampleSelector
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import FewShotPromptTemplate
from langchain.chains.sql_database.prompt import PROMPT_SUFFIX, _mysql_prompt
from langchain.prompts.prompt import PromptTemplate
from langchain_experimental.sql import SQLDatabaseChain
from transformers import GPT4, Claude

# Alternative Language Models
from langchain.llms import OpenAI, Anthropic

# Creating an LLM object with GPT-4 or Claude
api_key = 'my key'
# llm = GooglePalm(google_api_key=api_key, temperature=0.2)  # Original
llm = OpenAI(api_key=api_key, model_name='gpt-4', temperature=0.2)  # Using GPT-4
# llm = Anthropic(api_key=api_key, model_name='claude', temperature=0.2)  # Using Claude

# Creating a DB connection with connection pooling and potential caching layer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import redis

db_user = "your_user"
db_password = "your_password"
db_host = "your_host"
db_name = "your_db_name"

# Using SQLAlchemy for connection pooling
engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}", pool_size=10, max_overflow=20)
Session = sessionmaker(bind=engine)
session = Session()

# Redis caching layer
cache = redis.Redis(host='localhost', port=6379, db=0)


# Define a caching function
def cache_query(query, result=None):
    if result:
        cache.set(query, result)
    return cache.get(query)


# Few-Shot Examples: expanded and dynamically updated
few_shots = [
    {'Question': "How many t-shirts do we have left for Nike in XS size and white color?",
     'SQLQuery': "SELECT sum(stock_quantity) FROM t_shirts WHERE brand = 'Nike' AND color = 'White' AND size = 'XS'",
     'SQLResult': "Result of the SQL query",
     'Answer': 55},
    {'Question': "How much is the total price of the inventory for all S-size t-shirts?",
     'SQLQuery': "SELECT SUM(price*stock_quantity) FROM t_shirts WHERE size = 'S'",
     'SQLResult': "Result of the SQL query",
     'Answer': 8576},
    {
        'Question': "If we have to sell all the Levi’s T-shirts today with discounts applied, how much revenue will our store generate (post discounts)?",
        'SQLQuery': """SELECT sum(a.total_amount * ((100-COALESCE(discounts.pct_discount,0))/100)) as total_revenue FROM
                   (SELECT sum(price*stock_quantity) as total_amount, t_shirt_id FROM t_shirts WHERE brand = 'Levi'
                   GROUP BY t_shirt_id) a LEFT JOIN discounts ON a.t_shirt_id = discounts.t_shirt_id""",
        'SQLResult': "Result of the SQL query",
        'Answer': 16735.00},
    {
        'Question': "If we have to sell all the Levi’s T-shirts today, how much revenue will our store generate without discount?",
        'SQLQuery': "SELECT SUM(price * stock_quantity) FROM t_shirts WHERE brand = 'Levi'",
        'SQLResult': "Result of the SQL query",
        'Answer': 16735},
    {'Question': "How many white color Levi's shirts do I have?",
     'SQLQuery': "SELECT sum(stock_quantity) FROM t_shirts WHERE brand = 'Levi' AND color = 'White'",
     'SQLResult': "Result of the SQL query",
     'Answer': 187}
    # Add more diverse examples as needed
]

# Embeddings: Exploring advanced models and fine-tuning
embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
# embeddings = HuggingFaceEmbeddings(model_name='bert-base-uncased')  # Alternative model
# Fine-tuning embeddings on domain-specific data (if available)

to_vectorize = [" ".join(example.values()) for example in few_shots]

# Vector Store: Alternatives and regular reindexing
vectorstore = Chroma.from_texts(to_vectorize, embeddings, metadatas=few_shots)
# vectorstore = FAISS.from_texts(to_vectorize, embeddings, metadatas=few_shots)  # Alternative
# vectorstore = Pinecone.from_texts(to_vectorize, embeddings, metadatas=few_shots)  # Another alternative

# Semantic Similarity Selector: Experimenting with different metrics
example_selector = SemanticSimilarityExampleSelector(
    vectorstore=vectorstore,
    k=2,
    # metric='euclidean'  # Alternative metric
)

example_selector.select_examples({"Question": "How many Adidas T-shirts do I have left in my store?"})

# MySQL Prompt Template with improvements
mysql_prompt = """You are a MySQL expert. Given an input question, first create a syntactically correct MySQL query to run, then look at the results of the query and return the answer to the input question.
Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. If there is a need to show the result in the table when the 
user mentioned the number of outputs needed like top 10 items, you should return the output in the table format. You can order the results to return the most informative data in the database.
Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks () to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use CURDATE() function to get the current date, if the question involves "today".

Use the following format:

Question: Question here
SQLQuery: Query to run with no pre-amble
SQLResult: Result of the SQLQuery
Answer: Final answer here

No pre-amble.
"""

# Example Prompt Template
example_prompt = PromptTemplate(
    input_variables=["Question", "SQLQuery", "SQLResult", "Answer"],
    template="\nQuestion: {Question}\nSQLQuery: {SQLQuery}\nSQLResult: {SQLResult}\nAnswer: {Answer}",
)

# Few-Shot Prompt Template
few_shot_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=example_prompt,
    prefix=mysql_prompt,
    suffix=PROMPT_SUFFIX,
    input_variables=["input", "table_info", "top_k"],
)

# SQL Database Chain with enhancements
new_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True, prompt=few_shot_prompt)


# Error handling, query optimization, and feedback loop
def execute_query(chain, question):
    try:
        # Check cache first
        cached_result = cache_query(question)
        if cached_result:
            return cached_result

        # Execute the query
        result = chain.run(question)

        # Cache the result
        cache_query(question, result)

        return result
    except Exception as e:
        print(f"Error executing query: {e}")
        # Implement fallback strategy
        return "There was an error processing your query. Please try again later."


# Modularity and preprocessing
def preprocess_question(question):
    # Add preprocessing steps such as cleaning and standardizing input
    return question.strip().lower()


def postprocess_answer(answer):
    # Add post-processing steps to format and enhance the final answer
    return answer


# Main function to handle the query
def handle_query(question):
    preprocessed_question = preprocess_question(question)
    answer = execute_query(new_chain, preprocessed_question)
    return postprocess_answer(answer)


# Example usage
question = "How many Adidas T-shirts do I have left in my store?"
print(handle_query(question))

# Additional improvements for performance, security, scalability, and user feedback integration
# For example, integrating a user feedback mechanism or implementing multi-language support.
