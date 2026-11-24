
from src.ingestion.hf_data_load import hf_data_load
from src.ingestion.ora_data_load import ora_data_load
from src.ingestion.agos_db_data_load import agos_db_data_load
from src.filtering.data_filtering import filter_recipe_datasets
from src.standardization.agos_id_mapping import standardize_recipe_datasets
from src.standardization.ora_recipe_content import extract_ora_recipe_content
from src.cleaning.column_renaming import rename_recipe_columns

ORA_REPO_URL = "https://github.com/adambouhmad/open-recipe-archive.git"


def pipeline():

    print("\nStarting recipe data pipeline...")

    # 1. Hugging Face
    hf_data = hf_data_load(
        "arya123321/recipes",
        "allrecipes"
    )

    # 2. Open Recipe Archive
    all_ora_data = ora_data_load(ORA_REPO_URL)

    # 3. A-GOS database
    agos_data = agos_db_data_load()

    print("\nData ingestion completed!")

    # 4. Filter recipe datasets
    hf_filtered, ora_filtered = filter_recipe_datasets()

    print("\nData filtering completed!")

    #5. Standardize recipe datasets
    hf_standardized, ora_standardized = standardize_recipe_datasets()

    print("\nData standardization completed!")

    #6. Extract ORA ingredients and directions
    ora_recipes = extract_ora_recipe_content()

    print("\nORA recipe content extraction completed!")

    #7. Clean recipe column names and data types
    rename_recipe_columns()

    print("\nRecipe cleaning completed!")



if __name__ == "__main__":
    pipeline()
