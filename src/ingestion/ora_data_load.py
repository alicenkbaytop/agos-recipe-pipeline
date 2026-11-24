import json
import subprocess
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPO_DIR = PROJECT_ROOT / "data" / "raw" / "open_recipe_archive_repo"
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"


def download_repository(repo_url, repo_dir):

    if not repo_dir.exists():

        repo_dir.parent.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(repo_dir)], check=True
        )


def ora_data_load(repo_url, collection=None):

    download_repository(repo_url, REPO_DIR)

    collections_dir = REPO_DIR / "collections"

    # Select collections
    if collection is None:
        selected_collections = [
            folder for folder in collections_dir.iterdir() if folder.is_dir()
        ]

    else:
        selected_path = collections_dir / collection

        if not selected_path.is_dir():
            raise ValueError(f"Collection not found: {collection}")

        selected_collections = [selected_path]

    recipes = []

    # Read recipes from selected collections
    for collection_dir in selected_collections:

        jsonl_path = collection_dir / "recipes.jsonl"

        if not jsonl_path.exists():
            print(f"Skipping: {collection_dir.name}")
            continue

        print(f"Loading collection: {collection_dir.name}")

        with jsonl_path.open("r", encoding="utf-8") as file:

            for line_number, line in enumerate(file, start=1):

                if not line.strip():
                    continue

                try:
                    recipe = json.loads(line)
                    recipes.append(recipe)

                except json.JSONDecodeError:
                    print(f"Invalid JSON at line {line_number}")

    if not recipes:
        raise ValueError("No recipes were loaded.")

    df = pd.DataFrame(recipes)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create a different CSV for each selection
    output_name = collection if collection else "all_collections"

    output_path = OUTPUT_DIR / f"ora_{output_name}.csv"

    df.to_csv(output_path, index=False)

    print(f"Loaded {len(df)} recipes.")
    print(f"Saved to: {output_path}")

    return df


if __name__ == "__main__":
    ora_data_load() # Link
