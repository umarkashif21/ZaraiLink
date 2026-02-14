import requests
import json
import sys

def verify_query(query):
    url = "http://localhost:8000/api/search/"
    try:
        response = requests.get(url, params={"q": query})
        if response.status_code == 200:
            data = response.json()
            print(f"Query: '{query}'")
            print("Parsed Query:", json.dumps(data.get('parsed_query'), indent=2))
            print("Result Count:", data.get('count'))
            # Check if extracted filters are correct in parsed_query
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    # Test cases
    verify_query("Buy 50MT sugar from Brazil")
    verify_query("Who buys ethanol?")
