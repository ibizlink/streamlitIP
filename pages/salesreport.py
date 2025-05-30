import streamlit as st
from utils.db import (
     fetch_domains,
     load_tables,
     fetch_inventory_items,
     fetch_customers
)
from utils.salesquery import(
    process_sales_data,
    runquery_raw
)
from datetime import datetime,timedelta
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd

st.set_page_config(
    page_title="BizLink Intelligence",
    page_icon=":bulb:",
    layout="wide"
)


# --- 쿼리 캐싱 및 데이터 처리 ---
@st.cache_data(show_spinner="Loading sales data...", persist=True)
def get_sales_data(start_date, end_date, selected_item_ids, selected_customer_ids):
    return runquery_raw(start_date, end_date, selected_item_ids, selected_customer_ids)


st.markdown("""
  <style>
        [data-testid="stSidebarNav"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

if not st.user.is_logged_in:
    st.switch_page("home.py")

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

# --- UI ---

# 사이드바 상단에 Home 버튼 추가
if st.sidebar.button("☰"):
    st.switch_page("home.py")

# (아래는 기존 사이드바 내용)
st.sidebar.markdown(f"""User : <b>{st.user.email}</b>""", unsafe_allow_html=True)

st.sidebar.markdown(
    """
    <div style="border-top: 2px solid #e74c3c; margin-top: 10px; margin-bottom: 16px;"></div>
    """,
    unsafe_allow_html=True
)




# --- 사이드바 위젯 ---
start_date = st.sidebar.date_input("Start Date", min_value=datetime(2020, 1, 1), max_value=datetime.today(), value=datetime.today(), key="sidebar_start_date")
end_date = st.sidebar.date_input("End Date", min_value=datetime(2020, 1, 1), max_value=datetime.today(), value=datetime.today(), key="sidebar_end_date")
report_option = st.sidebar.radio("Select Report Category", options=["By Item(s)", "By Customer(s)", "By Invoice Tracking By Date"])

df_inventory_items = fetch_inventory_items()
df_customers = fetch_customers()
item_codes = df_inventory_items['item_code'].tolist()
customer_lists = df_customers['card_name'].tolist()

selected_customers = st.multiselect("Select Customer(s)", options=customer_lists)
selected_items = st.multiselect("Select Item(s)", options=item_codes)

selected_item_ids = df_inventory_items[df_inventory_items['item_code'].isin(selected_items)]['item_id'].tolist() if selected_items else []
selected_customer_ids = df_customers[df_customers['card_name'].isin(selected_customers)]['card_id'].tolist() if selected_customers else []


# 2. 쿼리 입력값(날짜만)
query_inputs = {
    "start_date": start_date,
    "end_date": end_date
}


# 날짜 범위가 바뀌면 쿼리 재실행, 아니면 세션 캐시 사용

if "last_query_inputs" not in st.session_state or st.session_state["last_query_inputs"] != query_inputs:
    # 날짜가 바뀌면 쿼리 실행
    df_raw = runquery_raw(start_date, end_date)
    st.session_state["df_raw"] = df_raw
    st.session_state["last_query_inputs"] = query_inputs
else:
    df_raw = st.session_state.get("df_raw", None)

# 옵션에 따라 Python에서 가공
df_table = process_sales_data(
    df_raw,
    report_option,
    selected_item_ids,
    selected_customer_ids
)
st.dataframe(df_table, height=550)



