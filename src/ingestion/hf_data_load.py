from datasets import load_dataset
from pathlib import Path


def hf_data_load(dataset_name, output_name):

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading dataset: {dataset_name}")

    dataset = load_dataset(dataset_name)

    saved_files = []

    for split_name, split_data in dataset.items():

        df = split_data.to_pandas()

        output_path = output_dir / f"{output_name}_{split_name}.csv"

        df.to_csv(output_path, index=False)

        saved_files.append(output_path)

        print(f"Saved {len(df)} rows to {output_path}")

    return saved_files
