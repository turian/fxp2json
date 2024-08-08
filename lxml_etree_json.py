import json
from collections import defaultdict
from io import BytesIO

from lxml import etree


def xml_to_json(xml_string: str) -> str:
    def element_to_dict(element):
        elem_dict = {element.tag: {} if element.attrib else None}
        children = list(element)
        if children:
            dd = defaultdict(list)
            for dc in map(element_to_dict, children):
                for k, v in dc.items():
                    dd[k].append(v)
            elem_dict = {
                element.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}
            }
        if element.attrib:
            elem_dict[element.tag].update(
                ("@" + k, v) for k, v in element.attrib.items()
            )
        if element.text:
            text = element.text.strip()
            if children or element.attrib:
                if text:
                    elem_dict[element.tag]["#text"] = text
            else:
                elem_dict[element.tag] = text
        return elem_dict

    xml_bytes = BytesIO(xml_string.encode("utf-8"))
    root = etree.fromstring(xml_bytes)
    return json.dumps(element_to_dict(root), indent=4)


def json_to_xml(json_string: str) -> str:
    def dict_to_element(d):
        def _to_element(tag, value):
            element = etree.Element(tag)
            if isinstance(value, dict):
                for k, v in value.items():
                    if k.startswith("@"):
                        element.set(k[1:], v)
                    elif k == "#text":
                        element.text = v
                    else:
                        element.append(_to_element(k, v))
            else:
                element.text = str(value)
            return element

        assert len(d) == 1
        tag, value = next(iter(d.items()))
        return _to_element(tag, value)

    d = json.loads(json_string)
    root = dict_to_element(d)
    return etree.tostring(root, pretty_print=False).decode()
