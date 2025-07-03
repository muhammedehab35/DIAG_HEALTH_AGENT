"""
explanation_agent.py
-------------------
ExplanationAgent module for the RAG-driven healthcare assistant.

Purpose:
- Explains the reasoning behind the diagnostic and recommendation outcomes.
- Designed for easy integration of LLMs (OpenAI/GPT-4) for advanced, natural language explanations.
- Uses mock responses for now to enable rapid end-to-end testing and development.

How it works:
1. Receives diagnostic context, recommendation, and user profile.
2. Generates a natural language explanation (mock or LLM-based).
3. Ready to swap in LLM-powered logic when API key is available.
"""
import os
from utils.openai_client import get_openai_client
import logging

class ExplanationAgent:
    """
    ExplanationAgent provides explanations for diagnostic and recommendation outcomes.
    """
    def __init__(self):
        """
        Initializes the ExplanationAgent.
        Sets up for LLM integration if API key is present.
        """
        self.use_llm = bool(os.getenv("OPENAI_API_KEY"))

    def explain(self, context, recommendation=None, profile=None):
        """
        Generates a natural language explanation for the diagnosis and/or recommendation.
        Args:
            context (dict): Diagnostic context (e.g., likely conditions, symptoms).
            recommendation (str, optional): Recommendation text.
            profile (dict, optional): User profile (age, gender, known conditions, etc.).
        Returns:
            dict: { 'agent': 'explanation', 'response': str }
        """
        try:
            # Simple mock logic for demonstration
            if not context or not context.get('conditions'):
                logging.warning('No conditions in context; returning generic explanation.')
                return {
                    'agent': 'explanation',
                    'response': 'No explanation available.'
                }
            condition = context['conditions'][0].lower()
            if 'strep' in condition:
                logging.info('Strep condition detected; returning strep explanation.')
                return {
                    'agent': 'explanation',
                    'response': 'This diagnosis is based on your symptom pattern, which aligns with typical cases of strep throat. Further tests or follow-up may refine the diagnosis.'
                }
            elif 'migraine' in condition:
                logging.info('Migraine condition detected; returning migraine explanation.')
                return {
                    'agent': 'explanation',
                    'response': 'Migraine diagnosis is suggested by your history of headaches and sensitivity to light.'
                }
            else:
                logging.info('General condition; returning default explanation.')
                return {
                    'agent': 'explanation',
                    'response': 'The explanation is based on the provided symptoms and medical knowledge.'
                }
        except Exception as e:
            logging.error('Error in ExplanationAgent.explain: %s', e, exc_info=True)
            return {
                'agent': 'explanation',
                'response': 'Sorry, an internal error occurred while generating an explanation.',
                'error': str(e)
            }

# Test function (mock logic)
if __name__ == '__main__':
    agent = ExplanationAgent()
    context = {'conditions': ['migraine'], 'symptom': 'Headache'}
    recommendation = "Try resting in a dark room and monitor your symptoms."
    profile = {'age': 28, 'gender': 'female', 'known_conditions': ['migraine']}
    result = agent.explain(context, recommendation, profile)
    print(f"Agent Response: {result['response']}")

    # --- Real OpenAI test: comment out if you don't want to use your quota ---
    print("\n--- Real OpenAI Test ---")
    client = get_openai_client()
    prompt = (
        "You are a medical assistant. Explain in simple terms why a patient with migraine "
        "might experience headaches and sensitivity to light."
    )
    from utils.openai_client import get_default_openai_model
    response = client.chat.completions.create(
        model=get_default_openai_model(),
        messages=[
            {"role": "system", "content": "You are a helpful medical assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.7,
    )
    print("OpenAI response:")
    print(response.choices[0].message.content)
