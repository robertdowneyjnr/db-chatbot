import streamlit as st
from config import setup_logging, load_config
from database import connect_to_database
from async_chain import create_async_chain
from feedback import record_feedback
#from retriever import create_retriever
from testretriever import create_retriever
from ui import render_ui

#from testui import render_ui
setup_logging()


def main():
    st.set_page_config(page_title="SS Assistant", layout="wide")

    config = load_config()
    db = connect_to_database()
    async_chain = create_async_chain(db)
    retriever = create_retriever(db)

    render_ui(async_chain, retriever)


if __name__ == "__main__":
    main()
