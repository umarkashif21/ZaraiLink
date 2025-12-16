import pandas as pd
file_path = r"d:\Salman Adnan\HU\7th Semester\FYP\Coding\import_data_1year.xlsx"
df = pd.read_excel(file_path, header=None)
print("Shape:", df.shape)
for i, row in df.iterrows():
    if not row.isnull().all():
        print(f"First non-empty row is index {i}:")
        print(row.tolist())
        break
