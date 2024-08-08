import json
from io import BytesIO

from lxml import etree

from lxml_etree_json import json_to_xml


def xml_to_json(xml_string: str) -> str:
    xml_bytes = BytesIO(xml_string.encode("utf-8"))
    context = etree.iterparse(xml_bytes, events=("start", "end"))
    root = None
    stack = []

    for event, elem in context:
        if event == "start":
            d = {elem.tag: {"{}".format(k): v for k, v in elem.attrib.items()}}
            if stack:
                parent = stack[-1]
                parent_key = list(parent.keys())[0]
                if elem.tag not in parent[parent_key]:
                    parent[parent_key][elem.tag] = d[elem.tag]
                else:
                    if isinstance(parent[parent_key][elem.tag], list):
                        parent[parent_key][elem.tag].append(d[elem.tag])
                    else:
                        parent[parent_key][elem.tag] = [
                            parent[parent_key][elem.tag],
                            d[elem.tag],
                        ]
            stack.append(d)
        elif event == "end":
            current = stack.pop()
            if elem.text and elem.text.strip():
                current[elem.tag]["#text"] = elem.text.strip()
            if not stack:
                root = current
            elem.clear()

    # Flatten lists with single elements
    def flatten_json(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, list) and len(value) == 1:
                    obj[key] = value[0]
                elif isinstance(value, dict) and value == {}:
                    obj[key] = None
                elif isinstance(value, (dict, list)):
                    flatten_json(value)
        elif isinstance(obj, list):
            for i in range(len(obj)):
                if isinstance(obj[i], (dict, list)):
                    flatten_json(obj[i])

    flatten_json(root)
    return json.dumps(root, indent=4)
