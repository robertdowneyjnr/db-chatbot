# session_manager.py
import time
from threading import Timer


class SessionManager:
    def __init__(self, timeout=120):  # 120 seconds = 2 minutes
        self.timeout = timeout
        self.last_activity = time.time()
        self.timer = None
        self.reset_timer()

    def reset_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = Timer(self.timeout, self.end_session)
        self.timer.start()

    def update_activity(self):
        self.last_activity = time.time()
        self.reset_timer()

    def end_session(self):
        # Clear the session state
        import streamlit as st
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

    def check_activity(self):
        if time.time() - self.last_activity > self.timeout:
            self.end_session()
        else:
            self.update_activity()
