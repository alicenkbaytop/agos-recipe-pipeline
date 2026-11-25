
import pandas as pd

from config import PROCESSED_DATA_DIR


def rename_recipe_columns():

    print("\nStarting recipe column renaming...")

    datasets = {
        "hf": (
            "hf_standardized_recipes.csv",
            "hf_cleaned_recipes.csv"
        ),
        "ora": (
            "ora_recipes_with_ingredients_and_directions.csv",
            "ora_cleaned_recipes.csv"
        )
    }

    for source, (input_name, output_name) in datasets.items():

        input_file = PROCESSED_DATA_DIR / source / input_name
        output_file = PROCESSED_DATA_DIR / source / output_name

        df = pd.read_csv(input_file)

        # Preserve ID columns as nullable integers
        for column in ["category_id", "cuisine_id"]:
            if column in df.columns:
                df[column] = df[column].astype("Int64")

        # Rename directions to steps
        df.rename(
            columns={"directions": "steps"},
            inplace=True
        )

        df.to_csv(output_file, index=False)

        print(f"{source.upper()} columns renamed successfully.")
        print(f"Saved to: {output_file}")

    print("\nRecipe column renaming completed!")
