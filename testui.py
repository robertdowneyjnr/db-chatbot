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
        try:
            st.session_state.redis_client = RedisConnection.get_instance(
                host=config['redis_host'],
                port=config['redis_port'],
                password=config['redis_password']
            )
        except Exception as e:
            st.error(f"Failed to connect to Redis: {e}")
            st.session_state.redis_client = None

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

    # Store session names and IDs in Redis
    if 'session_names' not in st.session_state:
        st.session_state.session_names = {}

    # Display session names on the left side
    with st.sidebar:
        st.subheader("Sessions")
        selected_session_name = None
        for session_name, session_id in st.session_state.session_names.items():
            if st.button(session_name):
                selected_session_name = session_name
                selected_session_id = session_id

    # Display chat history for selected session in main chat area
    if selected_session_name:
        session_memory = RedisMemory(st.session_state.redis_url, selected_session_id)
        for message in session_memory.get_messages():
            with st.chat_message(message.type):
                st.markdown(message.content)

    # React to user input
    if prompt := st.chat_input("What would you like to know about our t-shirts?"):
        # Update session activity
        st.session_state.session_manager.update_activity()

        # Use existing session memory instance if a session is selected
        if selected_session_name:
            session_memory = RedisMemory(st.session_state.redis_url, selected_session_id)
        else:
            # Generate a session name and ID
            session_name = RedisMemory.generate_session_name(prompt)
            session_id = RedisMemory.generate_session_id(prompt)
            st.session_state.session_names[session_name] = session_id
            session_memory = RedisMemory(st.session_state.redis_url, session_id)

        # Display user message in chat message container
        st.chat_message("human").markdown(prompt)
        # Add user message to Redis memory
        session_memory.add_message("human", prompt)

        # Check if the question is relevant to the database
        relevant_docs = retriever.get_relevant_documents(prompt)
        if not relevant_docs:
            response = "I'm sorry, but this question doesn't seem to be related to our t-shirt database. Could you please ask a question about our t-shirt inventory?"
            st.chat_message("assistant").markdown(response)
            session_memory.add_message("ai", response)
        else:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                # Use synchronous run instead of async
                context = "\n".join([f"{'Human' if msg.type == 'human' else 'AI'}: {msg.content}" for msg in
                                     session_memory.get_messages()])
                contextualized_prompt = f"{context}\n\nHuman: {prompt}\nAI:"
                result = async_chain.run(contextualized_prompt)

                for chunk in result.split():
                    full_response += chunk + " "
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.05)
                message_placeholder.markdown(full_response)

            # Add assistant response to Redis memory
            session_memory.add_message("ai", full_response)

    # Display Redis connection status
    if st.session_state.redis_client:
        try:
            st.session_state.redis_client.ping()
            st.sidebar.success("Redis connection is active.")
        except Exception as e:
            st.sidebar.error(f"Redis connection error: {e}")
    else:
        st.sidebar.error("Redis client is not initialized.")
