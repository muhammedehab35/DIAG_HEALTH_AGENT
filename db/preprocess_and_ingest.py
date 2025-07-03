"""
preprocess_and_ingest.py
------------------------
Preprocesses the symptoms_data.csv file and ingests it into a normalized SQLite database for use in a RAG-driven diagnostic AI assistant.

This script:
- Cleans and validates the medical symptoms dataset.
- Splits multi-value fields (conditions, follow-up questions) for relational storage.
- Creates a normalized schema with tables for symptoms, conditions, questions, and their relationships.
- Populates the SQLite database, enabling fast, robust retrieval and downstream embedding.

This is the foundation for the knowledge base powering multi-agent retrieval-augmented generation (RAG) and diagnostic reasoning.
"""
import pandas as pd
import sqlite3
import os

# Paths to source CSV and target SQLite DB
CSV_PATH = os.path.join(os.path.dirname(__file__), '../data/symptoms_data.csv')
DB_PATH = os.path.join(os.path.dirname(__file__), 'symptoms.db')

def clean_text(text):
    """
    Cleans and normalizes input text: strips whitespace, converts NaN to empty string.
    Args:
        text (str): Input text or NaN.
    Returns:
        str: Cleaned string.
    """
    if pd.isna(text):
        return ''
    return str(text).strip()

def preprocess_csv(csv_path):
    """
    Loads and preprocesses the symptoms CSV file.
    - Converts symptoms to lowercase and trims whitespace.
    - Splits conditions (by comma) and follow-up questions (by semicolon) into lists.
    Args:
        csv_path (str): Path to the CSV file.
    Returns:
        pd.DataFrame: Cleaned and structured DataFrame.
    """
    df = pd.read_csv(csv_path)
    df['symptom'] = df['symptom'].apply(lambda x: clean_text(x).lower())
    df['conditions'] = df['conditions'].apply(lambda x: [clean_text(c).lower() for c in str(x).split(',')])
    df['follow_up_questions'] = df['follow_up_questions'].apply(lambda x: [clean_text(q) for q in str(x).split(';')])
    return df

def create_schema(conn):
    """
    Creates normalized SQLite tables for symptoms, conditions, questions, and their relationships.
    Args:
        conn (sqlite3.Connection): SQLite DB connection.
    """
    c = conn.cursor()
    # Table for unique symptoms
    c.execute('''CREATE TABLE IF NOT EXISTS symptoms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symptom TEXT UNIQUE NOT NULL
    )''')
    # Table for unique conditions
    c.execute('''CREATE TABLE IF NOT EXISTS conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        condition TEXT UNIQUE NOT NULL
    )''')
    # Table for unique follow-up questions
    c.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT UNIQUE NOT NULL
    )''')
    # Many-to-many relationship between symptoms and conditions
    c.execute('''CREATE TABLE IF NOT EXISTS symptom_condition (
        symptom_id INTEGER,
        condition_id INTEGER,
        FOREIGN KEY(symptom_id) REFERENCES symptoms(id),
        FOREIGN KEY(condition_id) REFERENCES conditions(id),
        PRIMARY KEY(symptom_id, condition_id)
    )''')
    # Many-to-many relationship between symptoms and follow-up questions
    c.execute('''CREATE TABLE IF NOT EXISTS symptom_question (
        symptom_id INTEGER,
        question_id INTEGER,
        FOREIGN KEY(symptom_id) REFERENCES symptoms(id),
        FOREIGN KEY(question_id) REFERENCES questions(id),
        PRIMARY KEY(symptom_id, question_id)
    )''')
    conn.commit()

def ingest_data(df, conn):
    c = conn.cursor()
    # Insert symptoms
    for _, row in df.iterrows():
        c.execute('INSERT OR IGNORE INTO symptoms (symptom) VALUES (?)', (row['symptom'],))
    conn.commit()
    # Insert conditions and questions, and relationships
    for _, row in df.iterrows():
        c.execute('SELECT id FROM symptoms WHERE symptom=?', (row['symptom'],))
        symptom_id = c.fetchone()[0]
        # Conditions
        for cond in row['conditions']:
            c.execute('INSERT OR IGNORE INTO conditions (condition) VALUES (?)', (cond,))
            c.execute('SELECT id FROM conditions WHERE condition=?', (cond,))
            cond_id = c.fetchone()[0]
            c.execute('INSERT OR IGNORE INTO symptom_condition (symptom_id, condition_id) VALUES (?,?)', (symptom_id, cond_id))
        # Questions
        for q in row['follow_up_questions']:
            c.execute('INSERT OR IGNORE INTO questions (question) VALUES (?)', (q,))
            c.execute('SELECT id FROM questions WHERE question=?', (q,))
            q_id = c.fetchone()[0]
            c.execute('INSERT OR IGNORE INTO symptom_question (symptom_id, question_id) VALUES (?,?)', (symptom_id, q_id))
    conn.commit()

def main():
    df = preprocess_csv(CSV_PATH)
    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)
    ingest_data(df, conn)
    print(f"Ingested {len(df)} symptoms into {DB_PATH}")
    conn.close()

if __name__ == '__main__':
    main()
