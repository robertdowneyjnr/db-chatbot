import logging

logger = logging.getLogger(__name__)


def record_feedback(question, generated_query, actual_query, feedback):
    # Store this information in a database or file for later analysis
    logger.info(f"Feedback recorded for question: {question}")
    pass
