import streamlit as st
from utils.db import (
     fetch_domains,
     load_tables,
     fetch_inventory_items,
     fetch_customers
)
from utils.salesquery import(
    process_sales_data,
    runquery_raw,
    process_trends_data
)
from datetime import datetime,timedelta
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
import altair as alt

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

df_inventory_items = fetch_inventory_items()
df_customers = fetch_customers()
item_codes = df_inventory_items['item_code'].tolist()
customer_lists = df_customers['card_name'].tolist()


# 1. 최상단: 고객/아이템 선택 (본문 상단에 고정)
st.markdown("### Filter: Customer & Item")
selected_customers = st.multiselect("Select Customer(s)", options=customer_lists)
selected_items = st.multiselect("Select Item(s)", options=item_codes)
selected_item_ids = df_inventory_items[df_inventory_items['item_code'].isin(selected_items)]['item_id'].tolist() if selected_items else []
selected_customer_ids = df_customers[df_customers['card_name'].isin(selected_customers)]['card_id'].tolist() if selected_customers else []

# 2. 탭 UI (st.tabs는 탭 index 반환 X, st.radio로 해결)
tab = st.radio("Select View", ["Summary", "Trend"], horizontal=True, label_visibility="collapsed")

# 3. 사이드바: 탭에 따라 다르게
if tab == "Summary":
    with st.sidebar:
        start_date = st.date_input(
            "Start Date", 
            min_value=datetime(2020, 1, 1), 
            max_value=datetime.today(), 
            value=datetime.today(), 
            key="sidebar_start_date"
        )
        end_date = st.date_input(
            "End Date", 
            min_value=datetime(2020, 1, 1), 
            max_value=datetime.today(), 
            value=datetime.today(), 
            key="sidebar_end_date"
        )
        report_option = st.radio(
            "Select Report Category", 
            options=["By Item(s)", "By Customer(s)", "By Invoice Tracking By Date"]
        )
elif tab == "Trend":
    with st.sidebar:
        trend_start = st.date_input(
            "Trend Start Date", 
            min_value=datetime(2020, 1, 1), 
            max_value=datetime.today(), 
            value=datetime.today() - timedelta(days=30), 
            key="trend_start"
        )
        trend_end = st.date_input(
            "Trend End Date", 
            min_value=datetime(2020, 1, 1), 
            max_value=datetime.today(), 
            value=datetime.today(), 
            key="trend_end"
        )
        trend_option = st.selectbox(
            "Trend Option", 
            options=["Sales Trend", "Order Count Trend"]
        )
        trend_group = st.radio(
            "Aggregation Level",
            options=["Daily", "Weekly", "Monthly", "Yearly"],
            horizontal=True
        )

# 4. 본문 내용도 탭에 따라 다르게
if tab == "Summary":
    st.header("Summary")
    df_raw = runquery_raw(start_date, end_date)
    df_table = process_sales_data(
        df_raw,
        report_option,
        selected_item_ids,
        selected_customer_ids
    )
    st.dataframe(
        df_table,
        height=550,
        column_config={
            "Image": st.column_config.ImageColumn("Image", help="Preview", width="small")
        }
    )
elif tab == "Trend":
    st.header("Trend")
     # 집계 단위에 따라 컬럼/쿼리 동적 생성
    group_col_map = {
        "Daily": "M.tran_date",
        "Weekly": "CONCAT(YEAR(M.tran_date), '-W', RIGHT('00' + CAST(DATEPART(WEEK, M.tran_date) AS VARCHAR(2)), 2))",
        "Monthly": "FORMAT(M.tran_date, 'yyyy-MM')",
        "Yearly": "YEAR(M.tran_date)"
    }

    group_col = group_col_map[trend_group]
    trend_df = process_trends_data(trend_start, trend_end, group_col,selected_item_ids,selected_customer_ids)

    if trend_group == "Yearly":
        trend_df["period"] = trend_df["period"].apply(lambda x: str(int(float(x))))

    # if trend_option == "Sales Trend":
    #     st.line_chart(trend_df.set_index("period")["subtotal_amount"])
    # else:
    #     st.line_chart(trend_df.set_index("period")["order_qty"])
    if trend_option == "Sales Trend":
        chart = alt.Chart(trend_df).mark_line(point=True).encode(
            x=alt.X('period:N', title='Period'),
            y=alt.Y('subtotal_amount:Q', title='Sales Amount'),
            tooltip=['period', 'subtotal_amount']
        )
    else:
        chart = alt.Chart(trend_df).mark_line(point=True).encode(
            x=alt.X('period:N', title='Period'),
            y=alt.Y('order_qty:Q', title='Order Qty'),
            tooltip=['period', 'order_qty']
        )

    st.altair_chart(chart, use_container_width=True)