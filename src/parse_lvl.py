# this file handles parsing .lvls
# maps are 10x10
# bottom is (0, 0), top is (9, 9)
# right is (9, 0), left is (0, 9)
import struct
from typing import Any

# needed for finding ids
from . import parse_gon as gon

class Level:
    class Entry:
        x: int
        y: int
        id: int

        @staticmethod
        def structStr():
            return "<hhhH"

        def __init__(self, data: bytes):
            self.x, self.y, self.id, self.special = struct.unpack(self.structStr(), data)

        def __repr__(self):
            return f"({self.x}, {self.y}): {self.id}"

    spawnGon: str
    tileGon: str

    spawns: list[Entry]
    tiles: list[int] # 10x10 = 100 ids, index = y * width + x

    def __init__(self, data: bytes):
        offset = 0

        unknown1, unknown2, unknown3, unknown4, spawnCount = struct.unpack_from("<IIIII", data, offset)
        offset += 20

        assert(unknown1 == 2)

        # assuming this is related to width/height?
        assert(unknown2 == 10)
        assert(unknown3 == 10)

        assert(unknown4 == 1)

        unknown5, unknown6, unknown7, unknown8 = struct.unpack_from("<IIII", data, offset)
        offset += 16

        assert(unknown5 == 0)
        assert(unknown6 == 0)

        # assuming this is related to width/height?
        assert(unknown7 == 10)
        assert(unknown8 == 10)

        spawnGonLen = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        self.spawnGon = data[offset:offset+spawnGonLen].decode("utf-8")
        offset += spawnGonLen

        tileGonLen = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        self.tileGon = data[offset:offset+tileGonLen].decode("utf-8")
        offset += tileGonLen

        unknown9, unknown10 = struct.unpack_from("<II", data, offset)
        offset += 8

        assert(unknown9 == 0)
        assert(unknown10 == 0)

        self.tiles = []
        for y in range(10):
            for x in range(10):
                self.tiles.append(struct.unpack_from("<H", data, offset)[0])
                offset += 2 

        self.spawns = []
        sz = struct.calcsize(Level.Entry.structStr())
        for i in range(spawnCount):
            self.spawns.append(Level.Entry(data[offset:offset+sz]))
            offset += sz


class ResolvedLevel:
    class Entry:
        x: int
        y: int
        id: int

        def __init__(self, spawnGon, entry: Level.Entry):
            self.x = entry.x
            self.y = entry.y

            # 2 - 10 dont have spawns.gon entries but are mapped to 1
            self.id = entry.id if entry.id <= 1 or entry.id > 10 else 1

            self.data = spawnGon.get(str(self.id))
            if (self.data != None):
                self.data["variation"] = entry.special

                if (self.id != entry.id):
                    self.data["original_id"] = entry.id

        def __repr__(self):
            return f"({self.x}, {self.y}): {self.data}"

    spawns: list[Entry]
    tiles: list[tuple[int, str]] # 10x10 = 100 names, index = y * width + x

    def __init__(self, spawnGon, tilesGon, level: Level):
        self.spawns = []
        self.tiles = []

        for spawn in level.spawns:
            self.spawns.append(ResolvedLevel.Entry(spawnGon, spawn))

        for tile in level.tiles:
            self.tiles.append((tile, tilesGon.get(str(tile))))

    def get_unique_objects(self) -> dict[int, Any]:
        out = {}
        for obj in self.spawns:
            out[obj.id] = obj.data

        return out  

    def get_unique_tiles(self)-> dict[int, str]:
        out = {}
        for tile in self.tiles:
            out[tile[0]] = tile[1]  

        return out


def parse_lvl(filename: str) -> Level:
    with open(filename, "rb") as file:
        content = file.read()

    return Level(content)

spawnData = gon.parse_gon("./data/data/spawns.gon")
tileData = gon.parse_gon("./data/data/tiles.gon")

def parsed_lvl_resolved(filename: str, datadir: str = "./data/data") -> ResolvedLevel:
    lvl = parse_lvl(filename)

    if (lvl.spawnGon != "spawns.gon"):
        spawnGon = gon.parse_gon(datadir + "/" + lvl.spawnGon)
    else:
        spawnGon = spawnData

    if (lvl.tileGon != "tiles.gon"):
        tileGon = gon.parse_gon(datadir + "/" + lvl.tileGon)
    else:
        tileGon = tileData

    return ResolvedLevel(spawnGon, tileGon, lvl)
