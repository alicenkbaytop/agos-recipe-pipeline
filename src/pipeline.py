from pathlib import Path

from config import (
    AGOS_PROCESSED_DIR,
    HF_PROCESSED_DIR,
    ORA_PROCESSED_DIR,
)

from src.ingestion.hf_data_load import hf_data_load
from src.ingestion.ora_data_load import ora_data_load
from src.ingestion.agos_db_data_load import agos_db_data_load

from src.processing.title_processing import process_titles
from src.processing.cuisine_processing import process_cuisines

from src.filtering.data_filtering import filter_recipe_datasets

from src.standardization.agos_id_mapping import standardize_recipe_datasets
from src.standardization.ora_recipe_content import extract_ora_recipe_content

from src.cleaning.column_renaming import rename_recipe_columns

# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------

ORA_REPO_URL = "https://github.com/adambouhmad/open-recipe-archive.git"


# --------------------------------------------------
# PIPELINE
# --------------------------------------------------


def pipeline():

    print("\nStarting recipe data pipeline...")

    # Create output directories
    AGOS_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    HF_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ORA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # 1. DATA INGESTION
    # --------------------------------------------------

    # Hugging Face
    hf_data_load("arya123321/recipes", "allrecipes")

    # Open Recipe Archive
    ora_data_load(ORA_REPO_URL)

    # A-GOS database
    agos_db_data_load()

    # --------------------------------------------------
    # 2. FILTER DATASETS
    # --------------------------------------------------

    print("\nFiltering recipe datasets...")

    hf_filtered, ora_filtered = filter_recipe_datasets()

    # --------------------------------------------------
    # 3. STANDARDIZATION
    # --------------------------------------------------

    print("\nStandardizing recipe datasets...")

    hf_standardized, ora_standardized = standardize_recipe_datasets()

    # --------------------------------------------------
    # 4. EXTRACT ORA RECIPE CONTENT
    # --------------------------------------------------

    print("\nExtracting ORA ingredients and directions...")

    ora_recipes = extract_ora_recipe_content()

    # --------------------------------------------------
    # 5. RENAME COLUMNS
    # --------------------------------------------------

    print("\nRenaming recipe columns...")

    rename_recipe_columns()

    # --------------------------------------------------
    # 6. PROCESS HF RECIPE TITLES
    # --------------------------------------------------

    print("\nProcessing Hugging Face recipe titles...")

    process_titles(
        input_path="data/processed/hf/hf_cleaned_recipes.csv",
        output_path="data/processed/hf/hf_titled_recipes.csv",
    )

    # --------------------------------------------------
    # 7. CLASSIFY HF RECIPE CUISINES
    # --------------------------------------------------

    print("\nClassifying recipe cuisines...")

    process_cuisines(
        input_path="data/processed/hf/hf_titled_recipes.csv",
        output_path="data/processed/hf/hf_processed_recipes.csv",
    )

    print("\nPipeline completed successfully!")


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    pipeline()
