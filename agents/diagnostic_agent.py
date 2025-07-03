"""
diagnostic_agent.py
------------------
DiagnosticAgent module for the RAG-driven healthcare assistant.

Purpose:
- Accepts user symptoms and patient profile.
- Uses the retriever to find relevant symptoms, conditions, and follow-up questions from the knowledge base.
- Asks dynamic follow-up questions to refine diagnosis in a multi-turn dialogue.
- Designed for easy integration of LLMs (OpenAI/GPT-4) for advanced reasoning and response generation.
- Uses mock responses for now to enable rapid end-to-end testing and development.

How it works:
1. Receives user symptom input and optional profile/chat history.
2. Retrieves the most relevant symptom context using the semantic retriever.
3. If follow-up questions are available, asks the next question.
4. If no further questions, provides a mock diagnostic summary based on retrieved context.
5. Ready to swap in LLM-powered logic when API key is available.
"""
import os
from retriever.retrieve import SymptomRetriever
# Centralized OpenAI client import (for future LLM logic)
from utils.openai_client import get_openai_client

class DiagnosticAgent:
    """
    DiagnosticAgent orchestrates the diagnostic dialogue for the AI assistant.
    - Accepts user symptoms and profile.
    - Retrieves relevant context (symptoms, conditions, questions).
    - Asks follow-up questions or provides diagnostic feedback.
    - Prepares context for LLM or mock response.
    """
    def __init__(self, retriever=None):
        """
        Initializes the DiagnosticAgent.
        Args:
            retriever (SymptomRetriever, optional): Semantic retriever instance. If not provided, creates a default one.
        """
        self.retriever = retriever or SymptomRetriever()
        # Use LLM if API key is set (for later integration)
        self.use_llm = bool(os.getenv("OPENAI_API_KEY"))

    def next(self, user_input, profile=None, chat_history=None, followup_count=0, max_followups=None):
        """
        Given user input and profile, returns the next agent action (follow-up question or diagnosis).
        Args:
            user_input (str): User's symptom description or answer.
            profile (dict, optional): User profile (age, gender, known conditions, etc.).
            chat_history (list, optional): List of previous (user, agent) turns.
            followup_count (int): Number of follow-ups already asked.
            max_followups (int or None): Maximum allowed follow-ups, or None for unlimited.
        Returns:
            dict: { 'agent': 'diagnostic', 'response': str, 'follow_up': bool, 'context': dict }
        """
        # Retrieve top relevant symptoms/conditions/questions from the knowledge base
        retrieval = self.retriever.retrieve(user_input, top_k=1)
        if retrieval:
            top = retrieval[0]
            # If follow-ups are allowed and not yet exhausted, ask next follow-up
            if top['questions'] and (max_followups is None or followup_count < max_followups):
                question = top['questions'][0]
                return {
                    'agent': 'diagnostic',
                    'response': f"Follow-up: {question}",
                    'follow_up': True,
                    'context': top
                }
            else:
                # If no more follow-ups allowed, give a mock diagnosis summary
                return {
                    'agent': 'diagnostic',
                    'response': f"Based on your symptoms, possible conditions: {', '.join(top['conditions'])}",
                    'follow_up': False,
                    'context': top
                }
        else:
            # If nothing relevant found, return a fallback response
            return {
                'agent': 'diagnostic',
                'response': "Sorry, I couldn't find relevant information for your symptoms.",
                'follow_up': False,
                'context': None
            }

# Test function
if __name__ == '__main__':
    agent = DiagnosticAgent()
    profile = {'age': 28, 'gender': 'female', 'known_conditions': ['migraine']}
    chat_history = []
    user_input = "I have a severe headache and light sensitivity"
    result = agent.next(user_input, profile, chat_history)
    print(f"Agent Response: {result['response']}")
    if result['context']:
        print(f"Context: {result['context']}")
