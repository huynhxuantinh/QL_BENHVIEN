import os
import re

TEMPLATE_DIR = r"c:\Users\ASUS\OneDrive\Documents\GISTOOL\QL_BENHVIEN\core\templates\core"

def fix_logout():
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        for file in files:
            if not file.endswith(".html"):
                continue
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # We want to replace `<a class="..." href="{% url 'logout' %}">Đăng xuất</a>`
            # With `<form action="{% url 'logout' %}" method="post" style="display:inline;">{% csrf_token %}<button type="submit" class="...">Đăng xuất</button></form>`
            # We will use regex to find the links.
            
            pattern = re.compile(r'<a\s+([^>]*?)href=[\'"]{% url \'logout\' %}[\'"]([^>]*?)>(.*?)</a>', re.IGNORECASE)
            
            def repl(match):
                attr1 = match.group(1).strip()
                attr2 = match.group(2).strip()
                text = match.group(3).strip()
                
                classes = ""
                # extract class from attr1 or attr2
                class_match = re.search(r'class=[\'"]([^\'"]+)[\'"]', attr1 + " " + attr2, re.IGNORECASE)
                if class_match:
                    classes = f' class="{class_match.group(1)}"'
                    
                return f'<form action="{{% url \'logout\' %}}" method="post" style="display:inline;">{{% csrf_token %}}<button type="submit"{classes}>{text}</button></form>'

            new_content = pattern.sub(repl, content)
            if new_content != content:
                print(f"Updated {file}")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)

if __name__ == "__main__":
    fix_logout()
