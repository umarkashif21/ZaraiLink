"""
Check fructose data to see if 0 results is a bug or just no data.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/search/"

def check_fructose():
    # 1. Broad search
    print("1. Broad: 'fructose suppliers'")
    r = requests.get(f"{BASE_URL}?q=fructose%20suppliers&scope=WORLDWIDE").json()
    print(f"   Count: {len(r.get('results', []))}")
    
    # 2. Country
    print("2. Country: 'fructose suppliers in China'")
    r = requests.get(f"{BASE_URL}?q=fructose%20suppliers%20in%20China&scope=WORLDWIDE").json()
    print(f"   Count: {len(r.get('results', []))}")
    
    # 3. Price
    print("3. Price: 'fructose under 700'")
    r = requests.get(f"{BASE_URL}?q=fructose%20under%20700&scope=WORLDWIDE").json()
    print(f"   Count: {len(r.get('results', []))}")
    
    # 4. Volume
    print("4. Volume: '40MT fructose'")
    r = requests.get(f"{BASE_URL}?q=40MT%20fructose&scope=WORLDWIDE").json()
    results = r.get('results', [])
    print(f"   Count: {len(results)}")
    if results:
        max_vol = results[0].get('total_volume_mt') # approx
        print(f"   Top vol: {max_vol}")

    # 5. Combined (The failing one)
    print("5. Combined: 'Top 3 fructose suppliers in China for 40MT under 700'")
    url = "http://localhost:8000/api/search/?q=Top%203%20fructose%20suppliers%20in%20China%20for%2040MT%20under%20700&scope=WORLDWIDE"
    r = requests.get(url).json()
    print(f"   Count: {len(r.get('results', []))}")

if __name__ == "__main__":
    check_fructose()
