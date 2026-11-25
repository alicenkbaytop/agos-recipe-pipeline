import json
import subprocess
import pandas as pd

from config import ORA_RAW_DIR, ORA_REPO_DIR

# ==========================================================
# DOWNLOAD OR CHECK REPOSITORY
# ==========================================================


def download_repository(repo_url, repo_dir):
    """
    Clone the ORA repository if it does not already exist.

    If already cloned, use the existing local repository.
    """

    if not repo_dir.exists():

        repo_dir.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        print("Cloning Open Recipe Archive repository...")

        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                repo_url,
                str(repo_dir),
            ],
            check=True,
        )

        print("Repository cloned successfully.")

    else:

        print(f"Using existing local repository: {repo_dir}")

    # Validate the repository directory
    collections_dir = repo_dir / "collections"

    if not collections_dir.exists():

        raise FileNotFoundError(f"Collections directory not found: {collections_dir}")

    return collections_dir


# ==========================================================
# LOAD ORA DATA
# ==========================================================


def ora_data_load(
    repo_url,
    collection=None,
):
    """
    Load recipes from Open Recipe Archive JSONL files.

    Args:
        repo_url: GitHub repository URL.
        collection: Optional collection name.
                    None means load all collections.

    Returns:
        pandas DataFrame containing loaded recipes.
    """

    print("\nStarting ORA ingestion...")

    # ------------------------------------------------------
    # 1. DOWNLOAD / LOCATE REPOSITORY
    # ------------------------------------------------------

    collections_dir = download_repository(
        repo_url=repo_url,
        repo_dir=ORA_REPO_DIR,
    )

    # ------------------------------------------------------
    # 2. SELECT COLLECTIONS
    # ------------------------------------------------------

    if collection is None:

        selected_collections = sorted(
            [folder for folder in collections_dir.iterdir() if folder.is_dir()]
        )

    else:

        selected_path = collections_dir / collection

        if not selected_path.is_dir():

            raise ValueError(f"Collection not found: {collection}")

        selected_collections = [selected_path]

    if not selected_collections:

        raise ValueError("No collections were found.")

    # ------------------------------------------------------
    # 3. READ JSONL FILES
    # ------------------------------------------------------

    recipes = []

    for collection_dir in selected_collections:

        jsonl_path = collection_dir / "recipes.jsonl"

        if not jsonl_path.exists():

            print(f"Skipping {collection_dir.name}: " "recipes.jsonl not found")

            continue

        print(f"Loading collection: " f"{collection_dir.name}")

        loaded_count = 0

        with jsonl_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line_number, line in enumerate(
                file,
                start=1,
            ):

                if not line.strip():
                    continue

                try:

                    recipe = json.loads(line)

                    # Track which collection the recipe came from
                    recipe["source_collection"] = collection_dir.name

                    recipes.append(recipe)

                    loaded_count += 1

                except json.JSONDecodeError as error:

                    print(
                        f"Invalid JSON in "
                        f"{collection_dir.name}, "
                        f"line {line_number}: {error}"
                    )

        print(f"Loaded {loaded_count} recipes " f"from {collection_dir.name}")

    # ------------------------------------------------------
    # 4. VALIDATE DATA
    # ------------------------------------------------------

    if not recipes:

        raise ValueError("No recipes were loaded from the selected collections.")

    df = pd.DataFrame(recipes)

    # ------------------------------------------------------
    # 5. SAVE CSV
    # ------------------------------------------------------

    OUTPUT_DIR = ORA_RAW_DIR

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_name = collection if collection is not None else "all_collections"

    output_path = OUTPUT_DIR / f"ora_{output_name}.csv"

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    # ------------------------------------------------------
    # 6. SUMMARY
    # ------------------------------------------------------

    print("\nORA ingestion completed!")
    print(f"Total recipes loaded: {len(df)}")
    print(f"Collections processed: {len(selected_collections)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Output saved to: {output_path}")

    return df


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    ora_data_load(
        repo_url="https://github.com/adambouhmad/open-recipe-archive.git",
    )
