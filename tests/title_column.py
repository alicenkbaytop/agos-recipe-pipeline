import pandas as pd

df = pd.read_csv("data/raw/allrecipes_train.csv")

# display(df.head())

test_df = df.head(5)

test_df.to_csv("data/interim/allrecipes_test.csv", index=False)
