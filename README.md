# AGOS Pipeline

* Run on project root!
1. .venv\Scripts\Activate
2. Uv sync
3. Uv run python -m src.pipeline


## Project Structure

agos-recipe-pipeline/
├── config.py
├── data/
│   ├── raw/
│   │   ├── agos/
│   │   ├── hf/
│   │   └── ora/
│   └── processed/
│       ├── agos/
│       ├── hf/
│       └── ora/
└── src/
    ├── pipeline.py
    ├── ingestion/
    ├── filtering/
    ├── standardization/
    ├── cleaning/
    └── processing/