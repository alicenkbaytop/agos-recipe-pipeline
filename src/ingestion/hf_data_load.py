from datasets import load_dataset

from config import HF_RAW_DIR


def hf_data_load(dataset_name, output_name):
    """
    Download a Hugging Face dataset and save its splits as CSV.

    Example:
        dataset_name = "username/dataset"
        output_name = "allrecipes"

    Output:
        allrecipes_train.csv
        allrecipes_test.csv
    """

    # Create output directory
    output_dir = HF_RAW_DIR

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(f"\nLoading Hugging Face dataset: {dataset_name}")

    # Download/load dataset
    dataset = load_dataset(dataset_name)

    saved_files = []

    # Process each split
    for split_name, split_data in dataset.items():

        # Convert Hugging Face Dataset to pandas DataFrame
        df = split_data.to_pandas()

        # Build output filename
        output_path = output_dir / f"{output_name}_{split_name}.csv"

        # Save CSV
        df.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
        )

        saved_files.append(output_path)

        print(f"Saved {len(df)} rows " f"from '{split_name}' split to {output_path}")

    print("\nHugging Face ingestion completed!")

    return saved_files


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    hf_data_load(
        dataset_name="arya123321/recipes",
        output_name="allrecipes",
    )
