import sqlite3
import pandas as pd

DB_PATH = "data/northwind.sqlite"

def get_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' OR type='view';")
    tables = cursor.fetchall()
    schema = {}
    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        schema[table_name] = [row[1] for row in cursor.fetchall()]
    conn.close()
    return schema

def execute_sql(sql: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return {"success": True, "data": df, "error": None}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}