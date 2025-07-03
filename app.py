# --- AGENT ORCHESTRATOR IMPORT ---
# We import the AgentOrchestrator class, which is the "brain" that manages
# the conversation flow between the diagnostic, recommendation, and explanation agents.
# This allows our Streamlit app to have a smart, multi-turn, healthcare chat experience.
import streamlit as st
from agents.agent_orchestrator import AgentOrchestrator
import logging

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --- AGENT ORCHESTRATOR SESSION STATE ---
# We use Streamlit's session_state to keep our AgentOrchestrator "alive" across user actions.
# This means the AI assistant will remember the conversation and context, even if the page reruns.
# --- GLOBAL CONFIGURATION ---
# Set the maximum number of follow-up questions for the entire app here.
MAX_FOLLOWUPS = 3  # Change this value to control follow-up limit globally

if 'orchestrator' not in st.session_state:
    st.session_state['orchestrator'] = AgentOrchestrator(max_followups=MAX_FOLLOWUPS)

# --- Onboarding Banner (universally compatible) ---
# --- Hero Banner & Animated Stepper Onboarding ---a
from datetime import datetime

with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Chat Section ---
def chat_interface(tab_key=""):
    st.subheader("💬 Symptom Checker Chat")
    clear_flag = f"clear_symptom_input_{tab_key}"
    input_key = f"symptom_input_{tab_key}"
    # Clear input if flagged (before widget is rendered)
    if st.session_state.get(clear_flag, False):
        st.session_state[input_key] = ""
        st.session_state[clear_flag] = False
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if input_key not in st.session_state:
        st.session_state[input_key] = ""

    # --- Display Chat History above input ---
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='stChatMessage' style='background:#222;padding:0.8em 1em;'><b>You:</b> {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='stChatMessage' style='background:#1f8ef1;padding:0.8em 1em;'><b>Assistant:</b> {msg['content']}</div>", unsafe_allow_html=True)

    # --- Chat Input UI ---
    user_input = st.text_area(
        "Describe your symptom(s)...",
        key=input_key,
        value=st.session_state[input_key] or "",
        help=None,
        height=80,
        max_chars=1000
    )

    # Inline help text and utility buttons row
    help_col, util_col = st.columns([2, 1], gap="small")
    with help_col:
        st.markdown("<div style='color:#bbb; font-size:0.97em; padding-top:2px;'>E.g., 'I have a persistent headache and nausea.' This field is accessible for screen readers.</div>", unsafe_allow_html=True)
    with util_col:
        util_btn_col1, util_btn_col2 = st.columns([1,1], gap="small")
        with util_btn_col1:
            clear_chat_key = f"clear_chat_{tab_key}"
            if st.button(
                "Clear Chat",
                key=clear_chat_key,
                help="Clear the chat history for this session. Accessible by keyboard and screen reader."
            ):
                st.session_state.chat_history = []
                st.session_state[f"clear_symptom_input_{tab_key}"] = True
                st.rerun()
        with util_btn_col2:
            if st.session_state.chat_history:
                transcript_lines = []
                for msg in st.session_state.chat_history:
                    role = 'You' if msg['role'] == 'user' else 'Assistant'
                    transcript_lines.append(f"{role}: {msg['content']}")
                transcript_text = '\n'.join(transcript_lines)
                st.download_button(
                    label="Download Transcript",
                    data=transcript_text,
                    file_name="chat_transcript.txt",
                    mime="text/plain",
                    help="Download your chat transcript as a text file.",
                    key=f"download_transcript_{tab_key}"
                )


    # Removed inline CSS for textarea. All textarea styling is now handled in styles.css for modularity and maintainability.

    # Main action row: Submit Symptom (full-width) and Report Issue (side-by-side, business-ready)
    submit_col, feedback_col = st.columns([2,1])
    with submit_col:
        if st.button(
            "Submit Symptom",
            key=f"submit_symptom_{tab_key}_submitcol",
            use_container_width=True,
            help="Submit your symptom to the assistant. Accessible by keyboard and screen reader."
        ):
            if not user_input.strip():
                st.error("Please describe your symptoms before submitting.")
            else:
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat()
                })
                # Show loading spinner while agent responds
                with st.spinner("Thinking..."):
                    orchestrator = st.session_state['orchestrator']
                    profile = st.session_state['profile']
                    result = orchestrator.step(user_input, profile)
                if result.get("next_action") == "ask_followup":
                    st.session_state.chat_history.append({
                        "role": "agent",
                        "content": result["response"],
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    st.session_state['latest_diagnosis'] = result['diagnosis']
                    st.session_state['latest_recommendation'] = result['recommendation']
                    st.session_state['latest_explanation'] = result['explanation']
                    st.session_state['latest_forced_diagnosis'] = result.get('forced_diagnosis', False)
                st.session_state[f"clear_symptom_input_{tab_key}"] = True
                st.rerun()
    with feedback_col:
        if st.button("Report Issue", key=f"report_issue_{tab_key}_feedbackcol", use_container_width=True):
            st.info("Feedback/reporting coming soon!")

# --- Results Section ---
def results_section():
    st.subheader("🔍 Reasoning & Recommendations")
    diagnosis = st.session_state.get("latest_diagnosis", "")
    forced_diag = st.session_state.get("latest_forced_diagnosis", False)
    if forced_diag:
        st.warning("You have reached the maximum number of follow-up questions. A summary diagnosis is now shown.")
    if diagnosis and not diagnosis.strip().lower().startswith("follow-up:"):
        st.markdown(f"**Diagnosis:** {diagnosis}")
        st.markdown(f"**Recommendation:** {st.session_state.get('latest_recommendation','')}")
        st.markdown(f"**Explanation:** {st.session_state.get('latest_explanation','')}")
    else:
        st.info("Start by describing your symptoms above.")

# --- Footer Section ---
def footer_section():
    st.markdown("""
        <div class='footer'>
            &copy; 2025 RAG Diagnostic AI. All rights reserved.<br>
            <a href='#'>Privacy Policy</a> | <a href='#'>Terms of Service</a>
        </div>
    """, unsafe_allow_html=True)

def onboarding_section():
    """
    Render the animated onboarding stepper UI for age, gender, and conditions.
    Sets profile in session_state and advances onboarding step.
    """
    st.markdown("""
        <div class='hero'>
            <div class='hero-title'>🧠 RAG Diagnostic AI Assistant</div>
            <div class='hero-tagline'>Your trusted AI companion for smarter, personalized healthcare guidance.</div>
            <div class='stepper'>
                <div class='step {step1}'><div class='step-circle'>1</div>Age</div>
                <div class='step {step2}'><div class='step-circle'>2</div>Gender</div>
                <div class='step {step3}'><div class='step-circle'>3</div>Conditions</div>
                <div class='step {step4}'><div class='step-circle'>4</div>Chat</div>
            </div>
        </div>
    """.format(
        step1="active" if st.session_state.get("onboard_step", 1) == 1 else "",
        step2="active" if st.session_state.get("onboard_step", 1) == 2 else "",
        step3="active" if st.session_state.get("onboard_step", 1) == 3 else "",
        step4="active" if st.session_state.get("onboard_step", 1) == 4 else ""
    ), unsafe_allow_html=True)

    if "onboard_step" not in st.session_state:
        st.session_state.onboard_step = 1
    profile = st.session_state.get("profile", {"age": None, "gender": None, "conditions": ""})
    step = st.session_state.onboard_step
    fade_css = """
    <style>
    .fade-step {
        animation: fadeInStep 0.5s;
        -webkit-animation: fadeInStep 0.5s;
    }
    @keyframes fadeInStep {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """
    st.markdown(fade_css, unsafe_allow_html=True)
    if step == 1:
        with st.container():
            st.markdown("<div class='fade-step'>", unsafe_allow_html=True)
            age = st.number_input("Enter your age", min_value=0, max_value=100, step=1, key="age_step", value=profile.get("age") or 0)
            next1 = st.button("Next: Gender", key="to_gender", help="Continue to gender selection")
            st.markdown("</div>", unsafe_allow_html=True)
            if next1:
                st.session_state.profile = {**profile, "age": age}
                st.session_state.onboard_step = 2
                st.rerun()
    elif step == 2:
        with st.container():
            st.markdown("<div class='fade-step'>", unsafe_allow_html=True)
            gender = st.selectbox("Select your gender", ["Select...", "Male", "Female", "Other"], key="gender_step", index=(["Select...", "Male", "Female", "Other"].index(profile.get("gender")) if profile.get("gender") else 0))
            next2 = st.button("Next: Conditions", key="to_conditions", help="Continue to conditions entry")
            st.markdown("</div>", unsafe_allow_html=True)
            if next2:
                if gender == "Select...":
                    st.warning("Please select your gender.")
                else:
                    st.session_state.profile = {**profile, "gender": gender}
                    st.session_state.onboard_step = 3
                    st.rerun()
    elif step == 3:
        with st.container():
            st.markdown("<div class='fade-step'>", unsafe_allow_html=True)
            conditions = st.text_input("Known conditions (comma-separated)", key="cond_step", value=profile.get("conditions") or "")
            finish = st.button("Finish Onboarding", key="to_chat", help="Complete onboarding and start chat")
            st.markdown("</div>", unsafe_allow_html=True)
            if finish:
                st.session_state.profile = {**profile, "conditions": conditions}
                st.session_state.onboard_step = 4
                st.rerun()

# Place the main function as before

def main():
    """
    Main entry point for the Streamlit app.
    Renders the three-tab UI: Profile, Chat, Diagnosis. Each tab shows the correct sections.
    """
    onboarding_section()
    # Only show tabs after onboarding is complete
    if st.session_state.get('onboard_step', 1) == 4:
        tab_labels = ["Profile", "Chat", "Diagnosis"]
        tab1, tab2, tab3 = st.tabs(tab_labels)
        with tab1:
            st.subheader("👤 Profile")
            st.write(f"**Age:** {st.session_state.profile.get('age','')}")
            st.write(f"**Gender:** {st.session_state.profile.get('gender','')}")
            st.write(f"**Known Conditions:** {st.session_state.profile.get('conditions','')}")
            st.markdown("---")
            # Only call chat_interface ONCE per tab_key
            chat_interface(tab_key="profile")
            # Optionally, show results below chat (not as a separate call to chat_interface)
            results_section()
        with tab2:
            chat_interface(tab_key="chat")
        with tab3:
            results_section()
    footer_section()

main()
