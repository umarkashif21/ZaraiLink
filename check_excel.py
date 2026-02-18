import pandas as pd

file_path = "export_data.xlsx"

# Load Excel, skip extra header rows
df = pd.read_excel(file_path, header=6)  # actual column names are on row 7

# Clean column names
df.columns = df.columns.str.strip().str.replace(" ", "_")

print("Columns in file after cleaning:")
print(df.columns)

# Now pick the sub-category column (match exact name after cleaning)
subcat_column = "Sub-Category".replace("-", "_")  # becomes Sub_Category
subcat_column = "Sub-Category"

# Strip whitespace
df[subcat_column] = df[subcat_column].astype(str).str.strip()

# Count unique subcategories
unique_count = df[subcat_column].nunique()
print("\nUnique Sub-Categories in Excel:", unique_count)

# Optional: list them
print("\nSample Sub-Categories:")
print(df[subcat_column].unique()[:20])
