# streamlit_app.py

import os
import streamlit as st
import requests
import openai  # or you can swap this for Anthropic, Gemini

# MCP and LLM settings
MCP_SERVER = "http://localhost:8000"
openai.api_key = os.getenv("OPENAI_API_KEY")  # load from secrets

# New way: Create a client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompt template to help the LLM generate good SQL
SYSTEM_PROMPT = """
You are a data analyst. Given the database schema and a user question, you must write a correct SQL query.
Only use the tables and columns available.
Don't make up table names or column names.
Respond with only the SQL query inside a markdown SQL block.
"""

# Helper: Ask MCP Server for context
def get_context():
    response = requests.post(f"{MCP_SERVER}/v1/context")
    return response.json()

def generate_sql(context, user_question):
    schema_text = ""
    for table in context['tables']:
        schema_text += f"Table {table['name']}:\n"
        for column in table['columns']:
            schema_text += f"  - {column['name']}\n"

    prompt = f"{SYSTEM_PROMPT}\n\nDatabase Schema:\n{schema_text}\n\nQuestion:\n{user_question}\n\nSQL:"

    # New way: call chat.completions.create()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for generating SQL queries."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )

    answer = response.choices[0].message.content

    # Extract SQL from markdown block
    if "```sql" in answer:
        sql = answer.split("```sql")[1].split("```")[0].strip()
    else:
        sql = answer.strip()

    return sql

# Helper: Query MCP Server
def query_mcp(sql):
    response = requests.post(f"{MCP_SERVER}/v1/query", json={"query": sql})
    return response.json()

# Streamlit UI
st.title("MCP + LLM SQL Explorer")

user_question = st.text_input("Ask a question about your data:")

if user_question:
    st.write("Generating SQL from your question...")
    context = get_context()
    sql_query = generate_sql(context, user_question)

    st.code(sql_query, language="sql")

    st.write("Running query...")
    result = query_mcp(sql_query)

    df = None
    if result.get('columns') and result.get('rows'):
        import pandas as pd
        df = pd.DataFrame(result['rows'], columns=result['columns'])
        st.dataframe(df)
    else:
        st.error("No results returned.")

    # Optional: Plot if the query returns year-like data
    if df is not None and 'year' in df.columns:
        st.line_chart(df.set_index('year'))

