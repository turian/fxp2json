import json

from lxml import etree

from lxml_etree_json import json_to_xml


class SAXHandler:
    def __init__(self):
        self.stack = []
        self.data = None

    def start(self, tag, attrib):
        self.stack.append({tag: {"{}".format(k): v for k, v in attrib.items()}})

    def end(self, tag):
        current = self.stack.pop()
        if self.data:
            current[tag]["#text"] = self.data
            self.data = None
        if self.stack:
            parent = self.stack[-1]
            parent_key = list(parent.keys())[0]
            if tag not in parent[parent_key]:
                parent[parent_key][tag] = current[tag]
            else:
                if isinstance(parent[parent_key][tag], list):
                    parent[parent_key][tag].append(current[tag])
                else:
                    parent[parent_key][tag] = [parent[parent_key][tag], current[tag]]
        else:
            self.stack.append(current)

    def data(self, data):
        if data.strip():
            self.data = data.strip()

    def close(self):
        return self.stack[0]


def simplify_json(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, list) and len(value) == 1:
                obj[key] = value[0]
            elif isinstance(value, dict) and value == {}:
                obj[key] = None
            elif isinstance(value, dict) or isinstance(value, list):
                simplify_json(value)
    elif isinstance(obj, list):
        for i in range(len(obj)):
            if isinstance(obj[i], dict) or isinstance(obj[i], list):
                simplify_json(obj[i])


def xml_to_json(xml_string: str) -> str:
    handler = SAXHandler()
    parser = etree.XMLParser(target=handler)
    etree.XML(xml_string.encode("utf-8"), parser)
    json_obj = handler.close()
    simplify_json(json_obj)
    return json.dumps(json_obj, indent=4)
