from pathlib import Path

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = PROJECT_ROOT

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

AGOS_RAW_DIR = RAW_DATA_DIR / "agos"
HF_RAW_DIR = RAW_DATA_DIR / "hf"
ORA_RAW_DIR = RAW_DATA_DIR / "ora"
ORA_REPO_DIR = RAW_DATA_DIR / "open_recipe_archive_repo"

FILTERED_RECIPES_DIR = AGOS_RAW_DIR / "filtered_recipes"

FILTERED_RECIPES_FILE = FILTERED_RECIPES_DIR / "filtered_recipes.csv"


# --------------------------------------------------
# TARGET CUISINES
# --------------------------------------------------

TARGET_CUISINES = (
    "Filipino",
    "Indonesian",
    "Indian",
    "Russian",
    "Turkish",
    "Ukrainian",
)


# --------------------------------------------------
# TARGET RECIPE CATEGORIES
# --------------------------------------------------

CATEGORY_PATTERNS = {
    "soups": "%Soups%",
    "main": "%Main%",
    "side": "%Side%",
    "protein": "%PROTEIN%",
    "salad": "%Salad%",
}


# --------------------------------------------------
# FILTERED RECIPE SQL QUERY
# --------------------------------------------------

FILTERED_RECIPES_SQL = """
    SELECT
        r.*,
        c.title AS cuisine,
        cat.title AS category

    FROM recipes r

    JOIN cuisines c
        ON r.cuisine_id = c.id

    JOIN categories cat
        ON r.category_id = cat.id

    WHERE c.title IN :target_cuisines

    AND (
        cat.title LIKE :soups
        OR cat.title LIKE :main
        OR cat.title LIKE :side
        OR cat.title LIKE :protein
        OR cat.title LIKE :salad
    )

    ORDER BY c.title, cat.title, r.id;
"""


# --------------------------------------------------
# SUPPORTING TABLES
# --------------------------------------------------

DEFAULT_TABLES = (
    "ingredient_recipe",
    "ingredients",
    "ingredient_conversions",
    "uoms",
    "uom_aliases",
    "cuisines",
    "categories",
    "category_recipe",
    "cuisine_nationality",
    "nationalities",
    "recipe_variants",
    "recipe_variant_ingredients",
)
