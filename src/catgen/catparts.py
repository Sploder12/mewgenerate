from . import swf_tree as swf
from . import sprite as sprite
from . import palette

from ..util import ffdec_tools as ffdec

CATPARTS_SWF = "./data/swfs/catparts.swf"

class HeadPlacements:
    head: swf.PlacedObject

    lear: swf.PlacedObject | None
    rear: swf.PlacedObject | None

    leye: swf.PlacedObject | None
    reye: swf.PlacedObject | None

    mouth: swf.PlacedObject | None

    headItem: swf.PlacedObject | None
    neckItem: swf.PlacedObject | None
    faceItem: swf.PlacedObject | None

    def __init__(self, placementFrame: swf.Frame):
        self.lear = None
        self.rear = None
        self.leye = None
        self.reye = None
        self.mouth = None
        self.headItem = None
        self.neckItem = None
        self.faceItem = None

        for obj in placementFrame.objs:
            if (obj.xform != None):
                obj.xform.xscale = -1.0 if obj.xform.xscale < 0.0 else 1.0
                obj.xform.yscale = -1.0 if obj.xform.yscale < 0.0 else 1.0

            match (obj.name):
                case "":
                    if (obj.clipDepth == None):
                        self.head = obj
                case "lear":
                    self.lear = obj
                case "rear":
                    self.rear = obj
                case "leye":
                    self.leye = obj
                case "reye":
                    self.reye = obj
                case "mouth":
                    self.mouth = obj
                case "ahead":
                    self.headItem = obj
                case "aneck":
                    self.neckItem = obj
                case "aface":
                    self.faceItem = obj
                case "tex":
                    pass
                case "scars":
                    pass
                case _:
                    raise RuntimeError(f"Head placement has unknown obj {obj.name}")

def getCatComponent(dumpdir: str, tree: swf.SWF_Tree, components: swf.SWF_Tree.SpriteNode, id: int, texOverride: int | None = None) -> sprite.Sprite:
    frame = components.frames[id]

    textureObj = None
    objs = []
    for obj in frame.objs:
        if (obj.name == "tex"):
            assert(textureObj == None)
            textureObj = obj
        else:
            objs.append(obj)

    if textureObj != None:
        textureTable = tree.get(textureObj.id)
        assert(isinstance(textureTable, swf.SWF_Tree.SpriteNode))

        textureFrame = textureTable.frames[id if texOverride == None else texOverride]
        textureSprite = sprite.spriteFromPlacedObjects(dumpdir, tree, textureFrame.objs)
        textureSprite.applyTransform(textureObj.xform).applyTransform(textureObj.cxform)

        objs.append(sprite.PlacedSprite(textureSprite, textureObj.id, textureObj.depth, textureObj.clipDepth, textureObj.name))

    return sprite.spriteFromPlacedObjects(dumpdir, tree, objs)

def getCatHeadShape(dumpdir: str, tree: swf.SWF_Tree, heads: swf.SWF_Tree.SpriteNode, id: int, texture: int) -> sprite.Sprite:
    # @TODO scars
    # @TODO figure out wrinkles + old hair
    frame = heads.frames[id]

    textureObj = None
    objs = []
    for obj in frame.objs:
        if (obj.name == "tex"):
            assert(textureObj == None)
            textureObj = obj
        elif (obj.name != "scars"):
            objs.append(obj)
            
    if (textureObj == None):
        raise RuntimeError("CatHead missing texture")

    textureTable = tree.get(textureObj.id)
    assert(isinstance(textureTable, swf.SWF_Tree.SpriteNode))
    textureFrame = textureTable.frames[texture]

    tcomps = []
    for comp in textureFrame.objs:
        if comp.name == "greyhair" or comp.name == "wrinkles":
            continue

        tcomps.append(comp)

    textureSprite = sprite.spriteFromPlacedObjects(dumpdir, tree, tcomps)
    textureSprite.applyTransform(textureObj.xform).applyTransform(textureObj.cxform)

    objs.append(sprite.PlacedSprite(textureSprite, textureObj.id, textureObj.depth, textureObj.clipDepth, textureObj.name))

    return sprite.spriteFromPlacedObjects(dumpdir, tree, objs)


