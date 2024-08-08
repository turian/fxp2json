import json

from lxml import etree

from lxml_etree_json import json_to_xml


def xml_to_json(xml_string: str) -> str:
    context = etree.iterparse(xml_string, events=("start", "end"))
    root = None
    stack = []
    for event, elem in context:
        if event == "start":
            d = {elem.tag: {"@{}".format(k): v for k, v in elem.attrib.items()}}
            if stack:
                stack[-1].setdefault(elem.tag, []).append(d[elem.tag])
            stack.append(d)
        elif event == "end":
            current = stack.pop()
            if elem.text and elem.text.strip():
                current[elem.tag]["#text"] = elem.text.strip()
            if not stack:
                root = current
            elem.clear()
    return json.dumps(root, indent=4)
