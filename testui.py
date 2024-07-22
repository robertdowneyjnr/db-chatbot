import streamlit as st
import asyncio
from session_manager import SessionManager
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Set the page configuration as the first Streamlit command
#st.set_page_config(page_title="SS Assistant", layout="wide")

def render_ui(async_chain, retriever):
    st.title("SS Assistant")

    # Initialize session manager
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()

    # Check activity and update session
    st.session_state.session_manager.check_activity()

    # Initialize chat history and context
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "context" not in st.session_state:
        st.session_state.context = ""

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What would you like to know about our t-shirts?"):
        # Update session activity
        st.session_state.session_manager.update_activity()

        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Check if the question is relevant to the database
        relevant_docs = retriever.get_relevant_documents(prompt)
        if not relevant_docs:
            response = "I'm sorry, but this question doesn't seem to be related to our t-shirt database. Could you please ask a question about our t-shirt inventory?"
            st.chat_message("assistant").markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""

                # Use synchronous run instead of async
                contextualized_prompt = f"{st.session_state.context}\n\nUser: {prompt}\nAI:"
                result = async_chain.run(contextualized_prompt)

                for chunk in result.split():
                    full_response += chunk + " "
                    message_placeholder.markdown(full_response + "▌")
                    import time
                    time.sleep(0.05)
                message_placeholder.markdown(full_response)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # Update context
            st.session_state.context += f"\nUser: {prompt}\nAI: {full_response}"

    # Display chat history
    with st.sidebar:
        st.subheader("Chat History")
        for message in st.session_state.messages:
            st.write(f"{message['role'].capitalize()}: {message['content'][:50]}...")

    # Add a button to start a new session
    if st.sidebar.button("Start New Session"):
        st.session_state.session_manager.end_session()

    # Display the current context (for debugging purposes)
    # Comment this out in production
    st.sidebar.subheader("Current Context")
    st.sidebar.text_area("Context", st.session_state.context, height=200)

    # Display session timer (for debugging purposes)
    # Comment this out in production
    import time
    remaining_time = max(0, 120 - (time.time() - st.session_state.session_manager.last_activity))
    st.sidebar.write(f"Session expires in: {remaining_time:.0f} seconds")
