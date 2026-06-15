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
            
            # Use regex to find any string that has {ThemeManager...} but isn't prefixed with f
            # Match: any non-word char (like space or parenthesis) \1
            # Then quote type \2
            # Then string contents \3
            # Then same quote \2
            content = re.sub(
                r'([^\w])(\"\"\"|\'\'\'|\"|\')(.*?\{ThemeManager\.Typography.*?)\2',
                r'\1f\2\3\2',
                content,
                flags=re.DOTALL
            )
            
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Fixed f-string in {file}')
