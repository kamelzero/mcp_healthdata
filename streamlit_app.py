# streamlit_app.py

import os
import requests
import streamlit as st
import openai
import pandas as pd
import matplotlib.pyplot as plt

# MCP and LLM settings
MCP_SERVER = "http://localhost:8000"
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Updated SYSTEM PROMPT
SYSTEM_PROMPT = """
You are a SQL expert data analyst tasked with helping users query a public health database via SQL.
You will receive:

- A list of tables, their columns, types, sample values, min/max values.
- Each table includes its "granularity" level (e.g., state-level, county-level, individual-level).
- Each column may include "units" to help label plots correctly.

Your goals:
1. Generate a correct SQL query based ONLY on the provided schema and the user's question.
2. Do NOT make up table names or column names — only use those provided.
3. NEVER join tables of different granularity without aggregation.
4. Use sample values to match correctly. Note: For `state`, use *full state names* like 'California', 'Texas', 'New York', not abbreviations like 'CA', 'TX'.
5. Ensure that if year is used, it's between provided min/max years.
6. For numeric values like pm2.5 or prevalence, use appropriate filters and aggregations.
7. When plotting:
   - Label x-axis and y-axis based on the column names and units.
   - If no units are provided, use sensible default labels.

Respond ONLY with a SQL query inside a Markdown SQL block like:
```sql
SELECT ... FROM ...;
```
Do not explain anything outside the SQL block.
"""

# Commentary Prompt
COMMENTARY_PROMPT_TEMPLATE = """
You are a data analysis expert.

Given the SQL query:
```sql
{sql}
```

And this sample of the results:
{sample}

Briefly (2–3 sentences), comment on:
- Whether the results seem reasonable or not.
- Mention any notable trends, anomalies, or known external factors (e.g., policy changes, COVID).
"""

def get_context():
    response = requests.post(f"{MCP_SERVER}/v1/context")
    return response.json()

def generate_sql(context, user_question):
    schema_text = ""
    for table in context['tables']:
        schema_text += f"Table {table['name']} (granularity: {table.get('granularity', 'unknown')}):\n"
        for column in table['columns']:
            units = f" ({column.get('units')})" if column.get('units') else ""
            schema_text += f"  - {column['name']} [{column['type']}] {units}\n"
            if column.get('sample_values'):
                schema_text += f"    e.g., {column['sample_values']}\n"
            if 'min' in column and 'max' in column:
                schema_text += f"    range: {column['min']} - {column['max']}\n"

    prompt = f"{SYSTEM_PROMPT}\n\nDatabase Schema:\n{schema_text}\n\nQuestion:\n{user_question}\n\nSQL:"

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

def query_mcp(sql):
    response = requests.post(f"{MCP_SERVER}/v1/query", json={"query": sql})
    return response.json()

def get_plot_labels(context, sql_query):
    """ Try to guess labels based on selected columns """
    x_label, y_label = "X", "Y"

    for table in context['tables']:
        for col in table['columns']:
            if col['name'] in sql_query:
                if 'year' in col['name'].lower():
                    x_label = f"{col['name']} ({col.get('units', '')})"
                if 'pm25' in col['name'].lower() or 'prevalence' in col['name'].lower() or 'deaths' in col['name'].lower():
                    y_label = f"{col['name']} ({col.get('units', '')})"

    return x_label.strip(), y_label.strip()

def generate_commentary(sql_query, df_sample):
    sample_text = df_sample.to_markdown(index=False)
    prompt = COMMENTARY_PROMPT_TEMPLATE.format(sql=sql_query, sample=sample_text)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for commenting on SQL results."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

# Streamlit UI
st.title("MCP + LLM SQL Explorer")

# State variables
if 'user_sql' not in st.session_state:
    st.session_state.user_sql = None
if 'context' not in st.session_state:
    st.session_state.context = None

user_question = st.text_input("Ask a question about your data:")

if user_question and st.session_state.user_sql is None:
    st.write("Generating SQL...")
    context = get_context()
    st.session_state.context = context  # 💾 Save context
    generated_sql = generate_sql(context, user_question)
    st.session_state.user_sql = generated_sql

# Editable SQL Section
if st.session_state.user_sql:
    with st.expander("Modify and Re-run SQL Query", expanded=False):
        edited_sql = st.text_area("SQL Query", st.session_state.user_sql, height=200)
        if st.button("Run Query"):
            st.session_state.user_sql = edited_sql

# Run the Query
if st.session_state.user_sql:
    sql_query = st.session_state.user_sql
    result = query_mcp(sql_query)

    if result.get('columns') and result.get('rows'):
        df = pd.DataFrame(result['rows'], columns=result['columns'])
        st.dataframe(df)

        # Plot if possible
        if 'year' in df.columns and len(df.columns) > 1:
            x_col = 'year'
            y_col = [col for col in df.columns if col != 'year'][0]

            fig, ax = plt.subplots()
            ax.plot(df[x_col], df[y_col], marker='o')
            xlabel, ylabel = get_plot_labels(st.session_state.context, sql_query)  # use session state context
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(f"{ylabel} over {xlabel}")
            ax.grid(True)
            st.pyplot(fig)

        # LLM Commentary
        st.write("### LLM Commentary on Results:")
        commentary = generate_commentary(sql_query, df.head(5))
        st.info(commentary)
    else:
        st.error("No results returned.")
