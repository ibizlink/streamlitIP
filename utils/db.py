import os
import pyodbc

def get_hub_connection():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('SQL_SERVER', 'tcp:ibizlinkaus.database.windows.net,1433')};"
        f"DATABASE={os.getenv('SQL_DB', 'ibizlink_hub')};"
        f"UID={os.getenv('SQL_UID', 'ibizlinkg')};"
        f"PWD={os.getenv('SQL_PWD', 'ibzHello2019Friends=')};"
    )

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