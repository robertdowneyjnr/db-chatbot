# async_chain.py
from langchain_community.llms.google_palm import GooglePalm
from langchain_experimental.sql import SQLDatabaseChain
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from config import load_config
from prompt_template import create_chat_prompt
from langchain import OpenAI
import os


def create_async_chain(db):
    config = load_config()
    # open ai
    os.environ['OPENAI_API_KEY'] = config['api_key']
    llm = OpenAI(temperature=0.1, max_tokens=500)
    # llm = GooglePalm(google_api_key=config['api_key'], temperature=0.2)
    chat_prompt = create_chat_prompt()
    # Set up async callback manager
    async_callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

    return SQLDatabaseChain.from_llm(
        llm,
        db,
        verbose=True,
        prompt=chat_prompt,
        callback_manager=async_callback_manager,
        use_query_checker=True
    )
