import re

def check_file(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # match tags like <tag attr="1" attr="2">
    tags = re.findall(r'<([a-zA-Z0-9-]+)(\s+[^>]+)>', content)
    for tag_name, attrs_str in tags:
        # find all attributes name
        attr_names = re.findall(r'([a-zA-Z0-9_:@.-]+)=', attrs_str)
        seen = set()
        for attr in attr_names:
            if attr in seen:
                print(f"Duplicate attribute '{attr}' in tag <{tag_name}>")
            seen.add(attr)

check_file("frontend/src/views/LandingView.vue")
