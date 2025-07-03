"""
Unit tests for DiagnosticAgent, RecommendationAgent, ExplanationAgent, and AgentOrchestrator.
Run with: pytest tests/test_agents.py
"""
import pytest
from agents.diagnostic_agent import DiagnosticAgent
from agents.recommendation_agent import RecommendationAgent
from agents.explanation_agent import ExplanationAgent
from agents.agent_orchestrator import AgentOrchestrator

# --- DiagnosticAgent Tests ---
def test_diagnostic_followup_and_diagnosis():
    agent = DiagnosticAgent()
    profile = {'age': 30, 'gender': 'female'}
    chat_history = []
    user_input = "I have a sore throat and fever"
    # First call should return a follow-up
    result1 = agent.next(user_input, profile, chat_history, followup_count=0, max_followups=2)
    assert result1['follow_up']
    # Second call (simulate answer to follow-up)
    result2 = agent.next("No cough", profile, chat_history, followup_count=1, max_followups=2)
    assert result2['follow_up']
    # Third call (should return diagnosis)
    result3 = agent.next("No headache", profile, chat_history, followup_count=2, max_followups=2)
    assert not result3['follow_up']
    assert "possible conditions" in result3['response']

def test_diagnostic_empty_input():
    agent = DiagnosticAgent()
    result = agent.next("", {}, [], 0, 1)
    assert 'response' in result

# --- RecommendationAgent Tests ---
def test_recommendation_strep():
    agent = RecommendationAgent()
    context = {'conditions': ['strep throat']}
    result = agent.recommend(context)
    assert 'strep throat' in result['response'].lower()

def test_recommendation_empty():
    agent = RecommendationAgent()
    result = agent.recommend({})
    assert 'no specific recommendation' in result['response'].lower()

# --- ExplanationAgent Tests ---
def test_explanation_strep():
    agent = ExplanationAgent()
    context = {'conditions': ['strep throat']}
    result = agent.explain(context)
    assert 'strep throat' in result['response'].lower()

def test_explanation_empty():
    agent = ExplanationAgent()
    result = agent.explain({})
    assert 'no explanation' in result['response'].lower()

# --- AgentOrchestrator Tests ---
def test_orchestrator_full_flow():
    orchestrator = AgentOrchestrator(max_followups=2)
    profile = {'age': 25, 'gender': 'male'}
    # Step 1: Symptom input
    result1 = orchestrator.step("I have a sore throat", profile)
    assert result1['next_action'] == 'ask_followup'
    # Step 2: Follow-up answer
    result2 = orchestrator.step("No cough")
    assert result2['next_action'] == 'ask_followup'
    # Step 3: Final answer (should trigger diagnosis)
    result3 = orchestrator.step("No headache")
    assert result3['next_action'] == 'complete'
    assert 'diagnosis' in result3
    assert 'recommendation' in result3
    assert 'explanation' in result3

def test_orchestrator_empty_input():
    orchestrator = AgentOrchestrator(max_followups=1)
    result = orchestrator.step("")
    # Accept either a follow-up or diagnosis as valid first response, depending on DB/agent logic
    assert (
        result.get('next_action') == 'ask_followup' or
        ('diagnosis' in result and 'recommendation' in result and 'explanation' in result)
    )
