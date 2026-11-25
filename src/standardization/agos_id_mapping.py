import json
import pandas as pd

from config import (
    AGOS_RAW_DIR,
    HF_PROCESSED_DIR,
    ORA_PROCESSED_DIR,
)

# ==========================================================
# LOAD A-GOS REFERENCE DATA
# ==========================================================


def load_agos_reference_data():

    cuisines_file = AGOS_RAW_DIR / "cuisines.csv"
    categories_file = AGOS_RAW_DIR / "categories.csv"

    if not cuisines_file.exists():
        raise FileNotFoundError(f"Cuisines file not found: {cuisines_file}")

    if not categories_file.exists():
        raise FileNotFoundError(f"Categories file not found: {categories_file}")

    cuisines = pd.read_csv(cuisines_file)
    categories = pd.read_csv(categories_file)

    return cuisines, categories


# ==========================================================
# BUILD CUISINE ID MAPPING
# ==========================================================


def build_cuisine_mapping(cuisines):

    mapping = {}

    for _, row in cuisines.iterrows():

        title = str(row["title"]).strip().lower()

        if title in mapping:

            print(f"Warning: Duplicate cuisine name found: {title}")

            continue

        mapping[title] = int(row["id"])

    return mapping


# ==========================================================
# BUILD CATEGORY ID MAPPING
# ==========================================================


def extract_category_title(value):
    """
    Extract a readable category title from the A-GOS
    multilingual JSON title field.
    """

    try:

        title_data = json.loads(value)

        if isinstance(title_data, dict):

            # Prefer Ukrainian, then English, then first
            # available non-empty translation.
            title = (
                title_data.get("ua")
                or title_data.get("en")
                or next((value for value in title_data.values() if value), "")
            )

        else:
            title = title_data

    except (json.JSONDecodeError, TypeError):

        title = value

    if pd.isna(title):
        return ""

    return str(title).strip()


def build_category_mapping(categories):

    mapping = {}

    for _, row in categories.iterrows():

        title = extract_category_title(row["title"])

        if not title:
            continue

        normalized_title = title.lower()

        if normalized_title in mapping:

            print(f"Warning: Duplicate category name found: " f"{normalized_title}")

            continue

        mapping[normalized_title] = int(row["id"])

    return mapping


# ==========================================================
# MAP HUGGING FACE IDS
# ==========================================================


def map_hf_ids(df):

    _, categories = load_agos_reference_data()

    category_mapping = build_category_mapping(categories)

    # Source category -> A-GOS category name
    category_names = {
        "side-dish": "sides",
        "main-dish": "main course",
        "salad": "salads",
        "soups-stews-and-chili": "soups",
        "protein": "protein",
    }

    df = df.copy()

    # HF dataset does not provide cuisine information
    df["cuisine_id"] = pd.Series(
        pd.NA,
        index=df.index,
        dtype="Int64",
    )

    # Normalize the source categories
    source_categories = df["category"].astype("string").str.strip().str.lower()

    # Convert HF category names to A-GOS category names
    agos_category_names = source_categories.map(category_names)

    # Convert A-GOS category names to A-GOS IDs
    category_ids = agos_category_names.map(category_mapping)

    df["category_id"] = category_ids.astype("Int64")

    # Report categories that could not be mapped
    unmapped = df.loc[df["category_id"].isna(), "category"].dropna().unique()

    if len(unmapped) > 0:

        print("\nUnmapped HF categories:")

        for category in unmapped:
            print(f"  - {category}")

    # Place standardized columns beside category
    columns = list(df.columns)

    columns.remove("category_id")
    columns.remove("cuisine_id")

    category_index = columns.index("category") + 1

    columns[category_index:category_index] = [
        "category_id",
        "cuisine_id",
    ]

    return df[columns]


# ==========================================================
# MAP OPEN RECIPE ARCHIVE IDS
# ==========================================================


def map_ora_ids(df):

    cuisines, _ = load_agos_reference_data()

    cuisine_mapping = build_cuisine_mapping(cuisines)

    # ORA culture -> A-GOS cuisine name
    culture_names = {
        "india": "indian",
        "indian": "indian",
        "philippines": "filipino",
        "filipino": "filipino",
        "turkey": "turkish",
        "turkish": "turkish",
        "russian": "russian",
        "ukraine": "ukrainian",
        "ukrainian": "ukrainian",
        "indonesia": "indonesian",
        "indonesian": "indonesian",
    }

    df = df.copy()

    source_cultures = df["culture"].astype("string").str.strip().str.lower()

    # Convert source culture to A-GOS cuisine name
    agos_cuisine_names = source_cultures.map(culture_names)

    # Convert A-GOS cuisine name to A-GOS ID
    cuisine_ids = agos_cuisine_names.map(cuisine_mapping)

    df["cuisine_id"] = cuisine_ids.astype("Int64")

    # ORA does not have a standardized category field yet
    df["category_id"] = pd.Series(
        pd.NA,
        index=df.index,
        dtype="Int64",
    )

    # Report cultures that could not be mapped
    unmapped = df.loc[df["cuisine_id"].isna(), "culture"].dropna().unique()

    if len(unmapped) > 0:

        print("\nUnmapped ORA cultures:")

        for culture in unmapped:
            print(f"  - {culture}")

    # Place standardized columns beside culture
    columns = list(df.columns)

    columns.remove("category_id")
    columns.remove("cuisine_id")

    culture_index = columns.index("culture") + 1

    columns[culture_index:culture_index] = [
        "category_id",
        "cuisine_id",
    ]

    return df[columns]


# ==========================================================
# STANDARDIZE RECIPE DATASETS
# ==========================================================


def standardize_recipe_datasets():

    print("\nStarting recipe standardization...")

    # ------------------------------------------------------
    # HUGGING FACE
    # ------------------------------------------------------

    hf_input = HF_PROCESSED_DIR / "hf_filtered_recipes.csv"

    hf_output = HF_PROCESSED_DIR / "hf_standardized_recipes.csv"

    if not hf_input.exists():

        raise FileNotFoundError(f"HF input file not found: {hf_input}")

    hf_df = pd.read_csv(hf_input)

    hf_standardized = map_hf_ids(hf_df)

    hf_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    hf_standardized.to_csv(
        hf_output,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"\nHF recipes standardized: {len(hf_standardized)}")
    print(f"Saved to: {hf_output}")

    # ------------------------------------------------------
    # OPEN RECIPE ARCHIVE
    # ------------------------------------------------------

    ora_input = ORA_PROCESSED_DIR / "ora_filtered_recipes.csv"

    ora_output = ORA_PROCESSED_DIR / "ora_standardized_recipes.csv"

    if not ora_input.exists():

        raise FileNotFoundError(f"ORA input file not found: {ora_input}")

    ora_df = pd.read_csv(ora_input)

    ora_standardized = map_ora_ids(ora_df)

    ora_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ora_standardized.to_csv(
        ora_output,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"\nORA recipes standardized: " f"{len(ora_standardized)}")

    print(f"Saved to: {ora_output}")

    # ------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------

    print("\nRecipe standardization completed!")

    return hf_standardized, ora_standardized
