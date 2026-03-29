import os, re

frontend_src = r'c:\Users\Dell\Documents\ZaraiLink\frontend\src'
count = 0

for root, _, files in os.walk(frontend_src):
    for f in files:
        if f.endswith(('.js', '.jsx')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            if 'http://localhost:8000' in content:
                # Handle direct backtick matches
                new_content = content.replace('`http://localhost:8000', '`${import.meta.env.VITE_API_BASE_URL}')
                
                # Handle strict hardcoded strings WITHOUT trailing slashes
                new_content = new_content.replace("'http://localhost:8000'", "import.meta.env.VITE_API_BASE_URL")
                new_content = new_content.replace('"http://localhost:8000"', "import.meta.env.VITE_API_BASE_URL")
                
                # Handle strings with trailing paths, morphing them into template literals
                new_content = re.sub(r"'http://localhost:8000/([^']*)'", r"`${import.meta.env.VITE_API_BASE_URL}/\1`", new_content)
                new_content = re.sub(r'"http://localhost:8000/([^"]*)"', r"`${import.meta.env.VITE_API_BASE_URL}/\1`", new_content)
                
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                count += 1
                print(f'Replaced in {f}')

print(f'Total files modified: {count}')
