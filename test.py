from database import connect_to_database
from config import load_config
from embedding import embeddings
from sqlalchemy import inspect
from langchain_community.embeddings import OpenAIEmbeddings,HuggingFaceEmbeddings
from redis_memory import RedisMemory
from config import load_config
import logging
from redis_connection import RedisConnection
#print(embeddings.encode('Hi')[0])

#print(embeddings().embed_query('Hi'))
config = load_config()
a = RedisConnection.get_instance(
            host=config['redis_host'],
            port=config['redis_port'],
            password=config['redis_password']
        )



print(a)
'''
emb = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
config = load_config()

print(config['api_key'])

db = connect_to_database()
inspector = inspect(db._engine)

print(db.get_table_names())

print(inspector.get_columns('t_shirts'))
#print(db.get_context())

#print(db.get_table_info())
'''