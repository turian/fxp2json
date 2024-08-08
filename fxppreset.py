import json
import struct
from typing import ByteString, List

import pytinyxml2 as tinyxml2
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
        print(self.xmlContent)
        open("1.xml", "w").write(self.xmlContent)
        self.wavetables: List[ByteString] = wavetables

        # Parse XML and convert to JSON
        json_str = xml_to_json(self.xmlContent)
        xml_str = json_to_xml(json_str)
        open("2.xml", "w").write(xml_str)
        assert xml_str == self.xmlContent, "XML to JSON to XML conversion failed"

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

            print("chunkSize", chunkSize)
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
    fxp = FXP.load(
        "/Library/Application Support/Surge XT/patches_3rdparty/Rare Earth/Basses/Bass Tuba.fxp"
    )
    fxp.save("tmp/test.fxp")
    assert (
        open("tmp/test.fxp", "rb").read()
        == open(
            "/Library/Application Support/Surge XT/patches_3rdparty/Rare Earth/Basses/Bass Tuba.fxp",
            "rb",
        ).read()
    )
    fxp2 = FXP.load("tmp/test.fxp")
