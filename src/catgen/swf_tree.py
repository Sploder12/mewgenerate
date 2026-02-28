from ..util import parse_swf as swf

import copy

class PlacedObject:
        id: int
        name: str
        xform: swf.Matrix | None
        cxform: swf.CXFORM | None
        depth: int
        clipDepth: int | None

        def __init__(self, po2: swf.PlaceObject2):
            self.id = po2.character
            self.name = "" if po2.name == None else po2.name
            self.xform = po2.matrix
            self.cxform = po2.cxform
            self.depth = po2.depth
            self.clipDepth = po2.clipdepth

class Frame:
        name: str = ""
        objs: list[PlacedObject]

        def __init__(self, name: str = ""):
            self.name = name
            self.objs = []

        def add(self, obj: PlacedObject):
            for i in range(len(self.objs)):
                o = self.objs[i]
                if obj.depth == o.depth:
                    self.objs[i] = obj
                    return

            self.objs.append(obj)

        def remove(self, depth: int):
            self.objs = [obj for obj in self.objs if obj.depth != depth]

class SWF_Tree:
    class ShapeNode:
        name: str = ""
        id: int

        def __init__(self, id: int, name: str = ""):
            self.name = name
            self.id = id

    class SpriteNode:
        name: str = ""
        frames: list[Frame]

        def __init__(self, name: str = ""):
            self.name = name
            self.frames = []

    symbolTable: dict[str, int]
    isymbTab: dict[int, str]
    characterLUT: dict[int, ShapeNode | SpriteNode]

    def __init__(self, symbTab: dict[str, int]):
        self.symbolTable = symbTab
        self.isymbTab = {value: key for key, value in symbTab.items()}
        self.characterLUT = {}

    def addSprite(self, sprite: swf.DefineSprite):
        if (sprite.id in self.characterLUT):
            return

        node = self.SpriteNode("" if sprite.id not in self.isymbTab else self.isymbTab[sprite.id])
        frames = swf.splitSpriteFrames(sprite)

        displist = Frame()
        for frame in frames:
            displist.name = frame.name

            for tag in frame.tags:
                if (tag.type == swf.SWF.PLACE_OBJECT2):
                    po2 = PlacedObject(swf.PlaceObject2(tag))
                    displist.add(po2)
                
                elif (tag.type == swf.SWF.REMOVE_OBJECT2):
                    ro2 = swf.RemoveObject2(tag)
                    displist.remove(ro2.depth)

            node.frames.append(copy.deepcopy(displist))

        self.characterLUT[sprite.id] = node

    def addShape(self, shape: swf.DefineShape):
        if (shape.id in self.characterLUT):
            return

        node = self.ShapeNode(shape.id, "" if shape.id not in self.isymbTab else self.isymbTab[shape.id])
        self.characterLUT[shape.id] = node
        
    def get(self, id: int | str) -> ShapeNode | SpriteNode | None:
        if isinstance(id, str):
            if id not in self.symbolTable:
                return None

            id = self.symbolTable[id]

        if id not in self.characterLUT:
            return None

        return self.characterLUT[id]

def swfToTree(flash: swf.SWF) -> SWF_Tree:
    out = SWF_Tree(swf.getSymbolTable(flash))

    for tag in flash.tags:
        if (tag.type == swf.SWF.DEFINE_SPRITE):
            dsprite = swf.DefineSprite(tag)

            if (dsprite.id == 4437):
                pass

            out.addSprite(dsprite)

        if (tag.type in swf.SWF.DEFINE_SHAPE_SET):
            out.addShape(swf.DefineShape(tag))

    return out

