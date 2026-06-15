import os
import re

mapping = {
    '28px': 'TITLE',
    '24px': 'TITLE',
    '20px': 'HEADING_LARGE',
    '16px': 'HEADING',
    '15px': 'SUBHEADING',
    '14px': 'SUBHEADING',
    '13px': 'BODY',
    '12px': 'BODY',
    '11px': 'CAPTION',
    '10px': 'CAPTION',
    '9px': 'MICRO',
    '8px': 'MICRO',
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    def replacer(match):
        px = match.group(1)
        if px in mapping:
            return f"font-size: {{ThemeManager.Typography.{mapping[px]}}}"
        return match.group(0)

    content = re.sub(r'font-size:\s*(\d+px)', replacer, content)
    
    if content != original_content:
        if 'ThemeManager' not in original_content:
            content = "from ui.themes.theme_manager import ThemeManager\n" + content
            
        # Convert non f-strings into f-strings if they contain our injected {ThemeManager...}
        # A simple hack: look for setStyleSheet("...{ThemeManager...") and make it setStyleSheet(f"...{ThemeManager...")
        content = re.sub(r'(?<!f)([\"\'])(.*?\{ThemeManager\.Typography.*?)\1', r'f\1\2\1', content, flags=re.DOTALL)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")

ui_dir = os.path.join(os.path.dirname(__file__), 'ui')
for root, dirs, files in os.walk(ui_dir):
    for file in files:
        if file.endswith('.py'):
            process_file(os.path.join(root, file))
