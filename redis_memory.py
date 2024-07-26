# redis_memory.py
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.schema import HumanMessage, AIMessage
import logging


class RedisMemory:
    def __init__(self, redis_url, session_id):
        self.redis_url = redis_url
        self.session_id = session_id
        try:
            self.history = RedisChatMessageHistory(url=self.redis_url, session_id=self.session_id)
        except Exception as e:
            logging.error(f"Failed to initialize RedisChatMessageHistory: {e}")
            self.history = None

    def add_message(self, role, content):
        if self.history is None:
            logging.error("RedisChatMessageHistory is not initialized")
            return

        if role == "human":
            message = HumanMessage(content=content)
        elif role == "ai":
            message = AIMessage(content=content)
        else:
            raise ValueError(f"Unsupported role: {role}")

        try:
            self.history.add_message(message)
        except Exception as e:
            logging.error(f"Failed to add message to Redis: {e}")

    def get_messages(self):
        if self.history is None:
            logging.error("RedisChatMessageHistory is not initialized")
            return []

        try:
            return self.history.messages
        except Exception as e:
            logging.error(f"Failed to get messages from Redis: {e}")
            return []

    def clear(self):
        if self.history is None:
            logging.error("RedisChatMessageHistory is not initialized")
            return

        try:
            self.history.clear()
        except Exception as e:
            logging.error(f"Failed to clear Redis history: {e}")

    @staticmethod
    def generate_session_id(question):
        import hashlib
        return f"session:{hashlib.md5(question.encode()).hexdigest()[:10]}"

    @staticmethod
    def generate_session_name(question):
        # Generate a session name based on the question (e.g., first few words)
        return ' '.join(question.split()[:5])