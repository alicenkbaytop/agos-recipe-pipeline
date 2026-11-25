import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from groq import Groq

from config import (
    PROJECT_ROOT,
    AGOS_RAW_DIR,
    HF_PROCESSED_DIR,
)

# ==========================================================
# CONFIGURATION
# ==========================================================

load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=api_key)

MODEL_NAME = "qwen/qwen3.8-27b"

CUISINE_FILE = AGOS_RAW_DIR / "cuisines.csv"


# ==========================================================
# LOAD CUISINE CATALOG
# ==========================================================


def load_cuisine_mapping(cuisine_file=CUISINE_FILE):
    """
    Load cuisine names and IDs from the A-GOS cuisine CSV.

    Returns:
        dict: cuisine_name -> cuisine_id
    """

    cuisine_file = Path(cuisine_file)

    if not cuisine_file.is_absolute():
        cuisine_file = PROJECT_ROOT / cuisine_file

    if not cuisine_file.exists():
        raise FileNotFoundError(f"Cuisine file not found: {cuisine_file}")

    cuisine_df = pd.read_csv(cuisine_file)

    required_columns = {"id", "title"}

    if not required_columns.issubset(cuisine_df.columns):
        raise ValueError("Cuisine CSV must contain 'id' and 'title' columns.")

    cuisine_df = cuisine_df.dropna(subset=["id", "title"]).copy()

    cuisine_df["title"] = cuisine_df["title"].astype(str).str.strip()

    cuisine_df["id"] = cuisine_df["id"].astype(int)

    # Check duplicate cuisine names
    duplicates = cuisine_df[cuisine_df["title"].duplicated(keep=False)]

    if not duplicates.empty:

        print("\nDuplicate cuisine names detected:")

        print(duplicates[["id", "title"]].sort_values("title"))

        raise ValueError(
            "Duplicate cuisine names exist in the A-GOS catalog. "
            "Resolve them before classification."
        )

    cuisine_mapping = dict(
        zip(
            cuisine_df["title"],
            cuisine_df["id"],
        )
    )

    return cuisine_mapping


# ==========================================================
# CUISINE CLASSIFICATION
# ==========================================================


def classify_recipe_cuisine(row, cuisine_mapping):
    """
    Classify one recipe using Groq.

    Returns:
        tuple: (cuisine_name, cuisine_id)
    """

    title = str(row.get("clean_title", row.get("title", "")))
    description = str(row.get("description", ""))
    ingredients = str(row.get("ingredients", ""))
    directions = str(row.get("steps", row.get("directions", "")))
    url = str(row.get("url", ""))

    cuisine_labels = list(cuisine_mapping.keys()) + ["Unclear"]

    prompt = f"""
You are a professional food and cuisine classification assistant.

Classify the recipe into the most appropriate cuisine.

AVAILABLE CUISINES:
{", ".join(cuisine_labels)}

RULES:
1. Return exactly one cuisine from the available list.
2. Consider the recipe title, ingredients, cooking methods,
   and description.
3. Use the dish's cultural origin and established association.
4. Do not classify based only on the website URL.
5. Choose the most specific cuisine supported by evidence.
6. Use Eastern European if the dish is clearly Eastern European
   but its specific national origin is uncertain.
7. Use International only when the recipe is broadly international.
8. Use Unclear if there is insufficient evidence.
9. Never invent cultural origins.
10. Return ONLY the exact cuisine label.

RECIPE:

Title: {title}
URL: {url[:500]}
Description: {description[:1500]}
Ingredients: {ingredients[:2500]}
Directions: {directions[:1500]}

Cuisine:
"""

    max_retries = 3

    for attempt in range(max_retries):

        try:

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0,
                max_completion_tokens=100,
            )

            result = response.choices[0].message.content

            if not result:
                return "Unclear", None

            result = result.strip().strip('"').strip("'").strip(".")

            matched_cuisine = next(
                (label for label in cuisine_labels if result.lower() == label.lower()),
                None,
            )

            if matched_cuisine is None:

                print(f"Invalid cuisine response for '{title}': " f"{result}")

                return "Unclear", None

            if matched_cuisine == "Unclear":
                return "Unclear", None

            cuisine_id = cuisine_mapping[matched_cuisine]

            return matched_cuisine, cuisine_id

        except Exception as error:

            print(f"Error classifying '{title}': {error}")

            if attempt < max_retries - 1:

                wait_time = 2 ** (attempt + 1)

                print(f"Retrying in {wait_time} seconds...")

                time.sleep(wait_time)

            else:

                print(f"Classification failed: {title}")

                return "Unclear", None


# ==========================================================
# PROCESS CSV
# ==========================================================


def process_cuisines(
    input_path,
    output_path,
    cuisine_file=CUISINE_FILE,
):
    """
    Read recipes, classify cuisine, add cuisine and cuisine_id,
    and export the processed dataset.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)
    cuisine_file = Path(cuisine_file)

    # Resolve relative paths from project root
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    if not cuisine_file.is_absolute():
        cuisine_file = PROJECT_ROOT / cuisine_file

    # Validate input file
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    # Load A-GOS cuisine catalog
    cuisine_mapping = load_cuisine_mapping(cuisine_file)

    print(f"Loaded {len(cuisine_mapping)} cuisines")

    # Read dataset
    df = pd.read_csv(input_path)

    if "title" not in df.columns and "clean_title" not in df.columns:
        raise ValueError("Input CSV must contain 'title' or 'clean_title'.")

    df = df.copy()

    # Classify recipes
    results = []

    for index, row in df.iterrows():

        recipe_title = row.get(
            "clean_title",
            row.get("title", ""),
        )

        print(f"Classifying recipe {index + 1}/{len(df)}: " f"{recipe_title}")

        cuisine, cuisine_id = classify_recipe_cuisine(
            row,
            cuisine_mapping,
        )

        results.append((cuisine, cuisine_id))

    # Add output columns
    df[["cuisine", "cuisine_id"]] = pd.DataFrame(
        results,
        index=df.index,
    )

    df["cuisine_id"] = df["cuisine_id"].astype("Int64")

    # Create output directory
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Export
    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nCuisine classification completed!")
    print(f"Total recipes: {len(df)}")
    print(f"Output: {output_path}")

    print("\nCuisine distribution:")
    print(df["cuisine"].value_counts(dropna=False))

    return df


# ==========================================================
# ENTRY POINT / TEST
# ==========================================================

if __name__ == "__main__":

    process_cuisines(
        input_path=HF_PROCESSED_DIR / "hf_titles_processed.csv",
        output_path=HF_PROCESSED_DIR / "hf_cuisine_processed.csv",
    )
