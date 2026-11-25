import os
import re
import time
import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# ==========================================================
# CONFIGURATION
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=api_key)

MODEL_NAME = "qwen/qwen3.8-27b"

# Fallback catalog based on the A-GOS cuisine table.
# Prefer loading the actual exported CSV in process_cuisines().

CUISINE_MAPPING = {
    "Mediterranean": 1,
    "Indian": 2,
    "Greek": 3,
    "Filipino": 4,
    "Eastern European": 5,
    "Middle Eastern": 6,
    "International": 7,
    "African": 8,
    "Myanmar (Burmese)": 9,
    "Latin American": 10,
    "Bangladeshi": 11,
    "Korean": 12,
    "Japanese": 13,
    "Indonesian": 14,
    "Chinese": 15,
    "Italian": 16,
    "French": 17,
    "Spanish": 18,
    "Georgian": 19,
    "Russian": 20,
    "Thai": 22,
    "Vietnamese": 23,
    "American": 24,
    "Peruvian": 25,
    "Lebanese": 26,
    "Moroccan": 27,
    "Latvian": 28,
    "Croatian": 29,
    "Egyptian": 30,
    "Turkish": 31,
    "Romanian": 32,
    "Polish": 33,
    "Ukrainian": 34,
}


# ==========================================================
# LOAD CUISINE CATALOG
# ==========================================================


def load_cuisine_mapping(cuisine_file=None):
    """
    Load cuisine names and IDs from the A-GOS cuisine CSV.

    If no file is provided, use the fallback mapping.
    """

    if cuisine_file is None:
        return CUISINE_MAPPING.copy()

    cuisine_file = Path(cuisine_file)

    if not cuisine_file.is_absolute():
        cuisine_file = PROJECT_ROOT / cuisine_file

    if not cuisine_file.exists():
        raise FileNotFoundError(f"Cuisine file not found: {cuisine_file}")

    cuisine_df = pd.read_csv(cuisine_file)

    required_columns = {"id", "title"}

    if not required_columns.issubset(cuisine_df.columns):
        raise ValueError("Cuisine CSV must contain 'id' and 'title' columns")

    cuisine_df = cuisine_df.dropna(subset=["id", "title"])

    if cuisine_df["title"].duplicated().any():
        duplicates = (
            cuisine_df.loc[cuisine_df["title"].duplicated(keep=False), "title"]
            .unique()
            .tolist()
        )

        raise ValueError(
            f"Duplicate cuisine names found: {duplicates}. "
            "Resolve them before processing."
        )

    return dict(zip(cuisine_df["title"].astype(str), cuisine_df["id"].astype(int)))


# ==========================================================
# CUISINE CLASSIFICATION
# ==========================================================


def classify_recipe_cuisine(row, cuisine_mapping):
    """
    Classify one recipe using Groq Qwen.

    Returns:
        tuple: (cuisine_name, cuisine_id)
    """

    title = str(row.get("title", ""))
    description = str(row.get("description", ""))
    ingredients = str(row.get("ingredients", ""))
    directions = str(row.get("directions", ""))
    url = str(row.get("url", ""))

    # Get available cuisine names
    cuisine_labels = list(cuisine_mapping.keys()) + ["Unclear"]

    prompt = f"""
    You are a professional food and cuisine classification assistant.

    Your task is to identify the most appropriate cuisine
    for the recipe.

    AVAILABLE CUISINES:
    {", ".join(cuisine_labels)}

    CLASSIFICATION RULES:

    1. Use only one label from the available cuisine list.
    2. Consider the recipe title, ingredients, cooking methods,
       and description.
    3. Consider the cultural origin and established association
       of the dish.
    4. Do not classify based only on the website URL.
    5. Choose the most specific cuisine supported by evidence.
    6. Use Eastern European if the dish is clearly Eastern
       European but its specific national origin is uncertain.
    7. Use International only when there is enough information
       to identify the recipe as broadly international.
    8. Use Unclear if there is insufficient evidence.
    9. Never invent cultural origins.
    10. Return ONLY the exact cuisine label.

    RECIPE INFORMATION:

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
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_completion_tokens=100,
            )

            result = response.choices[0].message.content

            if not result:
                return "Unclear", None

            result = result.strip()

            # Match the exact cuisine label
            matched_cuisine = next(
                (
                    label
                    for label in cuisine_labels
                    if result.lower().strip(" .\"'") == label.lower()
                ),
                None,
            )

            if matched_cuisine is None:
                print(f"Invalid cuisine response for '{title}': {result}")
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


def process_cuisines(input_path, output_path, cuisine_file=None):
    """
    Read recipe CSV, classify cuisines, add cuisine and
    cuisine_id columns, and export the processed CSV.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    # Resolve paths relative to project root
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    # Load cuisine mapping
    cuisine_mapping = load_cuisine_mapping(cuisine_file)

    print(f"Loaded {len(cuisine_mapping)} cuisines")

    # Read recipe dataset
    df = pd.read_csv(input_path)

    if "title" not in df.columns:
        raise ValueError("Input CSV must contain a 'title' column")

    df = df.copy()

    # Classify recipes
    results = []

    for index, row in df.iterrows():

        print(f"Classifying recipe {index + 1}/{len(df)}: " f"{row['title']}")

        cuisine, cuisine_id = classify_recipe_cuisine(row, cuisine_mapping)

        results.append((cuisine, cuisine_id))

    # Add result columns
    df[["cuisine", "cuisine_id"]] = pd.DataFrame(results, index=df.index)

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export processed dataset
    df.to_csv(output_path, index=False)

    print("\nCuisine classification completed!")
    print(f"Total recipes: {len(df)}")
    print(f"Output: {output_path}")

    print("\nCuisine distribution:")
    print(df["cuisine"].value_counts(dropna=False))

    return df
