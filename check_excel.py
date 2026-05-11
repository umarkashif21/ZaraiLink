import pandas as pd

file_path = "export_data.xlsx"

df = pd.read_excel(file_path, header=6)  # actual column names are on row 7

df.columns = df.columns.str.strip().str.replace(" ", "_")

print("Columns in file after cleaning:")
print(df.columns)

subcat_column = "Sub-Category".replace("-", "_")
subcat_column = "Sub-Category"

df[subcat_column] = df[subcat_column].astype(str).str.strip()

unique_count = df[subcat_column].nunique()
print("\nUnique Sub-Categories in Excel:", unique_count)

print("\nSample Sub-Categories:")
print(df[subcat_column].unique()[:20])
