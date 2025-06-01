import streamlit as st
import base64
from utils.db import fetch_domains
from streamlit_js_eval import streamlit_js_eval
import os

# --- Page Config ---
st.set_page_config(
    page_title="BizLink Intelligence",
    page_icon=":bulb:",
    layout="centered"
)


# --- Custom Styles ---
def inject_styles():
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"], [data-testid="stSidebar"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

inject_styles()

# --- Utility Functions ---
def load_base64_image(path):
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"

def show_logo(margin_bottom="4rem"):
    col1, col2, col3 = st.columns([1, 4, 1])
    icon_src = load_base64_image("assets/mark.png")
    text_src = load_base64_image("assets/logo.png")
    with col2:
        st.markdown(
            f"""
            <div style='text-align: center;'>
                <div style="display: flex; align-items: center; justify-content: center;margin-bottom: {margin_bottom};">
                    <img src="{icon_src}" width="60" style="margin-bottom: 4px;"/>
                    <img src="{text_src}" width="250"/>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# --- 1. 로그인 전: 안내/소개 페이지 ---
if not getattr(st.user, "is_logged_in", False):
    # 로그인 상태
    show_logo()
    # 타이틀 및 설명
    st.markdown(
        """
        <div style='display: flex; align-items: center; gap: 10px;'>
            <span style='font-size: 2.2em;'>💡</span>
            <span style='font-size: 2.2em; font-weight: bold;'>BizLink Intelligence Portal</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write(
    """
        **Welcome to the BizLink Intelligence Portal!**

        This portal is your secure gateway to powerful data analysis and visualization tools, available exclusively to authenticated users.

        After logging in, you can:
        - Explore and analyze a wide range of business data
        - Access tailored reports and interactive dashboards
        - Gain actionable insights to support your decision-making

        All features are protected by robust authentication, ensuring your data remains safe and confidential.

        Need help? Check out our [User Guide](https://seocoglobal.com) for step-by-step instructions.
        """
    )

    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown('<div style="margin-bottom: 32px;"></div>', unsafe_allow_html=True)
        if st.button("🔐 Login With Google", key="login_btn", use_container_width=True):
            user = st.login()
        st.stop()



st.session_state.user_email = st.user.email
st.session_state.user_name = st.user.name

show_logo(margin_bottom="2rem")
# 도메인 선택 (최초 1회)
if "target_database" not in st.session_state:
    user_domains = fetch_domains(st.user.email)
    user_domains = [d for d in user_domains if d["target_database"]]
    if len(user_domains) == 0:
        st.error("No service available for your account.")
        st.stop()
    else:
        chosen = user_domains[0]
        st.session_state.domain_code = chosen["domain_code"]
        st.session_state.target_database = chosen["target_database"]
        #save_domain_to_localstorage(chosen["domain_code"], chosen["target_database"])
        st.rerun()

# 메인 UI
col1, col2 = st.columns([7, 2])
with col1:
    st.markdown(f"""
        <div style='text-align: left;'>
            <div style='font-size: 16px; color: grey; margin-bottom: 20px;'>
                Account: <code>{st.session_state.user_email}</code> &nbsp;|&nbsp;
                Domain: <b>{st.session_state.domain_code}</b> &nbsp;
            </div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    if st.button("🔓 Log out"):
        st.logout()

st.markdown('<div style="margin-bottom: 42px;"></div>', unsafe_allow_html=True)
# Navigation Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Sales Report", key="sales_report_btn", use_container_width=True):
        st.switch_page("pages/salesreport.py")
#with col2:
    # if st.button("Date Range", key="reports_btn", use_container_width=True):
    #     st.switch_page("pages/reports.py")
#with col3:
    # if st.button("Settings", key="settings_btn", use_container_width=True):
    #     st.switch_page("pages/settings.py")


