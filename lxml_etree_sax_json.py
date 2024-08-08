import json
from io import BytesIO

from lxml import etree

from lxml_etree_json import json_to_xml


class SAXHandler:
    def __init__(self):
        self.stack = []
        self.data = None

    def start(self, tag, attrib):
        self.stack.append({tag: {"@{}".format(k): v for k, v in attrib.items()}})

    def end(self, tag):
        current = self.stack.pop()
        if self.data:
            current[tag]["#text"] = self.data
            self.data = None
        if self.stack:
            parent = self.stack[-1]
            parent[list(parent.keys())[0]].setdefault(tag, []).append(current[tag])
        else:
            self.stack.append(current)

    def data(self, data):
        if data.strip():
            self.data = data.strip()


def xml_to_json(xml_string: str) -> str:
    handler = SAXHandler()
    parser = etree.XMLParser(target=handler)
    xml_bytes = BytesIO(xml_string.encode("utf-8"))
    etree.XML(xml_bytes, parser)
    return json.dumps(handler.stack[0], indent=4)
