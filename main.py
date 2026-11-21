
from config import (
    DEFAULT_TABLES,
    RAW_DATA_DIR,
    FILTERED_RECIPES_FILE,
)

from src.ingestion.load_data import (
    get_db_engine,
    extract_tables,
    extract_filtered_recipes,
)


def main():
    """
    Run the A-GOS raw data extraction workflow.

    1. Extract filtered recipes.
    2. Extract supporting reference and ingredient tables.
    """

    engine = get_db_engine()

    try:

        print("\nStarting A-GOS data extraction...")

        # Extract recipes matching the target criteria.
        recipe_count = extract_filtered_recipes(
            engine=engine,
            output_path=FILTERED_RECIPES_FILE,
        )

        # Extract supporting tables.
        table_summary = extract_tables(
            engine=engine,
            tables=DEFAULT_TABLES,
            output_dir=RAW_DATA_DIR,
        )

        total_records = sum(table_summary.values())

        print("\nExtraction completed successfully.")

        print(f"Filtered recipes: {recipe_count}")

        print(f"Supporting tables: {len(table_summary)}")

        print(f"Supporting table records: {total_records}")

        print(f"Output directory: {RAW_DATA_DIR}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
