import struct
import pytinyxml2 as xml

import struct

import struct
from typing import List, ByteString
from typeguard import typechecked

class FXP:
    @typechecked
    def __init__(self, chunkmagic: bytes, byteSize: int, fxMagic: bytes, version: int, fxId: int, fxVersion: int, numPrograms: int, 
                 prgName: str,
                 #prgName: bytes,
                 chunkSize: int, xmlContent: str, wavetables: List[ByteString]):
        assert len(prgName.encode('utf-8')) <= 28, "Program name must be at most 28 bytes long"

        self.chunkmagic: bytes = chunkmagic
        assert self.chunkmagic == b'CcnK', "Chunk magic must be 'CcnK'"
        self.byteSize: int = byteSize
        #assert self.byteSize == len(xmlContent.encode("utf-8")) + 28, f"Byte size must be {len(xmlContent.encode("utf-8")) + 28}, but is {self.byteSize}"
        self.fxMagic: bytes = fxMagic
        assert self.fxMagic == b'FPCh', "FX magic must be 'FPCh'"
        self.version: int = version
        self.fxId: int = fxId
        self.fxVersion: int = fxVersion
        self.numPrograms: int = numPrograms
        self.prgName: str = prgName
        #self.prgName: bytes = prgName
        self.chunkSize: int = chunkSize
        self.xmlContent: str = xmlContent
        print(self.xmlContent)
        self.wavetables: List[ByteString] = wavetables

    @typechecked
    def save(self, filename: str) -> None:
        fxp_header: ByteString = struct.pack(
            ">4si4siiii28si",
            self.chunkmagic, #b'CcnK',
            self.byteSize, #len(self.xmlContent) + 28,
            self.fxMagic, # b'FPCh',
            self.version,
            self.fxId,
            self.fxVersion,
            self.numPrograms,
            self.prgName.encode('utf-8'),
            #self.prgName,
            len(self.xmlContent)
        )

        assert len(fxp_header) == 60, "FXP header size must be 60 bytes"

        wavetable_data: ByteString = b''.join(self.wavetables)

        with open(filename, 'wb') as f:
            f.write(fxp_header)
            f.write(self.xmlContent.encode('utf-8'))
            f.write(wavetable_data)

    @staticmethod
    @typechecked
    def load(filename: str) -> "FXP":
        with open(filename, 'rb') as f:
            patch_content = f.read()
            fxp_header: ByteString = patch_content[:60] # f.read(60)
            assert len(fxp_header) == 60, "FXP header size must be 60 bytes"

            chunkmagic, byteSize, fxMagic, version, fxId, fxVersion, numPrograms, prgName, chunkSize = struct.unpack(
                ">4si4siiii28si", fxp_header)

            print("chunkSize", chunkSize)
            patch_header: ByteString = patch_content[60:92] # f.read(32)
            patch_header_unpack = struct.unpack("<4siiiiiii", patch_header)
            print(patch_header_unpack)
            xml_size = patch_header_unpack[1]
            print("xml_size", xml_size)

            """
            for i in range(len(patch_content)):
                try:
                    patch_content[92:92+i].decode("utf-8")
                    print(i)
                except:
                    break
            print(patch_content[92:92+i-1].decode("utf-8"))
            """

            #xml_content: ByteString = f.read(chunkSize)
            xml_content: ByteString = patch_content[92:92+xml_size] # f.read(xml_size)
            wavetables: ByteString = patch_content[92+xml_size:] # f.read()

            assert len(prgName.strip(b'\x00')) <= 28, "Program name must be at most 28 bytes long"

        return FXP(chunkmagic, byteSize, fxMagic,version, fxId, fxVersion, numPrograms,
                   #prgName,
                   prgName.strip(b'\x00').decode('utf-8'), 
                   chunkSize, xml_content.decode('utf-8'), [wavetables])


if __name__ == "__main__":
    fxp = FXP.load("/Library/Application Support/Surge XT/patches_3rdparty/Rare Earth/Basses/Bass Tuba.fxp")
    fxp.save("tmp/test.fxp")
    assert open("tmp/test.fxp", "rb").read() == open("/Library/Application Support/Surge XT/patches_3rdparty/Rare Earth/Basses/Bass Tuba.fxp", "rb").read()
    fxp2 = FXP.load("tmp/test.fxp")