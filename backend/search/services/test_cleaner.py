"""
Check if 'and' remains in cleaned text.
"""
import re

text = "Find dextrose suppliers under $800 and list top 5"
STOPWORDS = [
    " in ", " with ", " for ", " of ", " from ", " to ", " between ",
    "please", "search", "find", "show", "me", "list", 
    "details", "price", "prices", "active", "recent", "data", "who", "is", "are",
    "import", "export", "importing", "exporting"
]

clean_text = text.lower()

# Simulate Price Extraction removal first
clean_text = clean_text.replace("under $800", "") 

# Simulate cleaning
clean_text = re.sub(r'\b(?:top|best|first|suggest|rank)\s+\d+\b', '', clean_text, flags=re.IGNORECASE)

for sw in STOPWORDS:
    clean_text = re.sub(r'\b' + re.escape(sw.strip()) + r'\b', ' ', clean_text)

clean_text = re.sub(r'[^\w\s\.]', '', clean_text).strip()
clean_text = re.sub(r'\s+', ' ', clean_text)

print(f"Original: '{text}'")
print(f"Cleaned: '{clean_text}'")
if "and" in clean_text.split():
    print("❌ 'and' remains!")
else:
    print("✅ 'and' removed")
