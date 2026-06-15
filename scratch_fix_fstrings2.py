import os
import re

ui_dir = os.path.join(os.path.dirname(__file__), 'ui')

for root, dirs, files in os.walk(ui_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            original = content
            
            # If the file has {ThemeManager.Typography, we must ensure the enclosing string is an f-string.
            # Easiest way: just change setStyleSheet(" to setStyleSheet(f"
            # Since almost all font-size hardcodes were in setStyleSheet calls.
            
            def add_f_prefix(match):
                # match.group(1) is the opening quote (could be ", ', """, ''')
                quote = match.group(1)
                body = match.group(2)
                # check if body contains ThemeManager.Typography
                if '{ThemeManager.Typography' in body:
                    return f'setStyleSheet(f{quote}{body}'
                return match.group(0)

            # Match setStyleSheet( optionally followed by whitespace, then quote, then anything until close.
            # Actually, `content.replace('setStyleSheet("', 'setStyleSheet(f"')` is much simpler and safe
            # since all stylesheets with {ThemeManager} will need it. But it might double-f `setStyleSheet(f"`
            
            content = re.sub(r'setStyleSheet\(\s*([\"\']{1,3})(.*?)\)', add_f_prefix, content, flags=re.DOTALL)
            
            # Also fix f"f""
            content = content.replace('f"f""', 'f"""')
            content = content.replace("f'f''", "f'''")
            
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Fixed {file}')
