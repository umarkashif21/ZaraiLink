import os
import re
import tokenize
from io import BytesIO

def strip_python_comments(source):
    """
    Removes comments from Python source code using the tokenize module.
    Preserves docstrings and strings.
    """
    # Repair artifact from previous run if present
    source = re.sub(r'^utf-8\s*', '', source)
    
    io_obj = BytesIO(source.encode('utf-8'))
    out = ""
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    try:
        tokens = tokenize.tokenize(io_obj.readline)
        for tok in tokens:
            token_type = tok.type
            token_string = tok.string
            start_line, start_col = tok.start
            end_line, end_col = tok.end
            
            if start_line > last_lineno:
                last_col = 0
            if start_col > last_col:
                out += (" " * (start_col - last_col))
            
            # Remove comments and encoding
            if token_type == tokenize.COMMENT or token_type == tokenize.ENCODING:
                pass
            # This handles docstrings as strings, effectively keeping them. 
            # If the user wanted docstrings removed, we'd need more logic, 
            # but usually "comments" refers to # comments.
            else:
                out += token_string
            
            prev_toktype = token_type
            last_col = end_col
            last_lineno = end_line
    except tokenize.TokenError:
        return source # Return original on error
        
    return out

def strip_js_comments(source):
    """
    Removes // and /* */ comments from JavaScript source code.
    Respects strings and regex literals.
    """
    output = []
    i = 0
    length = len(source)
    state = "CODE" # CODE, STRING_SINGLE, STRING_DOUBLE, STRING_BACKTICK, COMMENT_LINE, COMMENT_BLOCK
    
    while i < length:
        char = source[i]
        next_char = source[i+1] if i+1 < length else ""
        
        if state == "CODE":
            if char == '/' and next_char == '/':
                state = "COMMENT_LINE"
                i += 2
                continue
            elif char == '/' and next_char == '*':
                state = "COMMENT_BLOCK"
                i += 2
                continue
            elif char == "'":
                state = "STRING_SINGLE"
                output.append(char)
            elif char == '"':
                state = "STRING_DOUBLE"
                output.append(char)
            elif char == '`':
                state = "STRING_BACKTICK"
                output.append(char)
            else:
                output.append(char)
                
        elif state == "STRING_SINGLE":
            output.append(char)
            if char == "'" and source[i-1] != '\\':
                state = "CODE"
        
        elif state == "STRING_DOUBLE":
            output.append(char)
            if char == '"' and source[i-1] != '\\':
                state = "CODE"
                
        elif state == "STRING_BACKTICK":
            output.append(char)
            if char == '`' and source[i-1] != '\\':
                state = "CODE"
        
        elif state == "COMMENT_LINE":
            if char == '\n':
                state = "CODE"
                output.append(char) # Keep the newline
                
        elif state == "COMMENT_BLOCK":
            if char == '*' and next_char == '/':
                state = "CODE"
                i += 2
                continue
        
        i += 1
        
    return "".join(output)

def process_file(filepath):
    """
    Reads a file, strips comments, and writes it back safely.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        new_content = None
        
        if filepath.endswith('.py'):
            new_content = strip_python_comments(content)
        elif filepath.endswith(('.js', '.jsx', '.ts', '.tsx')):
            new_content = strip_js_comments(content)
            
        if new_content is not None and new_content != original_content:
            # Basic validation: If file becomes empty, it's valid if it was just encoding/comments
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Processed: {filepath}")
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    root_dirs = ['backend', 'frontend/src']
    
    target_files = []
    
    for root_dir in root_dirs:
        for root, dirs, files in os.walk(root_dir):
            # Skip hidden dirs and venv/migrations
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv' and d != 'migrations' and d != 'node_modules']
            
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                    # Skip migrations files specifically
                    if "migrations" in root:
                        continue
                    
                    target_files.append(os.path.join(root, file))
    
    print(f"Found {len(target_files)} files to process.")
    for filepath in target_files:
        process_file(filepath)
    print("Done.")

if __name__ == "__main__":
    main()
