import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update search bar placeholder to simply "Search"
    old_placeholder = 'placeholder="Search 1,000,000+ hotels, sightseeing, transit hubs, Delhi, Goa, Mumbai..."'
    new_placeholder = 'placeholder="Search"'
    if old_placeholder in content:
        content = content.replace(old_placeholder, new_placeholder)
        print(f"Updated search placeholder in {filepath}")
    else:
        # regex replace in case of minor whitespace variance
        content = re.sub(r'placeholder="Search 1,000,000\+[^"]*"', 'placeholder="Search"', content)
        print(f"Updated search placeholder (regex) in {filepath}")

    # 2. Extract and sort destination-select options
    pattern = r'(<select id="destination-select"[^>]*>)(.*?)(</select>)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print(f"destination-select not found in {filepath}")
        return

    open_tag = match.group(1)
    inner = match.group(2)
    close_tag = match.group(3)

    option_pattern = r'(<option\s+value="([^"]+)"[^>]*>.*?</option>)'
    options = re.findall(option_pattern, inner)

    pan_india_opt = None
    city_options = []
    for full_opt, val in options:
        if val == "Pan-India":
            pan_india_opt = full_opt
        else:
            city_options.append((val.lower(), full_opt))

    # Sort city options alphabetically by city value
    sorted_city_options = sorted(city_options, key=lambda x: x[0])

    new_inner = "\n        " + pan_india_opt + "\n"
    for _, opt in sorted_city_options:
        new_inner += "        " + opt + "\n      "

    new_select = open_tag + new_inner + close_tag
    content = content[:match.start()] + new_select + content[match.end():]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully sorted destination options in {filepath}")

process_file("frontend/map_view.html")
process_file("map_view.html")
