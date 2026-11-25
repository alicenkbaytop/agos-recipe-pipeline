import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from groq import Groq

from config import (
    PROJECT_ROOT,
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


# ==========================================================
# TITLE CLEANING
# ==========================================================


def clean_recipe_title(title):
    """
    Normalize a recipe title using Qwen through Groq.

    Returns the cleaned title while preserving the original
    title in the dataset.
    """

    if pd.isna(title) or not str(title).strip():
        return title

    title = str(title).strip()

    prompt = f"""
You are a recipe title normalization system.

Your task is to produce a concise, standardized dish name.

MANDATORY RULES:
- Remove promotional words: Simple, Easy, Best, Delicious,
  Tasty, Perfect, Ultimate, Quick.
- Remove words that only describe the quality or popularity
  of the recipe.
- Keep the main dish name.
- Keep important ingredients.
- Keep cuisine names and meaningful cooking methods.
- Do not add new information.
- Do not explain your answer.
- Return only the normalized title.

Examples:

Input: Simple Macaroni and Cheese
Output: Macaroni and Cheese

Input: Easy Homemade Chicken Soup
Output: Chicken Soup

Input: The Best Creamy Garlic Pasta
Output: Creamy Garlic Pasta

Input: Traditional Turkish Lentil Soup
Output: Traditional Turkish Lentil Soup

Input: Quick and Easy Beef Stew
Output: Beef Stew

Input: {title}
Output:
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

            if result and result.strip():

                return result.strip().strip('"').strip("'")

            print(f"Empty response for title: {title}")

            return title

        except Exception as error:

            print(f"Error cleaning title '{title}': {error}")

            if attempt < max_retries - 1:

                wait_time = 2 ** (attempt + 1)

                print(f"Retrying in {wait_time} seconds...")

                time.sleep(wait_time)

            else:

                print(f"Title cleaning failed: {title}")

                # Keep the original title if cleaning fails
                return title


# ==========================================================
# PROCESS CSV
# ==========================================================


def process_titles(
    input_path,
    output_path,
):
    """
    Read recipe CSV, normalize titles, and export the result.

    Original title is preserved.
    A new clean_title column is added.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    # Resolve relative paths from project root
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    # Check input file
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    # Read data
    df = pd.read_csv(input_path)

    if "title" not in df.columns:
        raise ValueError("CSV must contain a 'title' column.")

    df = df.copy()

    # Process recipe titles
    df["clean_title"] = df["title"].apply(clean_recipe_title)

    # Create output directory
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save output
    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nTitle processing completed!")
    print(f"Processed recipes: {len(df)}")
    print(f"Output saved to: {output_path}")

    return df


# ==========================================================
# ENTRY POINT / TEST
# ==========================================================

if __name__ == "__main__":

    process_titles(
        input_path=HF_PROCESSED_DIR / "hf_cleaned_recipes.csv",
        output_path=HF_PROCESSED_DIR / "hf_titles_processed.csv",
    )
