import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import bindparam, create_engine, inspect, text
from sqlalchemy.engine import URL

from config import (
    BASE_DIR,
    FILTERED_RECIPES_FILE,
    FILTERED_RECIPES_SQL,
    TARGET_CUISINES,
    CATEGORY_PATTERNS,
    DEFAULT_TABLES,
    AGOS_RAW_DIR,
)


def get_db_engine():
    """Create a SQLAlchemy engine using environment variables."""

    load_dotenv(BASE_DIR / ".env")

    required_variables = [
        "DB_HOST",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing_variables = [
        variable for variable in required_variables if not os.getenv(variable)
    ]

    if missing_variables:
        raise EnvironmentError(
            f"Missing database environment variables: "
            f"{', '.join(missing_variables)}"
        )

    try:
        port = int(os.getenv("DB_PORT", "3306"))
    except ValueError as exc:
        raise ValueError("DB_PORT must be a valid integer.") from exc

    database_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=port,
        database=os.getenv("DB_NAME"),
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


def save_dataframe(dataframe: pd.DataFrame, output_path: Path):
    """Save a DataFrame as CSV."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")

    try:
        dataframe.to_csv(
            temporary_path,
            index=False,
            encoding="utf-8-sig",
        )

        temporary_path.replace(output_path)

    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def extract_tables(
    engine,
    tables: tuple[str, ...],
    output_dir: Path,
) -> dict[str, int]:
    """Extract selected database tables into individual CSV files."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tables = tuple(dict.fromkeys(tables))

    available_tables = set(inspect(engine).get_table_names())

    missing_tables = set(tables) - available_tables

    if missing_tables:
        raise ValueError(
            "The following requested tables do not exist: " f"{sorted(missing_tables)}"
        )

    extraction_summary = {}

    with engine.connect() as connection:

        for table in tables:

            dataframe = pd.read_sql_table(
                table_name=table,
                con=connection,
            )

            output_path = output_dir / f"{table}.csv"

            save_dataframe(dataframe, output_path)

            extraction_summary[table] = len(dataframe)

            print(f"Extracted {table}: " f"{len(dataframe)} records")

    return extraction_summary


def extract_filtered_recipes(
    engine,
    output_path: Path = FILTERED_RECIPES_FILE,
) -> int:
    """Extract recipes matching configured cuisines and categories."""

    if not TARGET_CUISINES:
        raise ValueError("TARGET_CUISINES cannot be empty.")

    if not CATEGORY_PATTERNS:
        raise ValueError("CATEGORY_PATTERNS cannot be empty.")

    query = text(FILTERED_RECIPES_SQL).bindparams(
        bindparam(
            "target_cuisines",
            expanding=True,
        )
    )

    query_parameters = {
        "target_cuisines": list(TARGET_CUISINES),
        **CATEGORY_PATTERNS,
    }

    with engine.connect() as connection:

        dataframe = pd.read_sql_query(
            sql=query,
            con=connection,
            params=query_parameters,
        )

    save_dataframe(dataframe, output_path)

    recipe_count = len(dataframe)

    print(f"Filtered recipes extracted: {recipe_count}")
    print(f"Output file: {output_path}")

    return recipe_count


def agos_db_data_load():
    """
    Run the complete A-GOS database extraction workflow.

    1. Connect to the database.
    2. Extract filtered recipes.
    3. Extract supporting tables.
    """

    engine = get_db_engine()

    try:

        print("\nStarting A-GOS data extraction...")

        recipe_count = extract_filtered_recipes(
            engine=engine,
            output_path=FILTERED_RECIPES_FILE,
        )

        table_summary = extract_tables(
            engine=engine,
            tables=DEFAULT_TABLES,
            output_dir=AGOS_RAW_DIR,
        )

        total_records = sum(table_summary.values())

        print("\nA-GOS extraction completed successfully.")
        print(f"Filtered recipes: {recipe_count}")
        print(f"Supporting tables: {len(table_summary)}")
        print(f"Supporting table records: {total_records}")
        print(f"Output directory: {AGOS_RAW_DIR}")

        return {
            "recipe_count": recipe_count,
            "table_summary": table_summary,
        }

    finally:
        engine.dispose()


if __name__ == "__main__":
    agos_db_data_load()
