import re
import pandas as pd

from config import ORA_PROCESSED_DIR

# ==========================================================
# EXTRACT RECIPE SECTIONS
# ==========================================================


def extract_recipe_sections(body):
    """
    Extract ingredients and directions from a Markdown recipe body.

    Sections are identified by Markdown headings.
    Content is extracted until the next heading or end of body.
    """

    if pd.isna(body) or not str(body).strip():

        return pd.Series(
            {
                "ingredients": pd.NA,
                "directions": pd.NA,
            }
        )

    body = str(body)

    # Find Markdown headings and their positions
    headings = list(
        re.finditer(
            r"(?im)^\s*#{1,6}\s*(.*?)\s*$",
            body,
        )
    )

    sections = {}

    for index, heading in enumerate(headings):

        heading_name = heading.group(1).strip().rstrip(":").lower()

        # Content starts after the heading
        content_start = heading.end()

        # Content ends at the next heading
        if index + 1 < len(headings):

            content_end = headings[index + 1].start()

        else:

            content_end = len(body)

        content = body[content_start:content_end].strip()

        sections[heading_name] = content

    # Find ingredient section
    ingredients = sections.get(
        "ingredients",
        pd.NA,
    )

    # Support common alternatives to Directions
    direction_names = [
        "directions",
        "instructions",
        "method",
        "preparation",
        "steps",
    ]

    directions = pd.NA

    for name in direction_names:

        if name in sections:

            directions = sections[name]

            break

    # Empty strings should also become missing values
    if isinstance(ingredients, str) and not ingredients.strip():
        ingredients = pd.NA

    if isinstance(directions, str) and not directions.strip():
        directions = pd.NA

    return pd.Series(
        {
            "ingredients": ingredients,
            "directions": directions,
        }
    )


# ==========================================================
# EXTRACT ORA RECIPE CONTENT
# ==========================================================


def extract_ora_recipe_content():

    print("\nStarting ORA recipe content extraction...")

    # Input file
    input_file = ORA_PROCESSED_DIR / "ora_standardized_recipes.csv"

    # Output file
    output_file = ORA_PROCESSED_DIR / "ora_recipes_with_ingredients_and_directions.csv"

    # Check input
    if not input_file.exists():

        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Read CSV
    df = pd.read_csv(input_file)

    # Validate required column
    if "body" not in df.columns:

        raise ValueError("ORA dataset must contain a 'body' column.")

    # Extract recipe sections
    extracted_content = df["body"].apply(extract_recipe_sections)

    # Add extracted content to original dataset
    df["ingredients"] = extracted_content["ingredients"]
    df["directions"] = extracted_content["directions"]

    # Position columns after body
    columns = list(df.columns)

    columns.remove("ingredients")
    columns.remove("directions")

    body_index = columns.index("body") + 1

    columns[body_index:body_index] = [
        "ingredients",
        "directions",
    ]

    df = df[columns]

    # Create output directory
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save CSV
    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    # ======================================================
    # SUMMARY
    # ======================================================

    missing_ingredients = df["ingredients"].isna().sum()
    missing_directions = df["directions"].isna().sum()

    complete_recipes = (df["ingredients"].notna() & df["directions"].notna()).sum()

    print("\nExtraction summary")
    print("------------------------------")
    print(f"Total ORA recipes: {len(df)}")
    print(f"Recipes with ingredients: {len(df) - missing_ingredients}")
    print(f"Recipes with directions: {len(df) - missing_directions}")
    print(f"Recipes with both sections: {complete_recipes}")
    print(f"Missing ingredients: {missing_ingredients}")
    print(f"Missing directions: {missing_directions}")
    print(f"Output saved to: {output_file}")

    print("\nORA recipe content extraction completed!")

    return df


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    extract_ora_recipe_content()
