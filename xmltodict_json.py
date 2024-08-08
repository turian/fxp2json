import json

import xmltodict


def xml_to_json(xml_str):
    # Parse the XML to an ordered dictionary
    parsed_dict = xmltodict.parse(
        xml_str, dict_constructor=dict, attr_prefix="", force_list=True
    )
    return json.dumps(parsed_dict, indent=4)


def json_to_xml(json_str):
    # Load the JSON string to a dictionary
    json_dict = json.loads(json_str)
    # Convert the dictionary back to XML
    xml_str = xmltodict.unparse(json_dict, pretty=False)
    return xml_str
