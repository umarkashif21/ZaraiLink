import os

frontend_src = r'c:\Users\Dell\Documents\ZaraiLink\frontend\src'
count = 0
for root, _, files in os.walk(frontend_src):
    for f in files:
        if f.endswith(('.js', '.jsx')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            if 'import.meta.env.VITE_API_BASE_URL' in content:
                new_content = content.replace('import.meta.env.VITE_API_BASE_URL', 'process.env.REACT_APP_API_BASE_URL')
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                count += 1
print(f'Replaced in {count} files.')
