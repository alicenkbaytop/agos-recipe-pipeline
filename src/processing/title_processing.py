import os
import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

# Initialize Groq client
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=api_key)

MODEL_NAME = "qwen/qwen3.8-27b"


def clean_recipe_title(title):
    """
    Clean a recipe title using Qwen through Groq.
    """

    if pd.isna(title) or not str(title).strip():
        return title

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

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_completion_tokens=100,
    )

    return response.choices[0].message.content.strip()


def process_titles(input_path, output_path):
    """
    Read CSV, clean recipe titles and export processed CSV.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path

    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    df = pd.read_csv(input_path)

    if "title" not in df.columns:
        raise ValueError("CSV must contain a title column")

    df = df.copy()

    df["clean_title"] = df["title"].apply(clean_recipe_title)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    print(f"Processed {len(df)} recipes")
    print(f"Output saved to: {output_path}")

    return df
