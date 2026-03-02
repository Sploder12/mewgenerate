# this file does *magic* :)

from .catgen import catparts as catpart
from .catgen import swf_tree as swf
from .catgen import sprite

from .util import parse_gon as gon
from .util import ffdec_tools as ffdec
from .util import svg_tools as svg

from .catgen import palette

import os
import shutil
import logging

logging.getLogger("PIL").setLevel(logging.WARNING)

CUSTOM_CAT_GON = "./data/data/custom_cats.gon"
CATPARTS_SWF = "./data/swfs/catparts.swf"

class CustomCat:
    class Part:
        frame: int
        texture: int | None

        def __init__(self, defaultTex: int, defaultFrame: int, data = None):
            if (data == None):
                self.texture = None
                self.frame = defaultFrame - 1
                return

            if (isinstance(data, str) or isinstance(data, int)):
                self.frame = int(data) - 1
                self.texture = None
            else:
                self.frame = int(data.setdefault("frame", defaultFrame)) - 1
                self.texture = data.setdefault("texture", None)

    id: str

    voice = ""
    pitch = 1.0

    class_anis = ""
    default_frame = 1

    texture = 1
    palette = 1
   
    body: Part
    tail: Part
    
    leg1: Part
    leg2: Part
    arm1: Part
    arm2: Part
    claws: Part

    head: Part
    lefteye: Part
    righteye: Part
    lefteyebrow: Part
    righteyebrow: Part
    leftear: Part
    rightear: Part
    mouth: Part

    def __init__(self, name: str, gondata):
        self.id = name

        self.voice = gondata.setdefault("voice", "")
        self.pitch = float(gondata.setdefault("pitch", self.pitch))

        self.class_anis = gondata.setdefault("class_anis", self.class_anis)
        self.default_frame = int(gondata.setdefault("default_frame", self.default_frame))

        self.texture = int(gondata.setdefault("texture", self.texture)) - 1
        self.palette = int(gondata.setdefault("palette", self.palette))

        self.body = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("body", None))
        self.tail = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("tail", None))
        
        self.leg1 = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("leg1", None))
        self.leg2 = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("leg2", None))
        self.arm1 = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("arm1", None))
        self.arm2 = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("arm2", None))
        self.claws = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("claws", None))

        self.head = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("head", None))
        self.lefteye = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("lefteye", None))
        self.righteye = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("righteye", None))
        self.lefteyebrow = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("lefteyebrow", None))
        self.righteyebrow = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("righteyebrow", None))
        self.leftear = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("leftear", None))
        self.rightear = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("rightear", None))
        self.mouth = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("mouth", None))

def getCustomCats() -> list[CustomCat]:
    data = gon.parse_gon(CUSTOM_CAT_GON)

    out: list[CustomCat] = []
    for id, cat in data.items():
        if (id == "__COMMENTS__"):
            continue

        out.append(CustomCat(id, cat))

    return out

def assembleCat(cat: CustomCat, partDir: str, palettes: list[palette.Palette], catTree: swf.SWF_Tree) -> sprite.Sprite:
    colors = palettes[cat.palette]

    placements = catpart.HeadPlacements(catTree.get("CatHeadPlacements").frames[cat.head.frame])

    head = catpart.getCatHeadShape(partDir, catTree, catTree.get("CatHead"), cat.head.frame, cat.texture)
    head.applyTransform(placements.head.xform).applyTransform(placements.head.cxform)
    assembly = [
        sprite.PlacedSprite(head, cat.head.frame, placements.head.depth, placements.head.clipDepth, placements.head.name)
    ]
    
    if (placements.lear != None):
        lear = catpart.getCatComponent(partDir, catTree, catTree.get("CatEar"), cat.leftear.frame, cat.leftear.texture)
        lear.applyTransform(placements.lear.xform).applyTransform(placements.lear.cxform)
        assembly.append(sprite.PlacedSprite(lear, cat.leftear.frame, placements.head.depth - 2, placements.lear.clipDepth, placements.lear.name))

    if (placements.rear != None):
        rear = catpart.getCatComponent(partDir, catTree, catTree.get("CatEar"), cat.rightear.frame, cat.rightear.texture)
        rear.applyTransform(placements.rear.xform).applyTransform(placements.rear.cxform)
        assembly.append(sprite.PlacedSprite(rear, cat.rightear.frame, placements.head.depth - 1, placements.rear.clipDepth, placements.rear.name))

    if (placements.leye != None):
        adjDepth = placements.leye.depth if placements.mouth == None else placements.mouth.depth + 1
        leye = catpart.getCatComponent(partDir, catTree, catTree.get("CatEye"), cat.lefteye.frame, cat.lefteye.texture)
        leye.applyTransform(placements.leye.xform).applyTransform(placements.leye.cxform)
        assembly.append(sprite.PlacedSprite(leye, cat.lefteye.frame, adjDepth, placements.leye.clipDepth, placements.leye.name))

        lbrow = catpart.getCatComponent(partDir, catTree, catTree.get("CatEyebrow"), cat.lefteyebrow.frame, cat.lefteyebrow.texture)
        lbrow.applyTransform(placements.leye.xform).applyTransform(placements.leye.cxform)
        xform = swf.swf.Matrix()
        xform.yoffset = -15.0
        lbrow.applyTransform(xform)
        assembly.append(sprite.PlacedSprite(lbrow, cat.lefteyebrow.frame, adjDepth + 1, placements.leye.clipDepth, placements.leye.name + "brow"))

        

    if (placements.reye != None):
        adjDepth = placements.reye.depth if placements.mouth == None else placements.mouth.depth + 3
        reye = catpart.getCatComponent(partDir, catTree, catTree.get("CatEye"), cat.righteye.frame, cat.righteye.texture)
        reye.applyTransform(placements.reye.xform).applyTransform(placements.reye.cxform)
        assembly.append(sprite.PlacedSprite(reye, cat.righteye.frame, adjDepth, placements.reye.clipDepth, placements.reye.name))

        rbrow = catpart.getCatComponent(partDir, catTree, catTree.get("CatEyebrow"), cat.righteyebrow.frame, cat.righteyebrow.texture)
        rbrow.applyTransform(placements.reye.xform).applyTransform(placements.reye.cxform)
        xform = swf.swf.Matrix()
        xform.yoffset = -15.0
        rbrow.applyTransform(xform)
        assembly.append(sprite.PlacedSprite(rbrow, cat.righteyebrow.frame, adjDepth + 1, placements.reye.clipDepth, placements.reye.name + "brow"))


    if (placements.mouth != None):
        mouth = catpart.getCatComponent(partDir, catTree, catTree.get("CatMouth"), cat.mouth.frame, cat.mouth.texture)
        mouth.applyTransform(placements.mouth.xform).applyTransform(placements.mouth.cxform)
        assembly.append(sprite.PlacedSprite(mouth, cat.mouth.frame, placements.mouth.depth, placements.mouth.clipDepth, placements.mouth.name))

    
    

    # @TODO brows

    # @TODO items

    # @TODO body, animations, etc...

    out = sprite.spriteFromPlacedObjects(partDir, catTree, assembly)
    palette.applyPalette(colors, out.data)
    return out
   
def exportCustomCats(svgCropper: svg.SvgCropper, ffdecPath: str, cats: list[CustomCat], outdir: str):
    partDir = ffdec.exportShapesIfNeeded(ffdecPath, catpart.CATPARTS_SWF)
    palettes = palette.loadPalettes("./data/textures/palette.png")
    catpartTree = swf.getSwfTree(catpart.CATPARTS_SWF)

    outdir += "/custom_cats"
    if (os.path.isdir(outdir)):
        shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)

    count = 0
    for cat in cats:
        s = assembleCat(cat, partDir, palettes, catpartTree)
        outfile = f"{outdir}/{cat.id}.svg"
        with open(outfile, "w") as ocat:
            ocat.write(s.compile())

        svgCropper.crop(outfile, outfile)
        count += 1

    return count

    

    


