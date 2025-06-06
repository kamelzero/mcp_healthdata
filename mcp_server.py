# mcp_server.py
from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import uvicorn
import json

app = FastAPI()

# Load context.json
with open("context.json", "r") as f:
    context = json.load(f)

# Define query request model
class QueryRequest(BaseModel):
    query: str

# Endpoint for MCP /v1/context
@app.post("/v1/context")
async def get_context():
    return context

# Endpoint for MCP /v1/query
@app.post("/v1/query")
async def run_query(request: QueryRequest):
    conn = sqlite3.connect("copd_public_health.db")
    cursor = conn.cursor()
    try:
        cursor.execute(request.query)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        result = [dict(zip(columns, row)) for row in rows]
        return {"rows": result}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

# Start server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
