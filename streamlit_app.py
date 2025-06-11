# streamlit_app.py

import os
import requests
import streamlit as st
import openai
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("Please set the OPENAI_API_KEY environment variable")
    st.stop()

try:
    client = OpenAI()
except Exception as e:
    st.error(f"Failed to initialize OpenAI client: {str(e)}")
    st.stop()

# MCP and LLM settings
MCP_SERVER = "http://localhost:8000"

# Updated SYSTEM PROMPT
SYSTEM_PROMPT = """
You are a SQL expert data analyst tasked with helping users query a public health database via SQL.
You will receive:

- A list of tables, their columns, types, sample values, min/max values.
- Each table includes its "granularity" level (e.g., state-level, county-level, individual-level).
- Each column may include "units" to help label plots correctly.

Available Health Metrics:
1. PLACES health data (2022 only):
   - COPD prevalence (%)
   - Smoking prevalence (%)
   - Obesity prevalence (%)

2. WONDER mortality (2018-2023):
   - Respiratory deaths (ICD-10 codes J00-J99)
   - Population counts
   - Stratified by state, age, sex, race

3. Air Quality (2018-2023):
   - PM2.5 annual mean (µg/m³)
   - State level only

4. NHANES Survey (2022):
   - Individual responses
   - Asthma diagnosis (yes/no)
   - COPD diagnosis (yes/no)
   - Smoking status
   - Demographics

Your goals:
1. Generate a correct SQL query based ONLY on the provided schema and the user's question.
2. Do NOT make up table names or column names — only use those provided.
3. NEVER join tables of different granularity without aggregation.
4. For state names, use full names like 'California', not abbreviations.
5. Respect the year constraints of each dataset.
6. For numeric values, use appropriate filters and aggregations.

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

    # Debug: Show the prompt
    with st.expander("Debug: LLM Prompt", expanded=False):
        st.text(prompt)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for generating SQL queries."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )

    answer = response.choices[0].message.content

    # Debug: Show the raw LLM response
    with st.expander("Debug: LLM Response", expanded=False):
        st.text(answer)

    # Extract SQL from markdown block
    if "```sql" in answer:
        sql = answer.split("```sql")[1].split("```")[0].strip()
    else:
        sql = answer.strip()

    return sql

def query_mcp(sql):
    """Query the MCP server with improved error handling"""
    try:
        # Debug: Show the SQL query
        st.code(sql, language="sql")
        
        response = requests.post(f"{MCP_SERVER}/v1/query", json={"query": sql})
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            st.error(f"Server error: {data['error']}")
            return None
            
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Error querying MCP server: {str(e)}")
        return None
    except ValueError as e:
        st.error(f"Error parsing server response: {str(e)}")
        return None

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

# Initialize session state for context
if 'context' not in st.session_state:
    st.session_state.context = get_context()

# Get user question
user_question = st.text_input("Ask a question about your data:")

if user_question:
    # Generate SQL
    generated_sql = generate_sql(st.session_state.context, user_question)
    
    # Show editable SQL
    with st.expander("Modify and Re-run SQL Query", expanded=False):
        sql_query = st.text_area("SQL Query", generated_sql, height=200)
        run_button = st.button("Run Query")

    # Execute query
    result = query_mcp(sql_query)

    if result and result.get('columns') and result.get('rows'):
        df = pd.DataFrame(result['rows'], columns=result['columns'])
        st.dataframe(df)

        # Plot if possible
        if 'year' in df.columns and len(df.columns) > 1:
            x_col = 'year'
            y_cols = [col for col in df.columns if col != 'year' and col != 'state']

            # Sort the entire dataframe by year first
            df = df.sort_values(by='year')

            fig, ax = plt.subplots(figsize=(10, 6))
            
            # If we have state column, create a line for each state
            if 'state' in df.columns:
                # If query is about PM2.5 levels, only show top 5 states
                if 'pm25_annual_mean' in df.columns:
                    # Calculate average PM2.5 for each state
                    state_means = df.groupby('state')['pm25_annual_mean'].mean().sort_values(ascending=False)
                    top_states = state_means.head(5).index
                    df = df[df['state'].isin(top_states)]
                    
                for state in sorted(df['state'].unique()):
                    state_data = df[df['state'] == state].sort_values(by='year')  # Sort each state's data by year
                    ax.plot(state_data[x_col], state_data[y_cols[0]], marker='o', label=state)
                ax.legend()
            else:
                # Single state or aggregate data
                df = df.sort_values(by='year')  # Sort by year for single line plots too
                ax.plot(df[x_col], df[y_cols[0]], marker='o')

            xlabel, ylabel = get_plot_labels(st.session_state.context, sql_query)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(f"{ylabel} over {xlabel}")
            ax.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

        # LLM Commentary
        st.write("### LLM Commentary on Results:")
        commentary = generate_commentary(sql_query, df.head(5))
        st.info(commentary)
    else:
        st.error("No results returned or invalid query. Try rephrasing your question.")
