import json

import pytinyxml2 as tinyxml2


def dict_to_element(doc, parent, content):
    for key, value in content.items():
        print(f"Setting attribute '{key}' with value '{value}' of type '{type(value)}'")
        if isinstance(value, dict):
            child = doc.NewElement(key)
            parent.InsertEndChild(child)
            dict_to_element(doc, child, value)
        else:
            if isinstance(value, str):
                parent.SetAttribute(key, value)
            elif isinstance(value, int):
                parent.SetAttribute(key, value)
            elif isinstance(value, bool):
                parent.SetAttribute(key, value)
            elif isinstance(value, float):
                parent.SetAttribute(key, value)
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
        while child:
            elem_dict[element.Value()].update(element_to_dict(child))
            child = child.NextSiblingElement()
        # Convert text
        if element.GetText():
            elem_dict[element.Value()]["text"] = element.GetText()
        return elem_dict

    root = xml_doc.RootElement()
    return json.dumps(element_to_dict(root), indent=4)


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
