from . import swf_tree as tree

import logging

CATANIS_SWF1 = "./data/swfs/catanis.swf"
CATANIS_SWF2 = "./data/swfs/catanis2.swf"

class CatFrame:
    head: tuple[tree.swf.Matrix, int]
    body: tuple[tree.swf.Matrix, int]
    arm1: tuple[tree.swf.Matrix, int]
    arm2: tuple[tree.swf.Matrix, int]
    leg1: tuple[tree.swf.Matrix, int]
    leg2: tuple[tree.swf.Matrix, int]
    tail: tuple[tree.swf.Matrix, int]

    face: str

    extra: dict[str, tree.swf.Matrix]

    def __init__(self):
        self.head = (tree.swf.Matrix(), 0)
        self.body = (tree.swf.Matrix(), 0)

        self.arm1 = (tree.swf.Matrix(), 0)

        self.arm2 = (tree.swf.Matrix(), 0)

        self.leg1 = (tree.swf.Matrix(), 0)
        self.leg2 = (tree.swf.Matrix(), 0)
        self.tail = (tree.swf.Matrix(), 0)

        self.extra = {}

        self.face = ""

def catFrameFromObjs(objs: list[tree.PlacedObject]) -> CatFrame:
    out = CatFrame()
    for obj in objs:
        if (obj.name.startswith("head")):
            if "_" in obj.name:
                out.face = obj.name.removeprefix("head_")
            
            out.head = (obj.xform, obj.depth)
            continue

        match obj.name:
            case "body":
                out.body = (obj.xform, obj.depth)
            case "arm1":
                out.arm1 = (obj.xform, obj.depth)
            case "arm2":
                out.arm2 = (obj.xform, obj.depth)
            case "leg1":
                out.leg1 = (obj.xform, obj.depth)
            case "leg2":
                out.leg2 = (obj.xform, obj.depth)
            case "tail":
                out.tail = (obj.xform, obj.depth)
            case _:
                out.extra[obj.name] = obj.xform
    
    return out

def aniFromSprite(defSprite: tree.SWF_Tree.SpriteNode) -> list[CatFrame]:
    out = []
    for frame in defSprite.frames:
        out.append(catFrameFromObjs(frame.objs))

    return out

def anisFromSprite(swfTree: tree.SWF_Tree, defSprite: tree.SWF_Tree.SpriteNode) -> dict[str, list[CatFrame]]:
    out = {}
    for frame in defSprite.frames:
        if (frame.name == ""):
            continue

        if (len(frame.objs) > 1):
            logging.warning("Animation has many animations: " + frame.name)
            continue
            raise RuntimeError("Animation has many animations: " + frame.name)

        if (len(frame.objs) == 0):
            out[frame.name] = []
            continue

        node = swfTree.get(frame.objs[0].id)
        out[frame.name] = aniFromSprite(node)
        
    return out

def getCatAnims() -> dict[str, list[CatFrame]]:
    anis1 = tree.getSwfTree(CATANIS_SWF1)
    out = anisFromSprite(anis1, anis1.get("CatTest"))

    anis2 = tree.getSwfTree(CATANIS_SWF2)
    out |= anisFromSprite(anis2, anis2.get("_Append_CatTest"))

    return out