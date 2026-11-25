import pandas as pd

from config import (
    HF_RAW_DIR,
    ORA_RAW_DIR,
    PROCESSED_DATA_DIR
)


# -----------------------------------------
# FILTER HUGGING FACE RECIPES
# -----------------------------------------

def filter_hf_recipes():

    input_file = HF_RAW_DIR / "allrecipes_train.csv"

    output_dir = PROCESSED_DATA_DIR / "hf"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_file)

    target_categories = [
        "side-dish",
        "main-dish",
        "salad",
        "soups-stews-and-chili",
        "protein"
    ]

    filtered_df = df[
        df["category"]
        .astype("string")
        .str.strip()
        .str.lower()
        .isin(target_categories)
    ].copy()

    output_file = output_dir / "hf_filtered_recipes.csv"
    filtered_df.to_csv(output_file, index=False)

    print(f"HF recipes before filtering: {len(df)}")
    print(f"HF recipes after filtering: {len(filtered_df)}")
    print(f"Saved to: {output_file}")

    return filtered_df


# -----------------------------------------
# FILTER OPEN RECIPE ARCHIVE RECIPES
# -----------------------------------------

def filter_ora_recipes():

    input_file = ORA_RAW_DIR / "ora_all_collections.csv"

    output_dir = PROCESSED_DATA_DIR / "ora"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_file)

    target_cultures = [
        "india",
        "philippines",
        "turkey",
        "russian",
        "ukraine",
        "indonesia"
    ]

    filtered_df = df[
        df["culture"]
        .astype("string")
        .str.strip()
        .str.lower()
        .isin(target_cultures)
    ].copy()

    output_file = output_dir / "ora_filtered_recipes.csv"
    filtered_df.to_csv(output_file, index=False)

    print(f"ORA recipes before filtering: {len(df)}")
    print(f"ORA recipes after filtering: {len(filtered_df)}")
    print(f"Saved to: {output_file}")

    return filtered_df


# -----------------------------------------
# FILTER ALL RECIPE DATASETS
# -----------------------------------------

def filter_recipe_datasets():

    print("\nStarting recipe filtering...")

    hf_filtered = filter_hf_recipes()
    ora_filtered = filter_ora_recipes()

    print("\nRecipe filtering completed!")

    return hf_filtered, ora_filtered