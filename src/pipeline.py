from src.ingestion.hf_data_load import hf_data_load
from src.ingestion.ora_data_load import ora_data_load


def pipeline():

    # hf_data = hf_data_load("arya123321/recipes","allrecipes")

    # australian_data = ora_data_load(
    #     "https://github.com/adambouhmad/open-recipe-archive.git", "australian-table"
    # )

    # all_ora_data = ora_data_load(
    #     "https://github.com/adambouhmad/open-recipe-archive.git"
    # )
    pass

if __name__ == "__main__":
    pipeline()
