from src.ingestion.hf_data_load import hf_data_load
from src.ingestion.ora_data_load import ora_data_load
from src.ingestion.agos_db_data_load import agos_db_data_load

ORA_REPO_URL = "https://github.com/adambouhmad/open-recipe-archive.git"


def pipeline():

    print("\nStarting recipe data pipeline...")

    # 1. Hugging Face
    # hf_data = hf_data_load(
    #     "arya123321/recipes",
    #     "allrecipes"
    # )

    # 2. Open Recipe Archive

    # Load one collection
    # australian_data = ora_data_load(
    #     ORA_REPO_URL,
    #     "australian-table"
    # )

    # Load all collections
    # all_ora_data = ora_data_load(ORA_REPO_URL)

    # 3. A-GOS database
    agos_data = agos_db_data_load()

    print("\nData ingestion completed!")


if __name__ == "__main__":
    pipeline()
