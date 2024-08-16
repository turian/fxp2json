import json

import pytinyxml2 as tinyxml2

from lxml_etree_iterparse_json import flatten_json


def dict_to_element(doc, parent, content):
    for key, value in content.items():
        if isinstance(value, dict):
            child = doc.NewElement(key)
            parent.InsertEndChild(child)
            dict_to_element(doc, child, value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    child = doc.NewElement(key)
                    parent.InsertEndChild(child)
                    dict_to_element(doc, child, item)
        else:
            # WARNING: This might be wrong
            if value is None:
                # Create a self-closing tag for None values
                child = doc.NewElement(key)
                parent.InsertEndChild(child)
            elif isinstance(value, str):
                parent.SetAttribute(key, value)
            elif isinstance(value, int):
                parent.SetAttribute(key, str(value))
            elif isinstance(value, bool):
                parent.SetAttribute(key, str(value).lower())
            elif isinstance(value, float):
                parent.SetAttribute(key, str(value))
            else:
                raise TypeError(
                    f"Unsupported attribute type for key '{key}': {type(value)}"
                )


# Function to convert XML to JSON using tinyxml2
def xml_to_json(xml_str):
    xml_doc = tinyxml2.XMLDocument()
    xml_doc.Parse(xml_str)

    def element_to_dict(element):
        elem_dict = {element.Value(): {}}
        # Convert attributes
        attr = element.FirstAttribute()
        while attr:
            elem_dict[element.Value()][attr.Name()] = attr.Value()
            attr = attr.Next()
        # Convert child elements
        child = element.FirstChildElement()
        children = []
        while child:
            child_dict = element_to_dict(child)
            tag = child.Value()
            if tag in elem_dict[element.Value()]:
                if not isinstance(elem_dict[element.Value()][tag], list):
                    elem_dict[element.Value()][tag] = [elem_dict[element.Value()][tag]]
                elem_dict[element.Value()][tag].append(child_dict[tag])
            else:
                elem_dict[element.Value()].update(child_dict)
            child = child.NextSiblingElement()
        # Convert text
        if element.GetText():
            elem_dict[element.Value()]["text"] = element.GetText()
        return elem_dict

    root = xml_doc.RootElement()
    root_content = element_to_dict(root)
    flatten_json(root_content)
    return json.dumps(root_content, indent=4)


# Function to convert JSON back to XML using tinyxml2
def json_to_xml(json_str):
    json_obj = json.loads(json_str)

    xml_doc = tinyxml2.XMLDocument()
    root_tag, root_content = list(json_obj.items())[0]
    root_elem = xml_doc.NewElement(root_tag)
    xml_doc.InsertFirstChild(root_elem)
    dict_to_element(xml_doc, root_elem, root_content)

    buffer = tinyxml2.XMLPrinter()
    xml_doc.Print(buffer)
    return buffer.CStr()
