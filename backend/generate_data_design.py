import json

with open('schema_dump.json', 'r') as f:
    schema = json.load(f)

md_lines = ["# ZaraiLink Database Design\n"]

for model_name, info in schema.items():
    md_lines.append(f"### {model_name}")
    md_lines.append(f"**App Context**: `{info['app']}`")
    if info['desc']:
        md_lines.append(f"{info['desc']}")
    md_lines.append("\n**Attributes:**")
    
    for field in info['fields']:
        attrs = []
        if field['primary_key']:
            attrs.append("Primary key")
        else:
            if field['null']:
                attrs.append("Nullable")
            if field['unique']:
                attrs.append("Unique")
            if field['is_fk']:
                attrs.append(f"Foreign key to {field['related']}")
        
        attr_desc = ", ".join(attrs)
        if attr_desc:
            md_lines.append(f"- `{field['name']}` ({field['type']}) — {attr_desc}")
        else:
            md_lines.append(f"- `{field['name']}` ({field['type']})")
    
    if info['rels']:
        md_lines.append("\n**Relationships:**")
        for rel in info['rels']:
            md_lines.append(f"- {rel}")
            
    md_lines.append("\n---\n")

with open('ZARAILINK_DATA_DESIGN.md', 'w') as f:
    f.write("\n".join(md_lines))
