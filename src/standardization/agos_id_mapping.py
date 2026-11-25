
import json
import pandas as pd

from config import AGOS_RAW_DIR, PROCESSED_DATA_DIR


# -----------------------------------------
# LOAD A-GOS REFERENCE DATA
# -----------------------------------------

def load_agos_reference_data():

    cuisines = pd.read_csv(AGOS_RAW_DIR / "cuisines.csv")
    categories = pd.read_csv(AGOS_RAW_DIR / "categories.csv")

    return cuisines, categories


# -----------------------------------------
# BUILD CUISINE ID MAPPING
# -----------------------------------------

def build_cuisine_mapping(cuisines):

    return {
        str(row["title"]).strip().lower(): row["id"]
        for _, row in cuisines.iterrows()
    }


# -----------------------------------------
# BUILD CATEGORY ID MAPPING
# -----------------------------------------

def build_category_mapping(categories):

    mapping = {}

    for _, row in categories.iterrows():

        try:
            title = json.loads(row["title"]).get("ua", "")

        except (json.JSONDecodeError, TypeError):
            title = row["title"]

        if title:
            mapping[str(title).strip().lower()] = row["id"]

    return mapping


# -----------------------------------------
# MAP HUGGING FACE IDS
# -----------------------------------------

def map_hf_ids(df):

    cuisines, categories = load_agos_reference_data()
    category_mapping = build_category_mapping(categories)

    category_names = {
        "side-dish": "sides",
        "main-dish": "main course",
        "salad": "salads",
        "soups-stews-and-chili": "soups",
        "protein": "protein",
    }

    df = df.copy()

    # Hugging Face does not provide cuisine information
    df["cuisine_id"] = pd.Series(
        pd.NA,
        index=df.index,
        dtype="Int64"
    )

    # Map source categories to A-GOS category IDs
    category_ids = (
        df["category"]
        .astype("string")
        .str.strip()
        .str.lower()
        .map(category_names)
        .map(category_mapping)
    )

    df["category_id"] = category_ids.astype("Int64")

    # Arrange new columns beside the original category column
    columns = list(df.columns)

    columns.remove("category_id")
    columns.remove("cuisine_id")

    category_index = columns.index("category") + 1

    columns[category_index:category_index] = [
        "category_id",
        "cuisine_id"
    ]

    return df[columns]


# -----------------------------------------
# MAP OPEN RECIPE ARCHIVE IDS
# -----------------------------------------

def map_ora_ids(df):

    cuisines, categories = load_agos_reference_data()
    cuisine_mapping = build_cuisine_mapping(cuisines)

    culture_names = {
        "india": "indian",
        "philippines": "filipino",
        "turkey": "turkish",
        "russian": "russian",
        "ukraine": "ukrainian",
        "indonesia": "indonesian",
    }

    df = df.copy()

    # Map source cultures to A-GOS cuisine IDs
    cuisine_ids = (
        df["culture"]
        .astype("string")
        .str.strip()
        .str.lower()
        .map(culture_names)
        .map(cuisine_mapping)
    )

    df["cuisine_id"] = cuisine_ids.astype("Int64")

    # ORA has no dedicated category field at this stage
    df["category_id"] = pd.Series(
        pd.NA,
        index=df.index,
        dtype="Int64"
    )

    # Arrange new columns beside the original culture column
    columns = list(df.columns)

    columns.remove("category_id")
    columns.remove("cuisine_id")

    culture_index = columns.index("culture") + 1

    columns[culture_index:culture_index] = [
        "category_id",
        "cuisine_id"
    ]

    return df[columns]


# -----------------------------------------
# STANDARDIZE RECIPE DATASETS
# -----------------------------------------

def standardize_recipe_datasets():

    print("\nStarting recipe standardization...")

    # Hugging Face
    hf_input = (
        PROCESSED_DATA_DIR / "hf" / "hf_filtered_recipes.csv"
    )

    hf_output = (
        PROCESSED_DATA_DIR / "hf" / "hf_standardized_recipes.csv"
    )

    hf_df = pd.read_csv(hf_input)

    hf_standardized = map_hf_ids(hf_df)

    hf_standardized.to_csv(hf_output, index=False)

    print(f"HF recipes standardized: {len(hf_standardized)}")
    print(f"Saved to: {hf_output}")

    # Open Recipe Archive
    ora_input = (
        PROCESSED_DATA_DIR / "ora" / "ora_filtered_recipes.csv"
    )

    ora_output = (
        PROCESSED_DATA_DIR / "ora" / "ora_standardized_recipes.csv"
    )

    ora_df = pd.read_csv(ora_input)

    ora_standardized = map_ora_ids(ora_df)

    ora_standardized.to_csv(ora_output, index=False)

    print(f"ORA recipes standardized: {len(ora_standardized)}")
    print(f"Saved to: {ora_output}")

    print("\nRecipe standardization completed!")

    return hf_standardized, ora_standardized
