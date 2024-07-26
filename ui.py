# ui.py

import streamlit as st
import time
from session_manager import SessionManager
from redis_memory import RedisMemory
from config import load_config
import logging
from redis_connection import RedisConnection


def render_ui(async_chain, retriever):
    st.title("SS Assistant")

    config = load_config()

    # Initialize Redis connection
    if 'redis_client' not in st.session_state:
        st.session_state.redis_client = RedisConnection.get_instance(
            host=config['redis_host'],
            port=config['redis_port'],
            password=config['redis_password']
        )

    if 'redis_url' not in st.session_state:
        st.session_state.redis_url = RedisConnection.get_url(
            host=config['redis_host'],
            port=config['redis_port'],
            password=config['redis_password']
        )

    # Initialize session manager
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()

    # Check activity and update session
    st.session_state.session_manager.check_activity()

    # Initialize Redis memory
    if "redis_memory" not in st.session_state:
        st.session_state.redis_memory = None

    # Display chat messages from history on app rerun
    if st.session_state.redis_memory:
        for message in st.session_state.redis_memory.get_messages():
            with st.chat_message(message.type):
                st.markdown(message.content)

    # React to user input
    if prompt := st.chat_input("What would you like to know about our t-shirts?"):
        # Update session activity
        st.session_state.session_manager.update_activity()

        # Initialize or update Redis memory
        if not st.session_state.redis_memory:
            session_id = RedisMemory.generate_session_id(prompt)
            st.session_state.redis_memory = RedisMemory(st.session_state.redis_url, session_id)

        # Display user message in chat message container
        st.chat_message("human").markdown(prompt)
        # Add user message to Redis memory
        st.session_state.redis_memory.add_message("human", prompt)

        # Check if the question is relevant to the database
        relevant_docs = retriever.get_relevant_documents(prompt)
        if not relevant_docs:
            response = "I'm sorry, but this question doesn't seem to be related to our t-shirt database. Could you please ask a question about our t-shirt inventory?"
            st.chat_message("assistant").markdown(response)
            st.session_state.redis_memory.add_message("ai", response)
        else:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                # Use synchronous run instead of async
                context = "\n".join([f"{'Human' if msg.type == 'human' else 'AI'}: {msg.content}" for msg in
                                     st.session_state.redis_memory.get_messages()])
                contextualized_prompt = f"{context}\n\nHuman: {prompt}\nAI:"
                result = async_chain.run(contextualized_prompt)

                for chunk in result.split():
                    full_response += chunk + " "
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.05)
                message_placeholder.markdown(full_response)

            # Add assistant response to Redis memory
            st.session_state.redis_memory.add_message("ai", full_response)

    # Display chat history
    with st.sidebar:
        st.subheader("Chat History")
        if st.session_state.redis_memory:
            for message in st.session_state.redis_memory.get_messages():
                st.write(f"{'Human' if message.type == 'human' else 'AI'}: {message.content[:50]}...")

    # Add a button to start a new session
    if st.sidebar.button("Start New Session"):
        st.session_state.session_manager.end_session()
        st.session_state.redis_memory = None
        st.experimental_rerun()

    # Display the current context (for debugging purposes)
    # Comment this out in production
    st.sidebar.subheader("Current Context")
    if st.session_state.redis_memory:
        context = "\n".join([f"{'Human' if msg.type == 'human' else 'AI'}: {msg.content}" for msg in
                             st.session_state.redis_memory.get_messages()])
        st.sidebar.text_area("Context", context, height=200)

    # Display session timer (for debugging purposes)
    # Comment this out in production
    remaining_time = max(0, 120 - (time.time() - st.session_state.session_manager.last_activity))
    st.sidebar.write(f"Session expires in: {remaining_time:.0f} seconds")

    # Display Redis connection status
    try:
        st.session_state.redis_client.ping()
        st.sidebar.success("Redis connection is active.")
    except Exception as e:
        st.sidebar.error(f"Redis connection error: {e}")

