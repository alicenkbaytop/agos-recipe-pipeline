
import re
import pandas as pd

from config import PROCESSED_DATA_DIR


# -----------------------------------------
# EXTRACT INGREDIENTS AND DIRECTIONS
# -----------------------------------------

def extract_recipe_sections(body):

    if pd.isna(body):
        return pd.Series({
            "ingredients": pd.NA,
            "directions": pd.NA
        })

    # Extract Ingredients section
    ingredients_match = re.search(
        r"## Ingredients\s*(.*?)(?=## Directions)",
        body,
        flags=re.DOTALL
    )

    # Extract Directions section
    directions_match = re.search(
        r"## Directions\s*(.*)",
        body,
        flags=re.DOTALL
    )

    ingredients = (
        ingredients_match.group(1).strip()
        if ingredients_match else pd.NA
    )

    directions = (
        directions_match.group(1).strip()
        if directions_match else pd.NA
    )

    return pd.Series({
        "ingredients": ingredients,
        "directions": directions
    })


# -----------------------------------------
# EXTRACT ORA RECIPE CONTENT
# -----------------------------------------

def extract_ora_recipe_content():

    print("\nStarting ORA recipe content extraction...")

    input_file = (
        PROCESSED_DATA_DIR
        / "ora"
        / "ora_standardized_recipes.csv"
    )

    output_file = (
        PROCESSED_DATA_DIR
        / "ora"
        / "ora_recipes_with_ingredients_and_directions.csv"
    )

    df = pd.read_csv(input_file)

    # Extract sections directly from the body column
    extracted_content = df["body"].apply(
        extract_recipe_sections
    )

    # Add extracted columns while preserving existing columns
    df["ingredients"] = extracted_content["ingredients"]
    df["directions"] = extracted_content["directions"]

    # Position extracted columns immediately after body
    columns = list(df.columns)

    columns.remove("ingredients")
    columns.remove("directions")

    body_index = columns.index("body") + 1

    columns[body_index:body_index] = [
        "ingredients",
        "directions"
    ]

    df = df[columns]

    # Save output
    df.to_csv(output_file, index=False)

    # Report extraction results
    missing_ingredients = df["ingredients"].isna().sum()
    missing_directions = df["directions"].isna().sum()

    print(f"Total ORA recipes: {len(df)}")
    print(f"Missing ingredients: {missing_ingredients}")
    print(f"Missing directions: {missing_directions}")
    print(f"Saved to: {output_file}")

    print("\nORA recipe content extraction completed!")

    return df
