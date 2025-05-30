import streamlit as st
from utils.db import (
     fetch_domains,
     load_tables,
     fetch_inventory_items
)
from datetime import datetime,timedelta
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd

st.set_page_config(page_title="📊 Dashboard", layout="wide")


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

# 사이드바에 날짜 선택 위젯 추가
selected_date = st.sidebar.date_input(
    "Select Date", 
    min_value=datetime(2020, 1, 1), 
    max_value=datetime.today(), 
    value=datetime.today()
)

# today = datetime.today()
# one_year_ago = today - timedelta(days=700)
# # Make sure the date range is persisted across reruns using session_state
# if "start_date" not in st.session_state:
#     st.session_state.start_date = today - timedelta(days=30)  # Default value: last 30 days

# if "end_date" not in st.session_state:
#     st.session_state.end_date = today  # Default value: today

# 날짜 범위를 슬라이더로 선택
# start_date, end_date = st.sidebar.slider(
#     "Select Date Range",
#     # min_value=one_year_ago,
#     max_value=today,
#     value=(st.session_state.start_date, st.session_state.end_date),  # 기본값: 마지막 30일
#     format="YYYY-MM-DD"
# )


# --- 아이템 조회 ---
df_inventory_items = fetch_inventory_items()
item_codes = df_inventory_items['item_code'].tolist()

selected_items = st.sidebar.multiselect(
    "Select Item(s)", 
    options=item_codes,  # 선택 가능한 옵션
)
selected_item_ids=""

if selected_items:
    selected_item_ids = df_inventory_items[df_inventory_items['item_code'].isin(selected_items)]['item_id'].tolist()


# Fetch the data from SQL
df_table = load_tables(selected_date.strftime('%Y-%m-%d'), selected_date.strftime('%Y-%m-%d'), selected_item_ids)
gb = GridOptionsBuilder.from_dataframe(df_table)
gb.configure_selection("single", use_checkbox=True)

col1, col_mid, col2 = st.columns([8, 0.2, 2])
with col1:
    grid_options = gb.build()
    response = AgGrid(df_table, gridOptions=grid_options, height=700)
    selected_rows = response.get('selected_rows', [])

with col_mid:
    st.markdown(
        """
        <div style="height: 100%; border-left: 2px solid #e74c3c;"></div>
        """,
        unsafe_allow_html=True
    )

with col2:
    # Ensure selected_rows is always a list of dicts
    if isinstance(selected_rows, pd.DataFrame):
        selected_rows = selected_rows.to_dict('records')

    if selected_rows and len(selected_rows) > 0:
        selected_row = selected_rows[0]
        st.write("### Item Details")
        st.write(f"**Item Code**: {selected_row['description']}")
        st.write(f"**Price**: {selected_row['price']}")
        st.write(f"**Stock**: {selected_row['order_qty']}")
    else:
        st.write("No item selected.")






