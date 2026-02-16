import json

def analyze_counts():
    with open('audit_broad.json', 'r') as f:
        data = json.load(f)
        
    items = data['products']
    
    total_strict = 0
    total_fuzzy = 0
    
    strict_items = []
    fuzzy_items = []
    
    print("--- Analysis ---")
    
    for i in items:
        name = i['product_item__name'].upper()
        count = i['c']
        
        # Strict: Contains "DEXTROSE MONOHYDRATE"
        if "DEXTROSE MONOHYDRATE" in name:
            total_strict += count
            strict_items.append((name, count))
            
        # Fuzzyish: Contains "DEXTROSE" and maybe "MONO" or "HYDRATE" or "MOOHYDRATE" or "MONOYDRATE"
        # Let's look for specific typos seen
        if "MONOYDRATE" in name or "MOOHYDRATE" in name:
             print(f"FOUND TYPO: {name} ({count})")
             total_fuzzy += count
             fuzzy_items.append((name, count))

    print(f"\nStrict 'DEXTROSE MONOHYDRATE' Count: {total_strict}")
    print(f"Typo Items Count: {total_fuzzy}")
    print(f"Total (Strict + Typos): {total_strict + total_fuzzy}")

if __name__ == "__main__":
    analyze_counts()
