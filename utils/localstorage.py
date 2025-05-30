import json
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

def save_to_localstorage():
    """
    Save relevant session state variables to browser localStorage via JS.
    This must be called inside a Streamlit-rendered context (e.g., st.empty()).
    """
    if all(k in st.session_state for k in ["domain_code", "target_database"]):
        with st.empty():
            js_code = f"""
                localStorage.setItem('domain_code', '{st.session_state["domain_code"]}');
                localStorage.setItem('target_database', '{st.session_state["target_database"]}');
            """
            streamlit_js_eval(js_expressions=js_code, key="save_to_local")
