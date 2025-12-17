import json


with open("load_data.json", "r") as f:
    data = json.load(f)


data = [obj for obj in data if obj.get("model") != "contenttypes.contenttype"]


with open("load_data_clean.json", "w") as f:
    json.dump(data, f, indent=4)

print("All contenttypes.contenttype entries removed!")
