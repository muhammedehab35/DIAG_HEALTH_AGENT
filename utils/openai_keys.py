import os
import random
from dotenv import load_dotenv

load_dotenv()

def get_random_openai_key():
    keys = os.getenv("OPENAI_API_KEYS", "")
    key_list = [k.strip() for k in keys.split(",") if k.strip()]
    if not key_list:
        raise RuntimeError("No OpenAI API keys found in environment variable OPENAI_API_KEYS")
    return random.choice(key_list)
