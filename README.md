# Public Health Data Explorer

An interactive data exploration tool that combines public health datasets to analyze relationships between air quality, respiratory health, and mortality rates across the United States.

## Overview

This application integrates multiple public health datasets and provides an LLM-powered interface for exploring correlations between environmental factors and health outcomes. The data flows through the following process:

```
User Question → LLM Analysis → SQL Query → Database Server → Data Results → Visual Dashboard
```

## Data Sources

The application combines four major public health datasets:

1. **EPA Air Quality Data** (2010-2024)
   - PM2.5 annual mean measurements
   - State-level air quality indicators

2. **NHANES Survey Data** (2021-2023)
   - Individual health responses
   - Respiratory health indicators
   - Demographic information

3. **CDC PLACES Data** (2022)
   - County-level health statistics
   - COPD prevalence
   - Smoking rates
   - Obesity rates

4. **CDC WONDER Mortality Data** (2018-2023)
   - Respiratory disease mortality (ICD-10: J00-J99)
   - State-level mortality statistics
   - Demographic stratification

## Installation

### Prerequisites
- Python 3.11.8
- SQLite3

### Setup Environment

1. Install and configure pyenv:
```bash
curl -fsSL https://pyenv.run | bash
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"
```

2. Create and activate Python environment:
```bash
pyenv install 3.11.8
pyenv virtualenv 3.11.8 copd_mcp-311
pyenv activate copd_mcp-311
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

### Database Setup

Initialize and populate the database:
```bash
python create_db.py
python create_tables.py
python load_data.py
```

## Running the Application

1. Start the MCP server:
```bash
bash run_mcp_server.sh
```

2. In a separate terminal, launch the Streamlit interface:
```bash
streamlit run streamlit_app.py
```

The application will be available at `http://localhost:8501`

## Example Queries

The application supports various types of health data analysis. Here are some example queries:

### Air Quality Analysis
- Compare PM2.5 levels between California and New York from 2018 to 2022
- Show PM2.5 annual mean trends in California from 2018 to 2023
- Show the annual trend of PM2.5 levels in states with the highest air pollution

### Health Statistics
- Show the top 10 states with highest respiratory mortality in 2022
- Compare COPD prevalence across all counties in 2022

## Features

- **Interactive Query Interface**: Natural language to SQL conversion
- **Dynamic Visualizations**: Automatic chart generation based on query results
- **Data Analysis**: AI-powered commentary on query results
- **Flexible Query Options**: Both preset questions and custom queries supported

## License

This project is licensed under the MIT License - see the LICENSE file for details.

