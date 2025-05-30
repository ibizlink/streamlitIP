import streamlit as st
import os
import pyodbc
import pandas as pd

# Get credentials from secrets.toml
server = st.secrets["database"]["SQL_SERVER"]
database = st.secrets["database"]["SQL_DB"]
username = st.secrets["database"]["SQL_UID"]
password = st.secrets["database"]["SQL_PWD"]

def get_hub_connection():
    return pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}')

def get_db_connection():
    return pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={st.session_state.get('target_database')};UID={username};PWD={password}")

def runquery_raw(start_date, end_date):
    # 쿼리에는 날짜 조건만 반영!
    query = f"""
        SELECT
            M.master_type_id,
            M.reference_1,
            M.tran_date,
            II.item_id,
            II.item_code,
            II.item_name,
            IB.item_brand_id,
            IB.item_brand_name,
            SC.card_id,
            SC.card_code,
            SC.card_name,
            ISNULL(D.order_qty,0) as order_qty,
            ISNULL(D.subtotal_amount,0) as subtotal_amount
        FROM ibizlink.sales_details D WITH(NOLOCK)
        INNER JOIN ibizlink.sales_masters M WITH(NOLOCK) ON D.tran_id = M.tran_id
        INNER JOIN ibizlink.inventory_items II WITH(NOLOCK) ON D.item_id = II.item_id
        INNER JOIN ibizlink.sales_cards SC WITH(NOLOCK) ON M.card_id = SC.card_id
        LEFT JOIN ibizlink.core_item_brands IB WITH(NOLOCK) ON II.item_brand_id = IB.item_brand_id
        WHERE
            ISNULL(M.line_del,0) = 0 
            AND ISNULL(M.status_id,0) > 30
            AND M.tran_date BETWEEN '{start_date}' AND '{end_date}'
    """
    conn = get_db_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# 2. 옵션별 데이터 가공만 담당
def process_sales_data(df, option, selected_item_ids, selected_customer_ids):
    # 1. 고객/아이템 선택 필터링 (Python에서)
    if selected_item_ids:
        df = df[df['item_id'].isin(selected_item_ids)]
    if selected_customer_ids:
        df = df[df['card_id'].isin(selected_customer_ids)]
        
    if df.empty:
        return pd.DataFrame()
    if option == 'By Item(s)':
        df_grouped = (
            df.groupby(['item_id', 'item_code', 'item_name'], as_index=False)
            .agg({'order_qty': 'sum', 'subtotal_amount': 'sum'})
        )
        df_display = df_grouped.drop(columns=['item_id'])
        df_display = df_display.rename(columns={
            'item_code': 'Item Code',
            'item_name': 'Item Name',
            'order_qty': 'Order Qty',
            'subtotal_amount': 'Subtotal'
        })
        df_display['Order Qty'] = df_display['Order Qty'].apply(lambda x: f"{int(x):,}")
        df_display['Subtotal'] = df_display['Subtotal'].apply(lambda x: f"{int(x):,}")
        df_display = df_display.sort_values(
            by='Subtotal', ascending=False, key=lambda x: x.str.replace(',', '').astype(int)
        )
        df_display = df_display.reset_index(drop=True)
        df_display.index = df_display.index + 1
        total_qty = df_grouped['order_qty'].sum()
        total_subtotal = df_grouped['subtotal_amount'].sum()
        total_row = {
            'Item Code': 'TOTAL',
            'Item Name': '',
            'Order Qty': f"{int(total_qty):,}",
            'Subtotal': f"{int(total_subtotal):,}"
        }
        df_display = pd.concat([pd.DataFrame([total_row]), df_display], ignore_index=True)
        return df_display

    elif option == 'By Customer(s)':
        df_grouped = (
            df.groupby(['card_id', 'card_code', 'card_name'], as_index=False)
            .agg({'order_qty': 'sum', 'subtotal_amount': 'sum'})
        )
        df_display = df_grouped.drop(columns=['card_id'])
        df_display = df_display.rename(columns={
            'card_code': 'Customer Code',
            'card_name': 'Customer Name',
            'order_qty': 'Order Qty',
            'subtotal_amount': 'Subtotal'
        })
        df_display['Order Qty'] = df_display['Order Qty'].apply(lambda x: f"{int(x):,}")
        df_display['Subtotal'] = df_display['Subtotal'].apply(lambda x: f"{int(x):,}")
        df_display = df_display.sort_values(
            by='Subtotal', ascending=False, key=lambda x: x.str.replace(',', '').astype(int)
        )
        df_display = df_display.reset_index(drop=True)
        df_display.index = df_display.index + 1
        total_qty = df_grouped['order_qty'].sum()
        total_subtotal = df_grouped['subtotal_amount'].sum()
        total_row = {
            'Customer Code': 'TOTAL',
            'Customer Name': '',
            'Order Qty': f"{int(total_qty):,}",
            'Subtotal': f"{int(total_subtotal):,}"
        }
        df_display = pd.concat([pd.DataFrame([total_row]), df_display], ignore_index=True)
        return df_display

    elif option == 'By Invoice Tracking By Date':
        df_invoice = (
            df[df['master_type_id'] == 6]
            .groupby('tran_date')['reference_1']
            .nunique()
            .rename('Invoice')
        )
        df_creditnote = (
            df[df['master_type_id'] == 7]
            .groupby('tran_date')['reference_1']
            .nunique()
            .rename('Credit Note')
        )
        brand_order_df = (
            df[['item_brand_id', 'item_brand_name']]
            .drop_duplicates()
            .sort_values('item_brand_id')
        )
        brand_order_df = brand_order_df[brand_order_df['item_brand_name'].notna()]
        brand_order = brand_order_df['item_brand_name'].tolist()
        df_brand = df[df['item_brand_name'].notna()]
        df_brand_pivot = (
            df_brand.groupby(['tran_date', 'item_brand_name'])['reference_1']
            .nunique()
            .reset_index()
            .pivot(index='tran_date', columns='item_brand_name', values='reference_1')
            .fillna(0).astype(int)
        )
        result = pd.DataFrame({'tran_date': sorted(df['tran_date'].unique())})
        result = result.merge(df_invoice, left_on='tran_date', right_index=True, how='left')
        result = result.merge(df_creditnote, left_on='tran_date', right_index=True, how='left')
        result = result.merge(df_brand_pivot.reset_index(), on='tran_date', how='left')
        result = result.fillna(0)
        for col in result.columns:
            if col != 'tran_date':
                result[col] = result[col].astype(int)
        cols = ['tran_date', 'Invoice', 'Credit Note'] + brand_order
        cols = [col for col in cols if col in result.columns]
        result = result[cols]
        result = result.rename(columns={'tran_date': 'Date'})
        result = result.sort_values(by='Date', ascending=False).reset_index(drop=True)
        return result

    else:
        return df


def highlight_total_row(row):
    # Check for both possible total row columns
    if (
        ('Item Code' in row and row['Item Code'] == 'TOTAL') or
        ('Customer Code' in row and row['Customer Code'] == 'TOTAL')
    ):
        return ['font-weight: 900; font-size:20px; background-color: #d0e7ff; color: #003366'] * len(row)
    else:
        return [''] * len(row)