"""
retrieve.py
-----------
Retriever module for semantic search over symptoms in the healthcare knowledge base.

Purpose:
- Loads all symptom embeddings from the SQLite database.
- Accepts a user query, generates its embedding, and computes cosine similarity to all stored embeddings.
- Returns the top-k most similar symptoms, along with their associated conditions and follow-up questions.
- Includes a test function for quick validation.

This enables RAG-style retrieval for the AI assistant, powering dynamic, context-aware dialogue and agent reasoning.
"""
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
import heapq
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../db/symptoms.db')
MODEL_NAME = 'all-MiniLM-L6-v2'

class SymptomRetriever:
    """
    SymptomRetriever enables semantic search over symptoms using embeddings and cosine similarity.
    Loads all symptom embeddings and metadata from the database, and retrieves the most relevant symptoms for a user query.
    """
    def __init__(self, db_path=DB_PATH, model_name=MODEL_NAME):
        """
        Initializes the retriever by loading embeddings, metadata, and the transformer model.
        Args:
            db_path (str): Path to SQLite database.
            model_name (str): Name of the transformer model to use for embedding.
        """
        self.conn = sqlite3.connect(db_path)
        self.model = SentenceTransformer(model_name)
        self.embeddings, self.symptom_ids = self._load_embeddings()
        self.symptom_meta = self._load_symptom_metadata()

    def _load_embeddings(self):
        """
        Loads all symptom embeddings from the database.
        Returns:
            np.ndarray: Matrix of embeddings.
            list: List of corresponding symptom IDs.
        """
        c = self.conn.cursor()
        c.execute('SELECT symptom_id, embedding FROM symptom_embeddings')
        rows = c.fetchall()
        symptom_ids = []
        embeddings = []
        for sid, emb_blob in rows:
            symptom_ids.append(sid)
            emb = np.frombuffer(emb_blob, dtype=np.float32)
            embeddings.append(emb)
        return np.vstack(embeddings), symptom_ids

    def _load_symptom_metadata(self):
        """
        Loads metadata (symptom text, associated conditions, follow-up questions) for each symptom.
        Returns:
            dict: Maps symptom_id to its metadata.
        """
        c = self.conn.cursor()
        meta = {}
        for sid in self.symptom_ids:
            c.execute('SELECT symptom FROM symptoms WHERE id=?', (sid,))
            symptom = c.fetchone()[0]
            # Get all conditions linked to this symptom
            c.execute('''SELECT condition FROM conditions \
                         JOIN symptom_condition ON conditions.id = symptom_condition.condition_id \
                         WHERE symptom_condition.symptom_id=?''', (sid,))
            conditions = [row[0] for row in c.fetchall()]
            # Get all follow-up questions linked to this symptom
            c.execute('''SELECT question FROM questions \
                         JOIN symptom_question ON questions.id = symptom_question.question_id \
                         WHERE symptom_question.symptom_id=?''', (sid,))
            questions = [row[0] for row in c.fetchall()]
            meta[sid] = {'symptom': symptom, 'conditions': conditions, 'questions': questions}
        return meta

    def retrieve(self, query, top_k=3):
        """
        Given a user query, generates an embedding and retrieves the top-k most similar symptoms.
        Args:
            query (str): User input describing symptoms.
            top_k (int): Number of top matches to return.
        Returns:
            list: List of dicts with symptom, score, conditions, and questions.
        """
        # Encode the query to an embedding vector
        query_emb = self.model.encode([query])[0]
        # Compute cosine similarity between query and all stored embeddings
        scores = np.dot(self.embeddings, query_emb) / (np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_emb) + 1e-8)
        # Get indices of top-k scores
        top_idx = heapq.nlargest(top_k, range(len(scores)), scores.take)
        results = []
        for idx in top_idx:
            sid = self.symptom_ids[idx]
            meta = self.symptom_meta[sid]
            results.append({'symptom_id': sid, 'score': float(scores[idx]), **meta})
        return results

# Test function
if __name__ == '__main__':
    retriever = SymptomRetriever()
    test_query = "I have a severe headache and light sensitivity"
    print(f"Query: {test_query}\nTop matches:")
    results = retriever.retrieve(test_query, top_k=3)
    for i, res in enumerate(results, 1):
        print(f"\nMatch {i} (score {res['score']:.3f}):")
        print(f"Symptom: {res['symptom']}")
        print(f"Conditions: {', '.join(res['conditions'])}")
        print(f"Follow-up Questions: {', '.join(res['questions'])}")
