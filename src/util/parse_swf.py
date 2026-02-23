# this file handles parsing .swfs
# this is not meant to be a complete swf parser.
# see https://open-flash.github.io/mirrors/swf-spec-19.pdf for assistance

# twip = 1/20th of a pixel
# swf files are little-endian

import io
import math
import struct

class bit_reader:
    stream: io.BytesIO
    buffer: int
    bits_left: int

    def __init__(self, data: bytes):
        self.stream = io.BytesIO(data)
        self.buffer = 0
        self.bits_left = 0

    def read_bits(self, n):
        # read n unsigned bits
        result = 0
        while n > 0:
            if self.bits_left == 0:
                byte = self.stream.read(1)
                if not byte:
                    raise EOFError("Unexpected end of SWF file")
                
                self.buffer = byte[0]
                self.bits_left = 8

            take = min(n, self.bits_left)
            result <<= take
            shift = self.bits_left - take
            result |= (self.buffer >> shift) & ((1 << take) - 1)

            self.bits_left -= take
            self.buffer &= (1 << self.bits_left) - 1
            n -= take

        return result

    def read_signed_bits(self, n):
        # read n signed bits
        value = self.read_bits(n)
        sign_bit = 1 << (n - 1)
        if value & sign_bit:
            value -= (1 << n)

        return value

class Rect:
    # measured in twips
    xmin: int
    xmax: int
    ymin: int
    ymax: int

    def __init__(self):
        self.xmin = 0
        self.xmax = 0
        self.ymin = 0
        self.ymax = 0

class SWF:
    SHOW_FRAME = 1
    PLACE_OBJECT2 = 26
    DEFINE_SPRITE = 39
    FRAME_LABEL = 43
    SYMBOL_CLASS = 76

    class Header:
        compression: str
        version: int
        fileLength: int
        frameSize: Rect
        frameRate: int
        frameCount: int

        def __init__(self):
            self.compression = "F"
            self.version = 0
            self.fileLength = 0
            self.frameSize = Rect()
            self.frameRate = 0
            self.frameCount = 0

    class Tag:
        type: int
        length: int
        data: bytes

        def __init__(self):
            self.type = 0
            self.length = 0
            self.data = bytes()

        def type_to_string(self):
            match (self.type):
                case SWF.SHOW_FRAME:
                    return "ShowFrame"
                case 2:
                    return "DefineShape"
                case 4:
                    return "PlaceObject"
                case 5:
                    return "RemoveObject"
                case 9:
                    return "SetBackgroundColor"
                
                case 22:
                    return "DefineShape2"
                case SWF.PLACE_OBJECT2:
                    return "PlaceObject2"
                case 28:
                    return "RemoveObject2"
                case 32:
                    return "DefineShape3"

                case SWF.DEFINE_SPRITE:
                    return "DefineSprite"
                
                case SWF.FRAME_LABEL:
                    return "FrameLabel"    
                
                case 69:
                    return "FileAttributes"
                case 70:
                    return "PlaceObject3"
                case SWF.SYMBOL_CLASS:
                    return "SymbolClass"
                case 82:
                    return "DoABC"
                case 83:
                    return "DefineShape4"
            
            return "Unknown"

    @staticmethod
    def parseRECT(buffer: bytes, offset: int) -> tuple[Rect, int]:
        reader = bit_reader(buffer[offset:])

        out = Rect()

        nbits = reader.read_bits(5)
        out.xmin = reader.read_signed_bits(nbits)
        out.xmax = reader.read_signed_bits(nbits)
        out.ymin = reader.read_signed_bits(nbits)
        out.ymax = reader.read_signed_bits(nbits)

        byteCount = math.ceil((5.0 + nbits * 4.0) / 8.0)
        return (out, byteCount)

    @staticmethod
    def parseHeader(buffer: bytes, offset: int) -> tuple[Header, int]:
        out = SWF.Header()

        prelude = struct.unpack_from("<BBBBI", buffer, offset)
        
        out.compression = chr(prelude[0])
        if (chr(prelude[1]) != 'W' or chr(prelude[2]) != 'S'):
            raise RuntimeError("not a valid SWF file")
        
        if (out.compression != 'F'):
            raise RuntimeError("compressed SWF files are not supported")
        
        out.version = prelude[3]
        out.fileLength = prelude[4]

        out.frameSize, count = SWF.parseRECT(buffer, offset + 8)
        offset += 8 + count

        # @TODO convert framerate from 8.8 fixed to a usable type
        frameData = struct.unpack_from("<HH", buffer, offset)
        out.frameRate = frameData[0]
        out.frameCount = frameData[1]

        return (out, 8 + count + 4)
    
    @staticmethod
    def parseTag(buffer: bytes, offset: int) -> tuple[Tag, int]:
        typelen = struct.unpack_from("<H", buffer, offset)[0]

        out = SWF.Tag()
        size = 2

        out.type = (typelen & 0b1111111111000000) >> 6
        out.length = typelen & 0b0000000000111111

        if (out.length == 0x3f):
            out.length = struct.unpack_from("<I", buffer, offset + 2)[0]
            size += 4

        out.data = buffer[offset + size:offset + size + out.length:]

        return (out, size + out.length)


    header: Header
    tags: list[Tag]

    def __init__(self, buffer: bytes):
        self.header, offset = SWF.parseHeader(buffer, 0)
        self.tags = []
        
        while (offset < len(buffer)):
            tag, count = SWF.parseTag(buffer, offset)
            assert(count != 0)

            self.tags.append(tag)
            offset += count

    
class DefineSprite:
    id: int
    frames: int
    tags: list[SWF.Tag]

    def __init__(self, tag: SWF.Tag):
        if (tag.type != SWF.DEFINE_SPRITE):
            raise TypeError("tag is not a DefineSprite tag")
        
        self.id, self.frames = struct.unpack_from("<HH", tag.data, 0)
        self.tags = []

        offset = 4
        while (offset < len(tag.data)):
            newtag, count = SWF.parseTag(tag.data, offset)
            assert(count != 0)

            self.tags.append(newtag)
            offset += count

            if (newtag.type == 0):
                break

class PlaceObject2:
    depth: int
    character: int | None

    def __init__(self, tag: SWF.Tag):
        if (tag.type != SWF.PLACE_OBJECT2):
            raise TypeError("tag is not a PlaceObject2 tag")
        
        flags = struct.unpack_from("<B", tag.data)[0]
        offset = 1

        self.depth = struct.unpack_from("<H", tag.data, offset)[0]
        offset += 2

        self.character = None
        if flags & 0b00000010 > 0:
            self.character = struct.unpack_from("<H", tag.data, offset)[0]
            offset += 2

        # ignoring matrix and whatnot because it scares me. (and is not needed for our uses)

class FrameLabel:
    label: str

    def __init__(self, tag: SWF.Tag):
        if (tag.type != SWF.FRAME_LABEL):
            raise TypeError("tag is not a FrameLabel tag")

        self.label = tag.data[:-1].decode("utf-8")

class SymbolClass:
    symbols: list[tuple[int, str]]

    def __init__(self, tag: SWF.Tag):
        if (tag.type != SWF.SYMBOL_CLASS):
            raise TypeError("tag is not a SymbolClass tag")
        
        self.symbols = []
        
        count = struct.unpack_from("<H", tag.data)[0]
        offset = 2

        for _ in range(count):
            id = struct.unpack_from("<H", tag.data, offset)[0]
            offset += 2

            start = offset
            while (tag.data[offset] != 0):
                offset += 1

            name = tag.data[start:offset].decode("utf-8")
            offset += 1
            
            self.symbols.append((id, name))


def parse_swf(filename: str) -> SWF:
    with open(filename, "rb") as file:
        content = file.read()

    return SWF(content)
