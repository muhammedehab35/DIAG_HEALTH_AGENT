"""
openai_client.py
----------------
Centralized OpenAI client with API key rotation for the RAG Diagnostic AI project.

Usage:
    from utils.openai_client import get_openai_client
    client = get_openai_client()
    response = client.chat.completions.create(...)

All agents should use get_openai_client() to ensure robust key rotation and single-point configuration.
"""
import os
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
from utils.openai_keys import get_random_openai_key

# Optionally: add any global OpenAI configuration here (e.g., timeout, base_url)

DEFAULT_OPENAI_MODEL = os.getenv("DEFAULT_OPENAI_MODEL", "gpt-4o")

def get_default_openai_model():
    """
    Returns the default OpenAI model name from environment/config.
    All agents should use this for model selection.
    """
    return DEFAULT_OPENAI_MODEL

def get_openai_client(**kwargs):
    """
    Returns an OpenAI client with a randomly selected API key.
    Passes through any additional kwargs to the OpenAI constructor.
    """
    api_key = get_random_openai_key()
    return OpenAI(api_key=api_key, **kwargs)
