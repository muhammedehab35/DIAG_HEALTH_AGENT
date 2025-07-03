"""
recommendation_agent.py
----------------------
RecommendationAgent module for the RAG-driven healthcare assistant.

Purpose:
- Provides lifestyle or medical advice based on the current diagnostic context and user profile.
- Designed for easy integration of LLMs (OpenAI/GPT-4) for advanced, personalized recommendations.
- Uses mock responses for now to enable rapid end-to-end testing and development.

How it works:
1. Receives current diagnostic context (e.g., most likely conditions) and user profile.
2. Generates a recommendation (mock or LLM-based).
3. Ready to swap in LLM-powered logic when API key is available.
"""
import os
from utils.openai_client import get_openai_client
import logging

class RecommendationAgent:
    """
    RecommendationAgent provides lifestyle or medical advice based on diagnostic context and user profile.
    """
    def __init__(self):
        """
        Initializes the RecommendationAgent.
        Sets up for LLM integration if API key is present.
        """
        self.use_llm = bool(os.getenv("OPENAI_API_KEY"))

    def recommend(self, context, profile=None):
        """
        Generates a recommendation based on diagnostic context and user profile.
        Args:
            context (dict): Diagnostic context (e.g., likely conditions, symptoms).
            profile (dict, optional): User profile (age, gender, known conditions, etc.).
        Returns:
            dict: { 'agent': 'recommendation', 'response': str }
        """
        try:
            # Simple mock logic for demonstration
            if not context or not context.get('conditions'):
                logging.warning('No conditions in context; returning generic recommendation.')
                return {
                    'agent': 'recommendation',
                    'response': 'No specific recommendation available.'
                }
            condition = context['conditions'][0].lower()
            if 'strep' in condition:
                logging.info('Strep condition detected; returning strep recommendation.')
                return {
                    'agent': 'recommendation',
                    'response': 'This might be related to strep throat. Try resting, stay hydrated, and monitor your symptoms. If they worsen, consult a healthcare provider.'
                }
            elif 'migraine' in condition:
                logging.info('Migraine condition detected; returning migraine recommendation.')
                return {
                    'agent': 'recommendation',
                    'response': 'For migraines, rest in a dark room and consider over-the-counter pain relief. If severe, consult a doctor.'
                }
            else:
                logging.info('General condition; returning default recommendation.')
                return {
                    'agent': 'recommendation',
                    'response': f'Please follow general health advice and consult a medical professional if symptoms persist.'
                }
        except Exception as e:
            logging.error('Error in RecommendationAgent.recommend: %s', e, exc_info=True)
            return {
                'agent': 'recommendation',
                'response': 'Sorry, an internal error occurred while generating a recommendation.',
                'error': str(e)
            }

# Test function
if __name__ == '__main__':
    agent = RecommendationAgent()
    context = {'conditions': ['migraine'], 'symptom': 'Headache'}
    profile = {'age': 28, 'gender': 'female', 'known_conditions': ['migraine']}
    result = agent.recommend(context, profile)
    print(f"Agent Response: {result['response']}")
