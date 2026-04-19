import os

file_path = r'frontend/src/components/Search/SearchResults.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Colors replacement
content = content.replace('gray-', 'slate-')
content = content.replace('indigo-', 'emerald-')

# 2. Wrapper replacement
content = content.replace('className="dashboard-wrapper"', 'className="min-h-screen bg-slate-50 font-sans"')

# 3. Container replacement
content = content.replace('className="dashboard-container"', 'className="max-w-7xl mx-auto px-4 md:px-8 w-full"')
content = content.replace('className="dashboard-container flex gap-8"', 'className="max-w-7xl mx-auto px-4 md:px-8 w-full flex flex-col md:flex-row gap-8"')

# 4. View deal button styling replacement
old_deal_btn = """                                            <Link
                                                to={`/search/supplier/${encodeURIComponent(supplier.name)}?q=${encodeURIComponent(query)}&scope=${encodeURIComponent(scope)}${subcatId ? `&subcat_id=${encodeURIComponent(subcatId)}` : ''}${variantName ? `&variant_name=${encodeURIComponent(variantName)}` : ''}${overrideIntent ? `&intent=${encodeURIComponent(overrideIntent)}` : ''}`}
                                                className="stat-action text-center"
                                                style={{ textDecoration: 'none' }}
                                            >
                                                View Deal
                                            </Link>"""

new_deal_btn = """                                            <Link
                                                to={`/search/supplier/${encodeURIComponent(supplier.name)}?q=${encodeURIComponent(query)}&scope=${encodeURIComponent(scope)}${subcatId ? `&subcat_id=${encodeURIComponent(subcatId)}` : ''}${variantName ? `&variant_name=${encodeURIComponent(variantName)}` : ''}${overrideIntent ? `&intent=${encodeURIComponent(overrideIntent)}` : ''}`}
                                                className="px-6 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-bold rounded-lg transition-all shadow-md shadow-emerald-500/20 text-center text-sm block"
                                            >
                                                View Deal
                                            </Link>"""

# Fix a potential variant where string formatting or interpolation is different
content = content.replace('className="stat-action text-center"\n                                                style={{ textDecoration: \'none\' }}', 'className="px-6 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-bold rounded-lg transition-all shadow-md shadow-emerald-500/20 text-center text-sm block"')
content = content.replace(old_deal_btn, new_deal_btn)

# 5. Fix card border class string which might be using `gray-` vs `slate-` improperly after replacement if it was dynamic
# Ensure the padding fix
content = content.replace("style={{ padding: '1rem 2rem', maxWidth: '1400px', margin: '0 auto' }}", "")
content = content.replace("style={{ paddingTop: '2rem' }}", "className=\"max-w-7xl mx-auto px-6 py-8 flex items-start gap-8\"")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SearchResults.js updated!")
