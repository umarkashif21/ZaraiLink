import re

query = "Find suppliers in China and buyers in Pakistan"
parts = re.split(r'\b(?:and|also)\b', query, flags=re.IGNORECASE)
print(f"Parts: {parts}")

SELL_PHRASES = ["buyers"]
part = " buyers in Pakistan"

matches = []
for phrase in SELL_PHRASES:
    if re.search(r'\b' + re.escape(phrase) + r'\b', part.lower()):
        matches.append(phrase)

print(f"Matches in part 2: {matches}")
