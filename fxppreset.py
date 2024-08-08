import glob
import json
import re
import struct
from typing import Any, ByteString, Dict, List

from lxml import etree
from tqdm import tqdm
from typeguard import typechecked

# TODO: FXPHeader


@typechecked
class PatchHeader:
    # TODO: Check each field is correctly named
    def __init__(
        self,
        patchmagic: bytes,
        xmlSize: int,
        version: int,
        numWavetables: int,
        numSamples: int,
        numZones: int,
        numModMatrix: int,
        numModMatrixRows: int,
    ):
        self.patchmagic: bytes = patchmagic
        # assert self.patchmagic == b'cTfx', "Patch magic must be 'cTfx'"
        self.xmlSize: int = xmlSize
        self.version: int = version
        self.numWavetables: int = numWavetables
        self.numSamples: int = numSamples
        self.numZones: int = numZones
        self.numModMatrix: int = numModMatrix
        self.numModMatrixRows: int = numModMatrixRows

    @property
    def to_bytes(self) -> bytes:
        b = struct.pack(
            "<4siiiiiii",
            self.patchmagic,
            self.xmlSize,
            self.version,
            self.numWavetables,
            self.numSamples,
            self.numZones,
            self.numModMatrix,
            self.numModMatrixRows,
        )
        assert len(b) == 32, "Patch header size must be 32 bytes"
        return b


def convert_xml_declaration_quotes(xml_string: str) -> str:
    # Define the regex pattern to match the XML declaration
    pattern = r"(<\?xml[^>]*\?>)"

    # Function to replace " with ' in the matched XML declaration
    def replace_quotes(match):
        return match.group(0).replace("'", '"')

    # Use re.sub with the pattern and replacement function
    result = re.sub(pattern, replace_quotes, xml_string)

    return result


def handle_special_characters(xml_str: str) -> str:
    # Replace specific characters with their XML entities
    xml_str = xml_str.replace("&#13;", "&#x0D;")
    xml_str = xml_str.replace("&#10;", "&#x0A;")
    return xml_str


def xml_to_json(xml_str: str) -> str:
    xml_bytes = xml_str.encode("utf-8")  # Convert string to bytes
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.XML(xml_bytes, parser)

    def _element_to_dict(element):
        elem_dict = {element.tag: {}}
        # Add attributes if present
        if element.attrib:
            elem_dict[element.tag]["@attributes"] = dict(element.attrib)
        # Add text if present
        if element.text and element.text.strip():
            elem_dict[element.tag]["#text"] = element.text.strip()
        # Add children if present
        children = list(element)
        if children:
            child_dict = {}
            for child in children:
                child_elem_dict = _element_to_dict(child)
                for key, value in child_elem_dict.items():
                    if key not in child_dict:
                        child_dict[key] = []
                    child_dict[key].append(value)
            elem_dict[element.tag]["children"] = child_dict
        return elem_dict

    return json.dumps(_element_to_dict(root), indent=4)


def json_to_xml(json_str: str) -> str:
    def _dict_to_element(parent, dict_obj):
        for tag, content in dict_obj.items():
            if tag == "@attributes":
                for key, value in content.items():
                    parent.set(key, value)
            elif tag == "#text":
                parent.text = content
            elif tag == "children":
                for child_tag, child_list in content.items():
                    for child_content in child_list:
                        element = etree.SubElement(parent, child_tag)
                        _dict_to_element(element, child_content)
            else:
                element = etree.SubElement(parent, tag)
                _dict_to_element(element, content)

    json_obj = json.loads(json_str)
    root_tag = list(json_obj.keys())[0]
    root = etree.Element(root_tag)
    _dict_to_element(root, json_obj[root_tag])

    xml_bytes = etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    xml_str = xml_bytes.decode("utf-8")
    # Add space before the trailing slash for self-closing tags
    xml_str = xml_str.replace("/>", " />")
    xml_str = xml_str.replace("?>", " ?>")
    xml_str = xml_str.replace("\n", "")
    xml_str = convert_xml_declaration_quotes(xml_str)
    xml_str = handle_special_characters(xml_str)
    return xml_str


@typechecked
class FXP:
    def __init__(
        self,
        chunkmagic: bytes,
        byteSize: int,
        fxMagic: bytes,
        version: int,
        fxId: int,
        fxVersion: int,
        numPrograms: int,
        prgName: str,
        # prgName: bytes,
        chunkSize: int,
        patchHeader: PatchHeader,
        xmlContent: str,
        # xmlContent: bytes,
        wavetables: List[ByteString],
    ):
        assert (
            len(prgName.encode("utf-8")) <= 28
        ), "Program name must be at most 28 bytes long"

        self.chunkmagic: bytes = chunkmagic
        assert self.chunkmagic == b"CcnK", "Chunk magic must be 'CcnK'"
        self.byteSize: int = byteSize
        # assert self.byteSize == len(xmlContent.encode("utf-8")) + 28, f"Byte size must be {len(xmlContent.encode("utf-8")) + 28}, but is {self.byteSize}"
        self.fxMagic: bytes = fxMagic
        assert self.fxMagic == b"FPCh", "FX magic must be 'FPCh'"
        self.version: int = version
        self.fxId: int = fxId
        self.fxVersion: int = fxVersion
        self.numPrograms: int = numPrograms
        self.prgName: str = prgName
        # self.prgName: bytes = prgName
        self.chunkSize: int = chunkSize
        self.patchHeader: PatchHeader = patchHeader
        self.xmlContent: str = xmlContent
        # self.xmlContent: bytes = xmlContent
        # print(self.xmlContent)
        open("1.xml", "w").write(self.xmlContent)
        self.wavetables: List[ByteString] = wavetables

        # Parse XML and convert to JSON
        json_output = xml_to_json(self.xmlContent)
        xml_output = json_to_xml(json_output)
        open("2.xml", "w").write(xml_output)
        # < <meta name="Kalimba Attempt" category="Rare Earth\Percussion" comment='Based on the &quot;Drum One&quot; preset.' author="Leonard Bowman" />
        # < <meta name="SY 80&apos;s Future Key WT" category="Emu/Synth" comment="" author="The Emu" />
        assert xml_output == self.xmlContent.replace("'", '"').replace('&apos;', "'"), "XML to JSON to XML conversion failed"
        #assert xml_output == self.xmlContent, "XML to JSON to XML conversion failed"

    def save(self, filename: str) -> None:
        fxp_header: ByteString = struct.pack(
            ">4si4siiii28si",
            self.chunkmagic,  # b'CcnK',
            self.byteSize,  # len(self.xmlContent) + 28,
            self.fxMagic,  # b'FPCh',
            self.version,
            self.fxId,
            self.fxVersion,
            self.numPrograms,
            self.prgName.encode("utf-8"),
            # self.prgName,
            self.chunkSize,
        )

        assert len(fxp_header) == 60, "FXP header size must be 60 bytes"

        wavetable_data: ByteString = b"".join(self.wavetables)

        with open(filename, "wb") as f:
            f.write(fxp_header)
            f.write(self.patchHeader.to_bytes)
            f.write(self.xmlContent.encode("utf-8"))
            # f.write(self.xmlContent)
            f.write(wavetable_data)

    @staticmethod
    def load(filename: str) -> "FXP":
        with open(filename, "rb") as f:
            patch_content = f.read()
            fxp_header: ByteString = patch_content[:60]  # f.read(60)
            assert len(fxp_header) == 60, "FXP header size must be 60 bytes"

            (
                chunkmagic,
                byteSize,
                fxMagic,
                version,
                fxId,
                fxVersion,
                numPrograms,
                prgName,
                chunkSize,
            ) = struct.unpack(">4si4siiii28si", fxp_header)

            # print("chunkSize", chunkSize)
            patch_header_bytes: ByteString = patch_content[60:92]  # f.read(32)
            patch_header_unpack = struct.unpack("<4siiiiiii", patch_header_bytes)
            patchHeader = PatchHeader(*patch_header_unpack)

            # xml_content: ByteString = f.read(chunkSize)
            xml_content: ByteString = patch_content[
                92 : 92 + patchHeader.xmlSize
            ]  # f.read(xml_size)
            wavetables: ByteString = patch_content[
                92 + patchHeader.xmlSize :
            ]  # f.read()

            assert (
                len(prgName.strip(b"\x00")) <= 28
            ), "Program name must be at most 28 bytes long"

        return FXP(
            chunkmagic,
            byteSize,
            fxMagic,
            version,
            fxId,
            fxVersion,
            numPrograms,
            # prgName,
            prgName.strip(b"\x00").decode("utf-8"),
            chunkSize,
            patchHeader,
            # xml_content,
            xml_content.decode("utf-8"),
            [wavetables],
        )


if __name__ == "__main__":
    fxp_files = list(
        glob.glob("/Library/Application Support/Surge XT/**/*.fxp", recursive=True)
    )
    for fxp_file in tqdm(fxp_files):
        fxp = FXP.load(fxp_file)
        fxp.save("tmp/test.fxp")
        # fxp2 = FXP.load(f"{fxp_file}.tmp")
        # assert fxp.__dict__ == fxp2.__dict__

        assert (
            open("tmp/test.fxp", "rb").read()
            == open(
                fxp_file,
                "rb",
            ).read()
        )
