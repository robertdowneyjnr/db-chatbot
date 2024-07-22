from langchain_community.utilities import SQLDatabase
from config import load_config


def connect_to_database():
    config = load_config()
    try:
        db = SQLDatabase.from_uri(
            f"mysql+pymysql://{config['db_user']}:{config['db_password']}@{config['db_host']}/{config['db_name']}",
            sample_rows_in_table_info=3
        )
        return db
    except Exception as e:
        raise Exception(f"Database connection failed: {e}")
