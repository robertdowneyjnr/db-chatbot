import os
import logging
from dotenv import load_dotenv


def setup_logging():
    logging.basicConfig(level=logging.INFO)


def load_config():
    load_dotenv()
    return {
        'api_key': os.getenv('API_KEY'),
        'db_user': os.getenv('DB_USER'),
        'db_password': os.getenv('DB_PASSWORD'),
        'db_host': os.getenv('DB_HOST'),
        'db_name': os.getenv('DB_NAME'),
    }
