from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

# CORS (important for Streamlit, Cursor, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = 'copd_public_health.db'

def get_column_metadata(cursor, table_name):
    """Get metadata: name, type, sample values or min/max for each column."""
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns_info = cursor.fetchall()  # [cid, name, type, notnull, dflt_value, pk]

    columns_metadata = []

    for col in columns_info:
        col_name = col[1]
        col_type = col[2].upper()

        col_meta = {
            "name": col_name,
            "type": col_type,
        }

        # Try to add sample values or min/max
        if "CHAR" in col_type or "TEXT" in col_type:
            # Sample 3 distinct values for TEXT columns
            cursor.execute(f"""
                SELECT DISTINCT {col_name} 
                FROM {table_name} 
                WHERE {col_name} IS NOT NULL 
                LIMIT 3;
            """)
            samples = [row[0] for row in cursor.fetchall()]
            if samples:
                col_meta["sample_values"] = samples
        elif "INT" in col_type or "REAL" in col_type or "NUM" in col_type:
            # Min/Max for numeric columns
            cursor.execute(f"""
                SELECT MIN({col_name}), MAX({col_name}) 
                FROM {table_name};
            """)
            min_max = cursor.fetchone()
            if min_max and (min_max[0] is not None and min_max[1] is not None):
                col_meta["min"] = min_max[0]
                col_meta["max"] = min_max[1]

        columns_metadata.append(col_meta)

    return columns_metadata

@app.post("/v1/context")
async def context():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Build context response
    context = {"tables": []}

    for (table_name,) in tables:
        columns = get_column_metadata(cursor, table_name)

        table_meta = {
            "name": table_name,
            "description": f"Table {table_name} in the COPD public health database.",
            "columns": columns
        }

        context["tables"].append(table_meta)

    conn.close()
    return context

@app.post("/v1/query")
async def query(body: dict):
    query_text = body.get("query")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(query_text)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]

    conn.close()

    return {
        "columns": columns,
        "rows": rows
    }
