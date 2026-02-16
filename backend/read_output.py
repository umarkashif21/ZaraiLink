try:
    with open('audit_output.txt', 'r') as f:
        print(f.read())
except Exception as e:
    print(f"Error: {e}")
