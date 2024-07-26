# query_validation.py
from sqlparse import parse


def validate_query(query):
    parsed = parse(query)[0]
    if parsed.get_type() != 'SELECT':
        raise ValueError("Only SELECT queries are allowed")
    # Add more checks as needed

