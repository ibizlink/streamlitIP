import streamlit as st
import os
import pyodbc
import pandas as pd

# Get credentials from secrets.toml
server = st.secrets["database"]["SQL_SERVER"] or os.environ.get("SQL_SERVER")
database = st.secrets["database"]["SQL_DB"] or os.environ.get("SQL_DB")
username = st.secrets["database"]["SQL_UID"] or os.environ.get("SQL_UID")
password = st.secrets["database"]["SQL_PWD"] or os.environ.get("SQL_PWD")

def get_hub_connection():
    return pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}')

def get_db_connection():
    return pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={st.session_state.get('target_database')};UID={username};PWD={password}")


def fetch_all_users():
    conn = get_hub_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_email, pw_hash, user_id, chk_sysadmin
        FROM ibizlink.hub_users
        WHERE pw_hash is not null
    """)
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

def fetch_domains(email=None):
    conn = get_hub_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
        HD.domain_code,
        HD.target_database
        from ibizlink.hub_streamlit_users U
        INNER JOIN ibizlink.hub_domains HD ON U.domain_id = HD.domain_id
        WHERE user_email = ?
    """, (email,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"domain_code": r[0], "target_database": r[1]} for r in rows]


# 데이터 쿼리 함수
def load_tables(start_date, end_date, selected_items):
    # If no items are selected, we skip adding the item_id condition
    if selected_items:
        # Use the IN clause to filter the items by selected item_id(s)
        # Check if the selected_items is a single item, and format it correctly
        item_ids = tuple(selected_items)  # Convert the list to a tuple for SQL IN clause
        if len(item_ids) == 1:  # If there is only one item, don't leave a trailing comma
            item_ids = f"('{item_ids[0]}')"
        else:
            item_ids = str(item_ids)  # Convert the tuple to a string for SQL

        query = f"""
        SELECT 
            description, order_qty, price, subtotal_amount
        FROM ibizlink.sales_details D WITH(NOLOCK)
        INNER JOIN ibizlink.sales_masters M WITH(NOLOCK) ON D.tran_id = M.tran_id
        WHERE M.tran_date BETWEEN '{start_date}' AND '{end_date}' AND D.item_id IN {item_ids}
        """
    else:
        # If no items are selected, only filter by date range
        query = f"""
        SELECT 
            description, order_qty, price, subtotal_amount
        FROM ibizlink.sales_details D WITH(NOLOCK)
        INNER JOIN ibizlink.sales_masters M WITH(NOLOCK) ON D.tran_id = M.tran_id
        WHERE M.tran_date BETWEEN '{start_date}' AND '{end_date}'
        """
    
    conn = get_db_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    # Display the dataframe
    return df

def fetch_inventory_items():
    conn = get_db_connection()
    query = """
    SELECT item_id, item_code
    FROM ibizlink.inventory_items
    WHERE status_id = 10 AND line_del = 0
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def fetch_customers():
    conn = get_db_connection()
    query = """
    SELECT
    card_id,
    card_code + ' : '+  card_name as card_name
    FROM ibizlink.sales_cards
    WHERE ISNULL(line_del,0) = 0 AND ISNULL(status_id,0) = 10
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df