import re
import os


def find_emails(string: str):
    """Returns list of found emails from provided string"""
    email_regex = r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,3}'
    return sorted(set(re.findall(email_regex, string)))
