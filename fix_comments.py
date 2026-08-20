import os
import re

def fix_comments(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'\{#\s*(═+)\s*\n(.*?)\n\s*(═+)\s*#\}'
    
    def repl(m):
        top_line = m.group(1)
        text = m.group(2)
        bottom_line = m.group(3)
        return f'<!-- {top_line}\n{text}\n{bottom_line} -->'
        
    new_content = re.sub(pattern, repl, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {path}")

for root, dirs, files in os.walk('/home/alejandro/plataforma-novelas/'):
    for file in files:
        if file.endswith('.html'):
            fix_comments(os.path.join(root, file))
