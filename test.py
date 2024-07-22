from database import connect_to_database
from config import load_config
from embedding import embeddings
from sqlalchemy import inspect
from langchain_community.embeddings import OpenAIEmbeddings

#print(embeddings.encode('Hi')[0])

#print(embeddings().embed_query('Hi'))

emb = OpenAIEmbeddings()
config = load_config()

print(config['api_key'])

db = connect_to_database()
inspector = inspect(db._engine)

print(db.get_table_names())

print(inspector.get_columns('t_shirts'))
#print(db.get_context())

#print(db.get_table_info())
