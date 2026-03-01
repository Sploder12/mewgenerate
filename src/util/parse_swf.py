# this file handles parsing .swfs
# this is not meant to be a complete swf parser.
# see https://open-flash.github.io/mirrors/swf-spec-19.pdf for assistance

# twip = 1/20th of a pixel
# swf files are little-endian

import io
import math
import struct
from typing import Any

class bit_reader:
    stream: io.BytesIO
    buffer: int
    bits_left: int

    def __init__(self, data: bytes):
        self.stream = io.BytesIO(data)
        self.buffer = 0
        self.bits_left = 0

    def read_bits(self, n):
        if n == 0:
            return 0
        
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
        if n == 0:
            return 0

        # read n signed bits
        value = self.read_bits(n)
        sign_bit = 1 << (n - 1)
        if value & sign_bit:
            value -= (1 << n)

        return value

class Rect:
    # not in twips
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    def __init__(self):
        self.xmin = 0
        self.xmax = 0
        self.ymin = 0
        self.ymax = 0

class Matrix:
    # not in twips
    xoffset: float = 0 
    yoffset: float = 0

    xscale: float = 1.0
    yscale: float = 1.0

    skew1: float = 0.0
    skew2: float = 0.0

    def __init__(self):
        self.xoffset = 0.0
        self.yoffset = 0.0
        self.xscale = 1.0
        self.yscale = 1.0
        self.skew1 = 0.0
        self.skew2 = 0.0

    def transform(self, x: float, y: float):
        newX = x * self.xscale + y * self.skew2 + self.xoffset
        newY = x * self.skew1 + y * self.yscale + self.yoffset
        return (newX, newY)

class CXFORM:
    redMult: float = 1
    greenMult: float = 1
    blueMult: float = 1
    alphaMult: float = 1

    redAdd: int = 0
    greenAdd: int = 0
    blueAdd: int = 0
    alphaAdd: int = 0
    
    def __init__(self):
        self.redMult = 1.0
        self.greenMult = 1.0
        self.blueMult = 1.0
        self.alphaMult = 1.0

        self.redAdd = 0
        self.greenAdd = 0
        self.blueAdd = 0
        self.alphaAdd = 0

    def transform(self, r: float, g: float, b: float, a: float):
        nr = max(0.0, min(r * self.redMult + self.redAdd, 255.0))
        ng = max(0.0, min(g * self.greenMult + self.greenAdd, 255.0))
        nb = max(0.0, min(b * self.blueMult + self.blueAdd, 255.0))
        na = max(0.0, min(a * self.alphaMult + self.alphaAdd, 255.0))

        return (nr, ng, nb, na)

class SWF:
    SHOW_FRAME = 1
    DEFINE_SHAPE = 2
    DEFINE_SHAPE2 = 22
    DEFINE_SHAPE3 = 32
    DEFINE_SHAPE4 = 83
    DEFINE_SHAPE_SET = {DEFINE_SHAPE, DEFINE_SHAPE2, DEFINE_SHAPE3, DEFINE_SHAPE4}

    DEFINE_TEXT = 11

    PLACE_OBJECT2 = 26
    REMOVE_OBJECT2 = 28
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
                case SWF.DEFINE_SHAPE:
                    return "DefineShape"
                case 4:
                    return "PlaceObject"
                case 5:
                    return "RemoveObject"
                case 9:
                    return "SetBackgroundColor"
                case SWF.DEFINE_TEXT:
                    return "DefineText"
                
                case SWF.DEFINE_SHAPE2:
                    return "DefineShape2"
                case SWF.PLACE_OBJECT2:
                    return "PlaceObject2"
                case SWF.REMOVE_OBJECT2:
                    return "RemoveObject2"
                case SWF.DEFINE_SHAPE3:
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
                case SWF.DEFINE_SHAPE4:
                    return "DefineShape4"
            
            return "Unknown"

    @staticmethod
    def parseRECT(buffer: bytes, offset: int) -> tuple[Rect, int]:
        reader = bit_reader(buffer[offset:])

        out = Rect()

        nbits = reader.read_bits(5)
        out.xmin = reader.read_signed_bits(nbits) / 20.0
        out.xmax = reader.read_signed_bits(nbits) / 20.0
        out.ymin = reader.read_signed_bits(nbits) / 20.0
        out.ymax = reader.read_signed_bits(nbits) / 20.0

        byteCount = math.ceil((5.0 + nbits * 4.0) / 8.0)
        return (out, byteCount)

    @staticmethod
    def parseMATRIX(buffer: bytes, offset: int) -> tuple[Matrix, int]:
        out = Matrix()

        bits = 0
        bitReader = bit_reader(buffer[offset:])

        hasScale = bitReader.read_bits(1) == 1
        bits += 1

        if (hasScale):
            nbits = bitReader.read_bits(5)
            sxbits = bitReader.read_signed_bits(nbits)
            sybits = bitReader.read_signed_bits(nbits)
            bits += 5 + nbits * 2

            out.xscale = sxbits / 65536.0
            out.yscale = sybits / 65536.0


        hasRotate = bitReader.read_bits(1) == 1
        bits += 1

        if (hasRotate):
            nbits = bitReader.read_bits(5)
            rs1bits = bitReader.read_signed_bits(nbits)
            rs2bits = bitReader.read_signed_bits(nbits)
            bits += 5 + nbits * 2

            out.skew1 = rs1bits / 65536.0
            out.skew2 = rs2bits / 65536.0

        nBits = bitReader.read_bits(5)
        out.xoffset = bitReader.read_signed_bits(nBits) / 20.0
        out.yoffset = bitReader.read_signed_bits(nBits) / 20.0
        bits += 5 + nBits * 2

        return (out, math.ceil(bits / 8.0))
    
    @staticmethod
    def parseCXFORMWITHALPHA(buffer: bytes, offset: int) -> tuple[CXFORM, int]:
        out = CXFORM()

        bits = 0
        bitReader = bit_reader(buffer[offset:])

        hasAdd = bitReader.read_bits(1) == 1
        hasMult = bitReader.read_bits(1) == 1
        nbits = bitReader.read_bits(4)
        bits += 6

        if hasMult:
            out.redMult = bitReader.read_signed_bits(nbits) / 256.0
            out.greenMult = bitReader.read_signed_bits(nbits) / 256.0
            out.blueMult = bitReader.read_signed_bits(nbits) / 256.0
            out.alphaMult = bitReader.read_signed_bits(nbits) / 256.0

            bits += nbits * 4

        if hasAdd:
            out.redAdd = bitReader.read_signed_bits(nbits)
            out.greenAdd = bitReader.read_signed_bits(nbits)
            out.blueAdd = bitReader.read_signed_bits(nbits)
            out.alphaAdd = bitReader.read_signed_bits(nbits)

            bits += nbits * 4

        return (out, math.ceil(bits / 8.0))

    @staticmethod
    def parseSTRING(buffer: bytes, offset: int) -> tuple[str, int]:
        i = 0
        while i + offset < len(buffer):
            if (buffer[i] == 0):
                return (buffer[offset: offset + i].decode("utf-8"), i + 1)

            i += 1 

        raise RuntimeError("Failed to parse SWF STRING")



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

    
class DefineShape:
    id: int
    bounds: Rect
    # shapes is ignored cause not needed

    def __init__(self, tag: SWF.Tag):
        if (tag.type not in SWF.DEFINE_SHAPE_SET):
            raise TypeError("tag is not a DefineShape tag")
        
        self.id = struct.unpack_from("<H", tag.data, 0)[0]
        offset = 2

        self.bounds, o = SWF.parseRECT(tag.data, offset)
        offset += o

        # Shapes

class DefineText:
    id: int
    bounds: Rect
    matrix: Matrix

    def __init__(self, tag: SWF.Tag):
        if (tag.type != SWF.DEFINE_TEXT):
            raise TypeError("tag is not a DefineText tag")
        
        self.id = struct.unpack_from("<H", tag.data, 0)[0]
        offset = 2

        self.bounds, o = SWF.parseRECT(tag.data, offset)
        offset += o

        self.matrix, o = SWF.parseMATRIX(tag.data, offset)
        offset += o
        
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
    matrix: Matrix | None
    cxform: CXFORM | None
    ratio: int | None
    name: str | None
    clipdepth: int | None
    move: bool

    def __init__(self, tag: SWF.Tag):
        if (tag.type != SWF.PLACE_OBJECT2):
            raise TypeError("tag is not a PlaceObject2 tag")
        
        flags = struct.unpack_from("<B", tag.data)[0]
        offset = 1

        self.move = (flags & 0b00000001) > 0

        self.depth = struct.unpack_from("<H", tag.data, offset)[0]
        offset += 2

        self.character = None
        if flags & 0b00000010 > 0: # HasCharacter
            self.character = struct.unpack_from("<H", tag.data, offset)[0]
            offset += 2

        self.matrix = None
        if flags & 0b00000100 > 0: # HasMatrix
            self.matrix, o = SWF.parseMATRIX(tag.data, offset)
            offset += o

        self.cxform = None
        if flags & 0b00001000 > 0: # HasColorTransform
            self.cxform, o = SWF.parseCXFORMWITHALPHA(tag.data, offset)
            offset += o

        self.ratio = None
        if flags & 0b00010000 > 0: # HasRatio
            self.ratio = struct.unpack_from("<H", tag.data, offset)[0]
            offset += 2

        self.name = None
        if flags & 0b00100000 > 0: # HasName
            self.name, o = SWF.parseSTRING(tag.data, offset)
            offset += o

        self.clipdepth = None
        if flags & 0b01000000 > 0: # HasClipDepth
            self.clipdepth = struct.unpack_from("<H", tag.data, offset)[0]
            if (self.clipdepth == 0):
                self.clipdepth = None
            offset += 2

        # ignoring clipactions because it scares me. (and is not needed for our uses)

class RemoveObject2:
    depth: int

    def __init__(self, tag: SWF.Tag):
        if (tag.type != SWF.REMOVE_OBJECT2):
            raise TypeError("tag is not a RemoveObject2 tag")

        self.depth = struct.unpack("<H", tag.data)[0]

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

def getAllSprites(tags: SWF) -> dict[int, DefineSprite]:
    allSprites = {}

    for tag in tags.tags:
        if (tag.type == SWF.DEFINE_SPRITE):
            dsprite = DefineSprite(tag)
            allSprites[dsprite.id] = dsprite

    return allSprites

def getAllShapes(tags: SWF) -> dict[int, DefineShape]:
    allShapes = {}

    for tag in tags.tags:
        if (tag.type in SWF.DEFINE_SHAPE_SET):
            dshape = DefineShape(tag)
            allShapes[dshape.id] = dshape

    return allShapes

def getCharacterDict(tags: SWF) -> dict[int, Any]:
    charDict = {}

    for tag in tags.tags:
        if (tag.type in SWF.DEFINE_SHAPE_SET):
            dshape = DefineShape(tag)
            charDict[dshape.id] = dshape
        
        elif (tag.type == SWF.DEFINE_SPRITE):
            dsprite = DefineSprite(tag)
            charDict[dsprite.id] = dsprite

        elif (tag.type == SWF.DEFINE_TEXT):
            dtext = DefineText(tag)
            charDict[dtext.id] = dtext

    return charDict

def getSymbolTable(tags: SWF) -> dict[str, int]:
    symbolTable = {}
    for tag in tags.tags:
        if (tag.type == SWF.SYMBOL_CLASS):
            sclass = SymbolClass(tag)
            for symbol in sclass.symbols:
                symbolTable[symbol[1]] = symbol[0]

    return symbolTable


class Frame:
    name: str = ""
    tags: list[SWF.Tag]

    def __init__(self):
        self.name = ""
        self.tags = []


# useful for abilities and passives
# but not furniture, furniture uses a 2nd indirection
def splitSpriteFrames(sprite: DefineSprite) -> list[Frame]:
    out = []

    curFrame = Frame()
    for frame in sprite.tags:
        match frame.type:
            case SWF.FRAME_LABEL:
                curFrame.name = FrameLabel(frame).label

            case SWF.SHOW_FRAME:
                out.append(curFrame)
                curFrame = Frame()
            case _:
                curFrame.tags.append(frame)

    return out