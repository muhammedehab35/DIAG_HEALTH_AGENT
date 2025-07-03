"""
agent_orchestrator.py
---------------------
AgentOrchestrator module for the RAG-driven healthcare assistant.

Purpose:
- Manages the flow between Diagnostic, Recommendation, and Explanation agents.
- Maintains dialogue state, user profile, and context across turns.
- Provides a single interface for multi-turn, multi-agent dialogue.
- Designed for easy integration with Streamlit UI or other frontend interfaces.

How it works:
1. Receives user input (symptoms, answers, profile info) and chat history.
2. Calls DiagnosticAgent for next question or diagnosis.
3. If diagnosis is reached, calls RecommendationAgent for advice.
4. Optionally calls ExplanationAgent to provide reasoning.
5. Returns a structured response for UI rendering.

This enables seamless, context-aware, multi-agent collaboration in the AI assistant.
"""
from agents.diagnostic_agent import DiagnosticAgent
from agents.recommendation_agent import RecommendationAgent
from agents.explanation_agent import ExplanationAgent

import logging

class AgentOrchestrator:
    """
    Orchestrates the workflow between Diagnostic, Recommendation, and Explanation agents.
    Maintains dialogue state and coordinates agent responses.

    max_followups (int or None): Maximum number of follow-up questions per session. If None, unlimited follow-ups.
    This limit is set for optimal user experience and clinical safety, and is configurable for research/product tuning. Set to None to disable the limit.
    """
    def __init__(self, max_followups):
        """
        max_followups is set by the app globally (see app.py: MAX_FOLLOWUPS)
        """
        self.diagnostic_agent = DiagnosticAgent()
        self.recommendation_agent = RecommendationAgent()
        self.explanation_agent = ExplanationAgent()
        self.max_followups = max_followups
        self.state = {
            'profile': {},
            'chat_history': [],
            'context': None,
            'followup_count': 0,
            'diagnosis_complete': False
        }

    def step(self, user_input, profile=None):
        """
        Processes a single user turn and advances the dialogue.
        Args:
            user_input (str): The user's message (symptoms, answers, etc.).
            profile (dict, optional): User profile (age, gender, known conditions, etc.).
        Returns:
            dict: Structured response containing agent outputs and next UI action.
        """
        # Update profile if provided
        if profile:
            self.state['profile'] = profile

        # Call DiagnosticAgent for next question or diagnosis
        diag_result = self.diagnostic_agent.next(
            user_input,
            profile=self.state['profile'],
            chat_history=self.state['chat_history'],
            followup_count=self.state['followup_count'],
            max_followups=self.max_followups
        )
        self.state['chat_history'].append({'user': user_input, 'agent': diag_result['response']})
        self.state['context'] = diag_result.get('context')

        # If follow-up is needed and (max_followups is None or not reached), return diagnostic response
        followups_allowed = (self.max_followups is None) or (self.state['followup_count'] < self.max_followups)
        if diag_result['follow_up'] and followups_allowed:
            self.state['followup_count'] += 1
            return {
                'agent': 'diagnostic',
                'response': diag_result['response'],
                'context': self.state['context'],
                'next_action': 'ask_followup',
                'followup_count': self.state['followup_count'],
                'max_followups': self.max_followups
            }

        # If we've just exhausted follow-ups, force a diagnosis summary
        if diag_result['follow_up'] and not followups_allowed:
            # Force a summary diagnosis by simulating no more followups available
            summary_diag = self.diagnostic_agent.next(
                user_input,
                profile=self.state['profile'],
                chat_history=self.state['chat_history'],
                followup_count=self.max_followups + 1,  # ensure > max
                max_followups=self.max_followups
            )
            diag_result = {
                'agent': 'diagnostic',
                'response': f"Based on your symptoms, possible conditions: {', '.join(summary_diag.get('context', {}).get('conditions', [])) if summary_diag.get('context') else 'Unknown'}",
                'follow_up': False,
                'context': summary_diag.get('context'),
                'forced_diagnosis': True  # UI can use this to show a visible message
            }
            self.state['context'] = summary_diag.get('context')

        # Proceed to recommendation and explanation
        rec_result = self.recommendation_agent.recommend(
            self.state['context'],
            profile=self.state['profile']
        )
        exp_result = self.explanation_agent.explain(
            self.state['context'],
            recommendation=rec_result['response'],
            profile=self.state['profile']
        )
        self.state['diagnosis_complete'] = True

        diagnosis = diag_result['response'] if not diag_result['follow_up'] else ""
        return {
            'agent': 'orchestrator',
            'diagnosis': diagnosis,
            'recommendation': rec_result['response'],
            'explanation': exp_result['response'],
            'context': self.state['context'],
            'next_action': 'complete',
            'followup_count': self.state['followup_count'],
            'max_followups': self.max_followups
        }

# Test function
if __name__ == '__main__':
    orchestrator = AgentOrchestrator()
    profile = {'age': 28, 'gender': 'female', 'known_conditions': ['migraine']}
    user_input = "I have a severe headache and light sensitivity"
    print("--- Step 1 ---")
    result = orchestrator.step(user_input, profile)
    print(result)
    # Simulate user answering follow-up
    if result['next_action'] == 'ask_followup':
        print("--- Step 2 ---")
        followup_input = "Yes, I also feel nauseous."
        result2 = orchestrator.step(followup_input)
        print(result2)
