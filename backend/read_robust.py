try:
    with open('audit_products_output.txt', 'rb') as f:
        content = f.read()
    # Decode with 'replace' to handle bad chars
    print(content.decode('utf-16', errors='replace')) # PowerShell > redirect defaults to utf-16
except Exception as e:
    print(f"Error: {e}")
