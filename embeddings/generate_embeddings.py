"""
generate_embeddings.py
---------------------
This script generates vector embeddings for all symptoms in the SQLite medical knowledge base using a Sentence Transformers model (all-MiniLM-L6-v2).

Purpose:
- Converts each symptom into a high-dimensional vector representation (embedding) for semantic search and retrieval.
- Stores these embeddings as binary blobs in a new table (symptom_embeddings), linked to the corresponding symptom IDs.
- Enables fast, accurate similarity search for downstream retrieval-augmented generation (RAG) and AI agent workflows.

How it works:
1. Loads all symptoms from the database.
2. Uses a transformer model to convert each symptom into a vector.
3. Stores each vector (embedding) in the database for future retrieval.

This is a foundational step for enabling semantic search and multi-agent reasoning in the healthcare AI assistant.
"""
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../db/symptoms.db')
MODEL_NAME = 'all-MiniLM-L6-v2'  # Small, fast, and high quality for semantic search

def get_symptoms(conn):
    """
    Fetches all symptoms from the database.
    Args:
        conn (sqlite3.Connection): Open SQLite connection.
    Returns:
        List of tuples: (symptom_id, symptom_text)
    """
    c = conn.cursor()
    c.execute('SELECT id, symptom FROM symptoms')
    return c.fetchall()

def create_embeddings_table(conn, dim):
    """
    Creates the symptom_embeddings table if it doesn't exist.
    Args:
        conn (sqlite3.Connection): Open SQLite connection.
        dim (int): Dimension of the embedding vector (for reference/future use).
    """
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS symptom_embeddings (
        symptom_id INTEGER PRIMARY KEY,
        embedding BLOB NOT NULL,
        FOREIGN KEY(symptom_id) REFERENCES symptoms(id)
    )''')
    conn.commit()

def store_embedding(conn, symptom_id, embedding):
    """
    Stores an embedding vector as a binary blob in the database.
    Args:
        conn (sqlite3.Connection): Open SQLite connection.
        symptom_id (int): ID of the symptom.
        embedding (np.ndarray): Embedding vector.
    """
    c = conn.cursor()
    # Convert numpy array to binary
    emb_blob = embedding.astype(np.float32).tobytes()
    c.execute('INSERT OR REPLACE INTO symptom_embeddings (symptom_id, embedding) VALUES (?, ?)', (symptom_id, emb_blob))
    conn.commit()

def main():
    """
    Main routine to generate and store embeddings for all symptoms in the DB.
    Loads the transformer model, fetches symptoms, computes embeddings, and saves them.
    """
    print(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    conn = sqlite3.connect(DB_PATH)
    symptoms = get_symptoms(conn)
    if not symptoms:
        print("No symptoms found in DB. Run preprocessing first.")
        return
    # Get embedding dimension from a test vector
    test_emb = model.encode([symptoms[0][1]])[0]
    create_embeddings_table(conn, len(test_emb))
    print(f"Generating embeddings for {len(symptoms)} symptoms...")
    for symptom_id, symptom_text in symptoms:
        # Encode symptom text to embedding vector
        emb = model.encode([symptom_text])[0]
        store_embedding(conn, symptom_id, emb)
    print(f"Stored embeddings for {len(symptoms)} symptoms in symptom_embeddings table.")
    conn.close()

if __name__ == '__main__':
    main()
