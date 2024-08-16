import json
from collections import defaultdict

import bs4
from bs4 import BeautifulSoup


def xml_to_json(xml_string: str) -> str:
    def element_to_dict(element):
        elem_dict = {element.name: {}}

        # Add attributes
        if element.attrs:
            elem_dict[element.name].update(
                # {f"@{k}": v for k, v in element.attrs.items()}
                {f"{k}": v for k, v in element.attrs.items()}
            )

        # Add children
        children = list(element.children)
        if children:
            child_dict = defaultdict(list)
            for child in children:
                if isinstance(child, bs4.element.Tag):
                    child_dict[child.name].append(element_to_dict(child)[child.name])
                elif isinstance(child, bs4.element.NavigableString) and child.strip():
                    child_dict["#text"].append(child.strip())
            for k, v in child_dict.items():
                if len(v) == 1:
                    elem_dict[element.name][k] = v[0]
                else:
                    elem_dict[element.name][k] = v

        # If no attributes and no children, make it None
        if not elem_dict[element.name]:
            elem_dict[element.name] = None

        return elem_dict

    soup = BeautifulSoup(xml_string, "xml")
    root = soup.find()
    return json.dumps(element_to_dict(root), indent=4)


def json_to_xml(json_string: str) -> str:
    def dict_to_element(soup, d):
        def _to_element(tag, value):
            element = soup.new_tag(tag)
            if isinstance(value, dict):
                for k, v in value.items():
                    if k.startswith("@"):
                        element.attrs[k[1:]] = v
                    elif k == "#text":
                        element.string = v
                    else:
                        child = _to_element(k, v)
                        element.append(child)
            elif isinstance(value, list):
                for item in value:
                    child = _to_element(tag, item)
                    element.append(child)
            else:
                element.string = str(value)
            return element

        assert len(d) == 1
        tag, value = next(iter(d.items()))
        return _to_element(tag, value)

    d = json.loads(json_string)
    soup = BeautifulSoup("", "xml")
    root = dict_to_element(soup, d)
    soup.append(root)

    # Ensure space before self-closing tags
    xml_string = str(soup)
    xml_string = xml_string.replace("/>", " />")
    return xml_string
