import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

container_str = """            action_buttons_container = st.container()
            
"""
content = content.replace("            # 버튼 영역\n", container_str)

pattern = r"(            action_col1, action_col2, action_col3 = st\.columns\(\[1, 1\.5, 1\.5\]\)\n.*?)(?=            view_filter = st\.radio\()"
match = re.search(pattern, content, flags=re.DOTALL)
if match:
    button_block = match.group(1)
    content = content.replace(button_block, "") 
    
    button_block_indented = ""
    for line in button_block.split("\n"):
        if line.strip() == "":
            button_block_indented += "\n"
        else:
            button_block_indented += "    " + line + "\n"
            
    button_block_indented = button_block_indented.replace('if df_result["선택"].any():', 'if edited_df["선택"].any():')
    button_block_indented = button_block_indented.replace('df_result = df_result[~df_result["선택"]].copy()', 'df_result = df_result[~edited_df["선택"]].copy()')
    button_block_indented = button_block_indented.replace('selected_items = df_result[df_result["선택"]].copy()', 'selected_items = df_result[edited_df["선택"]].copy()')
    
    new_bottom = """            edited_df = render_editor_and_save()
            
            with action_buttons_container:
""" + button_block_indented

    content = content.replace("            render_editor_and_save()\n", new_bottom)
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success")
else:
    print("Failed to find button block")
