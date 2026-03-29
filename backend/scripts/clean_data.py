import pandas as pd

df = pd.read_csv("scripts/training_data.csv")
df.columns = df.columns.str.strip()
df['query'] = df['query'].str.strip().str.lower()
df['intent'] = df['intent'].str.strip().str.upper()

# Show duplicates before removing
dupes = df[df.duplicated(subset='query', keep=False)]
if len(dupes) > 0:
    print("DUPLICATE QUERIES FOUND:")
    print(dupes.sort_values('query').to_string())
    print(f"\nTotal rows with duplicates: {len(dupes)}")
else:
    print("No duplicates found")

# For duplicates, keep BUY label (since "need supplier" = BUY)
# Sort so BUY comes first, then drop duplicates keeping first occurrence
df = df.sort_values('intent', ascending=True)  # BUY comes before SELL alphabetically
df = df.drop_duplicates(subset='query', keep='first')

# Save cleaned version
df.to_csv("scripts/training_data.csv", index=False)

print(f"\nCleaned dataset saved.")
print(f"Total rows: {len(df)}")
print(f"BUY: {len(df[df['intent']=='BUY'])}")
print(f"SELL: {len(df[df['intent']=='SELL'])}")