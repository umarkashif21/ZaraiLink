from search.services.query_parser import QueryInterpreter

# Test the problematic query
query = "Find me Dextrose Suppliers from China"
interpreter = QueryInterpreter()
result = interpreter.parse(query)

print("====== PARSER OUTPUT ======")
print(f"Query: {query}")
print(f"Result: {result}")
print(f"Intent: {result.get('intent')}")
print(f"Product: {result.get('product')}")
print(f"Country Filter: {result.get('country_filter')}")
print(f"Scope: {result.get('scope')}")
