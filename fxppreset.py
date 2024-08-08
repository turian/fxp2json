import json
import struct
from typing import ByteString, List

from typeguard import typechecked

import pytinyxml2_json
import xmltodict_json

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


def compare_json(json1, json2):
    dict1 = json.loads(json1)
    dict2 = json.loads(json2)
    return dict1 == dict2


# TODO: Also try lxml
@typechecked
def verify_xml(xml_str: str) -> None:
    open("1.xml", "wt").write(xml_str)
    json_str_tinyxml2 = pytinyxml2_json.xml_to_json(xml_str)
    json_str_xmltodict = xmltodict_json.xml_to_json(xml_str)

    open("tinyxml2.json", "wt").write(json.dumps(json.loads(json_str_tinyxml2), indent=4))
    open("xmltodict.json", "wt").write(json.dumps(json.loads(json_str_xmltodict), indent=4))
    assert compare_json(json_str_tinyxml2, json_str_xmltodict), "JSON strings differ"

    # TODO: Other variations?
    xml_str_tinyxml2_json_str_tinyxml2 = pytinyxml2_json.json_to_xml(json_str_tinyxml2)
    xml_str_xmltodict_json_str_tinyxml2 = xmltodict_json.json_to_xml(json_str_tinyxml2)

    json_str_tinyxml2_xml_str_tinyxml2 = pytinyxml2_json.xml_to_json(
        xml_str_tinyxml2_json_str_tinyxml2
    )
    json_str_xmltodict_xml_str_tinyxml2 = xmltodict_json.xml_to_json(
        xml_str_xmltodict_json_str_tinyxml2
    )
    json_str_tinyxml2_xml_str_xmltodict = pytinyxml2_json.xml_to_json(
        xml_str_tinyxml2_json_str_tinyxml2
    )
    json_str_xmltodict_xml_str_xmltodict = xmltodict_json.xml_to_json(
        xml_str_xmltodict_json_str_tinyxml2
    )

    assert compare_json(
        json_str_tinyxml2, json_str_tinyxml2_xml_str_tinyxml2
    ), "JSON strings differ"
    assert compare_json(
        json_str_tinyxml2, json_str_xmltodict_xml_str_tinyxml2
    ), "JSON strings differ"
    assert compare_json(
        json_str_tinyxml2, json_str_tinyxml2_xml_str_xmltodict
    ), "JSON strings differ"
    assert compare_json(
        json_str_tinyxml2, json_str_xmltodict_xml_str_xmltodict
    ), "JSON strings differ"


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

        """
        # self.xmlContent: bytes = xmlContent
        print(self.xmlContent)
        open("1.xml", "w").write(self.xmlContent)
        self.wavetables: List[ByteString] = wavetables

        # Parse XML and convert to JSON
        json_str = xml_to_json(self.xmlContent)
        xml_str = json_to_xml(json_str)
        open("2.xml", "w").write(xml_str)
        assert xml_str == self.xmlContent, "XML to JSON to XML conversion failed"
        """

        verify_xml(self.xmlContent)

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
