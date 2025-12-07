import json

# Load your fixture
with open("load_data.json", "r") as f:
    data = json.load(f)

# Keep only entries that are NOT contenttypes.contenttype
data = [obj for obj in data if obj.get("model") != "contenttypes.contenttype"]

# Save cleaned fixture
with open("load_data_clean.json", "w") as f:
    json.dump(data, f, indent=4)

print("All contenttypes.contenttype entries removed!")
