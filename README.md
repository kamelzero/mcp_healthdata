## Install

```
curl -fsSL https://pyenv.run | bash
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"
```

```
pyenv install 3.11.8
pyenv virtualenv 3.11.8 copd_mcp-311
pyenv activate copd_mcp-311
```
python3.11 -m venv .venv
source .venv/bin/activate
```

```
uv pip install -r requirements.txt
```

# Run

```python mcp_server.py```

# Obtaining Data

1. EPA AQI
    years 2020-2024
2. NHANES
    years 2017-2018 (good quality), 2019-2020 (partial due to COVID)
3. PLACES
    year 2020 (through 2022 is available but just get 2020)
4. WONDER
    year 2020
