# this file does *magic* :)

from .catgen import catparts as catpart
from .catgen import swf_tree as swf
from .catgen import sprite
from .catgen import animations

from .util import parse_gon as gon
from .util import ffdec_tools as ffdec
from .util import svg_tools as svg

from .catgen import palette

from . import items

import copy
import os
import shutil
import logging

from typing import Any

logging.getLogger("PIL").setLevel(logging.WARNING)

CUSTOM_CAT_GON = "./data/data/custom_cats.gon"
CATPARTS_SWF = "./data/swfs/catparts.swf"

class CustomCat:
    class Part:
        frame: int
        texture: int | None

        def __init__(self, defaultTex: int, defaultFrame: int, data = None):
            if (data == None):
                self.texture = defaultTex
                self.frame = defaultFrame - 1
                return

            if (isinstance(data, str) or isinstance(data, int)):
                self.frame = int(data) - 1
                self.texture = defaultTex
            else:
                self.frame = int(data.setdefault("frame", defaultFrame)) - 1
                self.texture = data.setdefault("texture", defaultTex)

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


class FacePose:
    browUp: tuple[float, float]
    browRot: tuple[float, float]
    earRot: tuple[float, float]
    mouth: str
    eyes: tuple[str, str]
    offset: tuple[float, float]
    back: bool

    def __init__(self, gondata: dict[str, Any]):
        ebu = gondata.setdefault("eyebrow_up", 15)
        if (isinstance(ebu, list)):
            self.browUp = (float(ebu[0]), float(ebu[1]))
        else:
            self.browUp = (float(ebu), float(ebu))

        ebr = gondata.setdefault("eyebrow_rotation", 0)
        if (isinstance(ebr, list)):
            self.browRot = (float(ebr[0]), float(ebr[1]))
        else:
            self.browRot = (float(ebr), float(ebr))

        earr = gondata.setdefault("ear_rotation", 0)
        if (isinstance(earr, list)):
            self.earRot = (float(earr[0]), float(earr[1]))
        else:
            self.earRot = (float(earr), float(earr))

        self.mouth = gondata.setdefault("mouth", "closed")
        eyes = gondata.setdefault("eyes", "open")
        if (isinstance(eyes, list)):
            self.eyes = (eyes[0], eyes[1])
        else:
            self.eyes = (eyes, eyes)

        offset = gondata.setdefault("face_offset", [10, 0])
        if (isinstance(offset, list)):
            self.offset = (float(offset[0]), float(offset[1]))
        else:
            self.offset = (float(offset), float(offset))

        self.back = gondata.setdefault("back", False)

class CatEquipment:
    head_front : sprite.Sprite | None
    head_back : sprite.Sprite | None

    face_front : sprite.Sprite | None
    face_back : sprite.Sprite | None

    neck_front : sprite.Sprite | None
    neck_back : sprite.Sprite | None

    def __init__(self):
        self.head_front = None
        self.head_back = None
        
        self.face_front = None
        self.face_back = None

        self.neck_back = None
        self.neck_front = None

class CatFace:
    lbrow : sprite.Sprite | None
    rbrow : sprite.Sprite | None

    lear : sprite.Sprite | None
    rear : sprite.Sprite | None

    leye_open : sprite.Sprite | None
    leye_closed : sprite.Sprite | None

    reye_open : sprite.Sprite | None
    reye_closed : sprite.Sprite | None

    mouth_open : sprite.Sprite | None
    mouth_closed : sprite.Sprite | None
    mouth_smile: sprite.Sprite | None

    headItemXForm : swf.swf.Matrix
    neckItemXForm : swf.swf.Matrix
    faceItemXForm : swf.swf.Matrix

    def __init__(self):
        self.lbrow = None
        self.rbrow = None
        self.lear = None
        self.rear = None
        self.leye_open = None
        self.reye_open = None
        self.leye_closed = None
        self.reye_closed = None
        self.mouth_open = None
        self.mouth_closed = None
        self.mouth_smile = None
        self.headItemXForm = swf.swf.Matrix()
        self.neckItemXForm = swf.swf.Matrix()
        self.faceItemXForm = swf.swf.Matrix()

def makeCatHead(cat: CustomCat, partDir: str, palettes: list[palette.Palette], catTree: swf.SWF_Tree) -> tuple[swf.swf.Matrix, CatFace]:
    colors = palettes[cat.palette]

    placements = catpart.HeadPlacements(catTree.get("CatHeadPlacements").frames[cat.head.frame])

    face = CatFace()

    allParts = []
    if (placements.lear != None):
        face.lear = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatEar"), cat.leftear.frame, cat.leftear.texture))
        face.lear.applyTransform(placements.lear.xform).applyTransform(placements.lear.cxform)
        allParts.append(face.lear)

    if (placements.rear != None):
        face.rear = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatEar"), cat.rightear.frame, cat.rightear.texture))
        face.rear.applyTransform(placements.rear.xform).applyTransform(placements.rear.cxform)
        allParts.append(face.rear)

    if (placements.leye != None):
        face.leye_open = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatEye"), cat.lefteye.frame, cat.lefteye.texture))
        face.leye_open.applyTransform(placements.leye.xform).applyTransform(placements.leye.cxform)

        face.leye_closed = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatEyeClosed"), cat.lefteye.frame, cat.lefteye.texture))
        face.leye_closed.applyTransform(placements.leye.xform).applyTransform(placements.leye.cxform)

        face.lbrow = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatEyebrow"), cat.lefteyebrow.frame, cat.lefteyebrow.texture))
        face.lbrow.applyTransform(placements.leye.xform).applyTransform(placements.leye.cxform)
        
        allParts += [face.leye_open, face.leye_closed, face.lbrow]

    if (placements.reye != None):
        face.reye_open = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatEye_Right"), cat.righteye.frame, cat.righteye.texture))
        face.reye_open.applyTransform(placements.reye.xform).applyTransform(placements.reye.cxform)

        face.reye_closed = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatEyeClosed_Right"), cat.righteye.frame, cat.righteye.texture))
        face.reye_closed.applyTransform(placements.reye.xform).applyTransform(placements.reye.cxform)

        face.rbrow = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatEyebrow"), cat.righteyebrow.frame, cat.righteyebrow.texture))
        face.rbrow.applyTransform(placements.reye.xform).applyTransform(placements.reye.cxform)
        
        allParts += [face.reye_open, face.reye_closed, face.rbrow]


    if (placements.mouth != None):
        face.mouth_closed = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatMouth"), cat.mouth.frame, cat.mouth.texture))
        face.mouth_closed.applyTransform(placements.mouth.xform).applyTransform(placements.mouth.cxform)
        
        face.mouth_open = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatMouthOpen"), cat.mouth.frame, cat.mouth.texture))
        face.mouth_open.applyTransform(placements.mouth.xform).applyTransform(placements.mouth.cxform)

        face.mouth_smile = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatMouthSmile"), cat.mouth.frame, cat.mouth.texture))
        face.mouth_smile.applyTransform(placements.mouth.xform).applyTransform(placements.mouth.cxform)

        allParts += [face.mouth_closed, face.mouth_open, face.mouth_smile]

    if (placements.headItem != None and placements.headItem.xform != None):
        face.headItemXForm = placements.headItem.xform

    if (placements.faceItem != None and placements.faceItem.xform != None):
        face.faceItemXForm = placements.faceItem.xform

    if (placements.neckItem != None and placements.neckItem.xform != None):
        face.neckItemXForm = placements.neckItem.xform

    for part in allParts:
        palette.applyPalette(colors, part.data)

    return (placements.head.xform, face)

ITEM_DICT = None

def getCatEquipment(partDir: str, catTree: swf.SWF_Tree, head: str | None, face: str | None, neck: str | None) -> CatEquipment:
    global ITEM_DICT

    out = CatEquipment()

    if (ITEM_DICT == None):
        ITEM_DICT = items.getItemDict()

    if (head != None):
        idata = ITEM_DICT[head]
        frame = idata.frame - 1

        fronts = catTree.get("HeadItemF")
        backs = catTree.get("HeadItemB")

        out.head_front = sprite.spriteFromPlacedObjects(partDir, catTree, fronts.frames[frame].objs)
        out.head_back = sprite.spriteFromPlacedObjects(partDir, catTree, backs.frames[frame].objs)

    if (face != None):
        idata = ITEM_DICT[face]
        frame = idata.frame - 1

        fronts = catTree.get("FaceItemF")
        backs = catTree.get("FaceItemB")

        out.face_front = sprite.spriteFromPlacedObjects(partDir, catTree, fronts.frames[frame].objs)
        out.face_back = sprite.spriteFromPlacedObjects(partDir, catTree, backs.frames[frame].objs)

    if (neck != None):
        idata = ITEM_DICT[neck]
        frame = idata.frame - 1

        fronts = catTree.get("NeckItemF")
        backs = catTree.get("NeckItemB")

        out.neck_front = sprite.spriteFromPlacedObjects(partDir, catTree, fronts.frames[frame].objs)
        out.neck_back = sprite.spriteFromPlacedObjects(partDir, catTree, backs.frames[frame].objs)

    return out


# palette and base position should be applied before this
def headWithPose(cat: CustomCat, partDir: str, catTree: swf.SWF_Tree, equipment: CatEquipment, face: CatFace, pose: FacePose, palettes: list[palette.Palette]):
    # don't want to deal with Python's nonsense reference semantics
    head = copy.deepcopy(catpart.getCatHeadShape(partDir, catTree, catTree.get("CatHead"), cat.head.frame, cat.texture, pose.offset))
    #headPlacement.yoffset -= 10
    #head.applyTransform(headPlacement)
    
    palette.applyPalette(palettes[cat.palette], head.data)

    face = copy.deepcopy(face)
    equipment = copy.deepcopy(equipment)

    HEAD_DEPTH = 10
    
    forward = -1 if pose.back else 1

    # ears: 3-4, ears are ALWAYS behind head
    # head: 10
    # mouth: 11
    # eyes: 12-13
    # brows: 14-15

    assembly = [
        sprite.PlacedSprite(head, 0, HEAD_DEPTH, None, "Head")
    ]

    onlyoffset = swf.swf.Matrix()
    onlyoffset.xoffset = pose.offset[0]
    onlyoffset.yoffset = -pose.offset[1]

    if (pose.back):
        if (equipment.head_back != None):
            equipment.head_back.applyTransform(face.headItemXForm)
            assembly.append(sprite.PlacedSprite(equipment.head_back, 0, HEAD_DEPTH + 6, None, "Head Item"))

        if (equipment.face_back != None):
            equipment.face_back.applyTransform(face.faceItemXForm)
            equipment.face_back.applyTransform(onlyoffset)
            assembly.append(sprite.PlacedSprite(equipment.face_back, 0, HEAD_DEPTH + 8, None, "Face Item"))
        
        if (equipment.neck_back != None):
            equipment.neck_back.applyTransform(face.neckItemXForm)
            assembly.append(sprite.PlacedSprite(equipment.neck_back, 0, HEAD_DEPTH - 1, None, "Neck Item"))
    else:
        if (equipment.head_front != None):
            equipment.head_front.applyTransform(face.headItemXForm)
            assembly.append(sprite.PlacedSprite(equipment.head_front, 0, HEAD_DEPTH + 6, None, "Head Item"))

        if (equipment.face_front != None):
            equipment.face_front.applyTransform(face.faceItemXForm)
            equipment.face_front.applyTransform(onlyoffset)
            assembly.append(sprite.PlacedSprite(equipment.face_front, 0, HEAD_DEPTH + 8, None, "Face Item"))
        
        if (equipment.neck_front != None):
            equipment.neck_front.applyTransform(face.headItemXForm)
            assembly.append(sprite.PlacedSprite(equipment.neck_front, 0, HEAD_DEPTH - 1, None, "Neck Item"))

    if (face.lear != None):
        xform = swf.swf.Matrix()
        # @TODO rotation
        
        face.lear.applyTransform(xform)
        assembly.append(sprite.PlacedSprite(face.lear, 0, HEAD_DEPTH - 6, None, "Left Ear"))

    if (face.rear != None):
        xform = swf.swf.Matrix()
        # @TODO rotation
        
        face.rear.applyTransform(xform)
        assembly.append(sprite.PlacedSprite(face.rear, 0, HEAD_DEPTH - 7, None, "Right Ear"))

    if (face.lbrow != None):
        xform = swf.swf.Matrix()
        xform.xoffset = pose.offset[0]
        xform.yoffset = -pose.offset[1] - pose.browUp[0]
        # @TODO rotation
        
        face.lbrow.applyTransform(xform)
        assembly.append(sprite.PlacedSprite(face.lbrow, 0, HEAD_DEPTH + forward * 4, None, "Left Brow"))

    if (face.rbrow != None):
        xform = swf.swf.Matrix()
        xform.xoffset = pose.offset[0]
        xform.yoffset = -pose.offset[1] - pose.browUp[1]
        # @TODO rotation
        
        face.rbrow.applyTransform(xform)
        assembly.append(sprite.PlacedSprite(face.rbrow, 0, HEAD_DEPTH + forward * 5, None, "Right Brow"))

    if (pose.eyes[0] == "closed" and face.leye_closed != None):
        tf = sprite.Sprite.matrixFromSVG(face.leye_closed.data.data.getTransform())
        if (pose.offset[0] < 0):
            tf.xscale *= -1.0
            face.leye_closed.data.data.subcomponents[0].setTransform(sprite.Sprite.matrixToSVG(tf))

        face.leye_closed.applyTransform(onlyoffset)
        assembly.append(sprite.PlacedSprite(face.leye_closed, 0, HEAD_DEPTH + forward * 2, None, "Left Eye"))
    elif (pose.eyes[0] == "open" and face.leye_open != None):
        tf = sprite.Sprite.matrixFromSVG(face.leye_open.data.data.getTransform())
        if (pose.offset[0] < 0):
            tf.xscale *= -1.0
            face.leye_open.data.data.subcomponents[0].setTransform(sprite.Sprite.matrixToSVG(tf))

        face.leye_open.applyTransform(onlyoffset)
        assembly.append(sprite.PlacedSprite(face.leye_open, 0, HEAD_DEPTH + forward * 2, None, "Left Eye"))
    elif (pose.eyes[0] != "closed" and pose.eyes[0] != "open"):
        raise RuntimeError("Weird eye state " + pose.eyes[0])

    if (pose.eyes[1] == "closed" and face.reye_closed != None):
        tf = sprite.Sprite.matrixFromSVG(face.reye_closed.data.data.getTransform())
        if (pose.offset[0] > 0):
            tf.xscale *= -1.0
            face.reye_closed.data.data.subcomponents[0].setTransform(sprite.Sprite.matrixToSVG(tf))

        face.reye_closed.applyTransform(onlyoffset)
        assembly.append(sprite.PlacedSprite(face.reye_closed, 0, HEAD_DEPTH + forward * 3, None, "Right Eye"))
    elif (pose.eyes[1] == "open" and face.reye_open != None):
        tf = sprite.Sprite.matrixFromSVG(face.reye_open.data.data.subcomponents[0].getTransform())
        if (pose.offset[0] > 0):
            tf.xscale *= -1.0
            face.reye_open.data.data.subcomponents[0].setTransform(sprite.Sprite.matrixToSVG(tf))

        face.reye_open.applyTransform(onlyoffset)
        assembly.append(sprite.PlacedSprite(face.reye_open, 0, HEAD_DEPTH + forward * 3, None, "Right Eye"))
    elif (pose.eyes[1] != "closed" and pose.eyes[1] != "open"):
        raise RuntimeError("Weird eye state " + pose.eyes[1])

    
    if (pose.mouth == "closed" and face.mouth_closed != None):
        tf = sprite.Sprite.matrixFromSVG(face.mouth_closed.data.data.getTransform())
        if (pose.offset[0] < 0):
            tf.xscale *= -1.0
            face.mouth_closed.data.data.subcomponents[0].setTransform(sprite.Sprite.matrixToSVG(tf))

        face.mouth_closed.applyTransform(onlyoffset)
        assembly.append(sprite.PlacedSprite(face.mouth_closed, 0, HEAD_DEPTH + forward * 1, None, "Mouth"))
    elif (pose.mouth == "open" and face.mouth_open != None):
        tf = sprite.Sprite.matrixFromSVG(face.mouth_open.data.data.getTransform())
        if (pose.offset[0] < 0):
            tf.xscale *= -1.0
            face.mouth_open.data.data.subcomponents[0].setTransform(sprite.Sprite.matrixToSVG(tf))

        face.mouth_open.applyTransform(onlyoffset)
        assembly.append(sprite.PlacedSprite(face.mouth_open, 0, HEAD_DEPTH + forward * 1, None, "Mouth"))
    elif (pose.mouth == "smile" and face.mouth_smile != None):
        tf = sprite.Sprite.matrixFromSVG(face.mouth_smile.data.data.getTransform())
        if (pose.offset[0] < 0):
            tf.xscale *= -1.0
            face.mouth_smile.data.data.subcomponents[0].setTransform(sprite.Sprite.matrixToSVG(tf))

        face.mouth_smile.applyTransform(onlyoffset)
        assembly.append(sprite.PlacedSprite(face.mouth_smile, 0, HEAD_DEPTH + forward * 1, None, "Mouth"))
    elif (pose.mouth != "closed" and pose.mouth != "open" and pose.mouth != "smile"):
        raise RuntimeError("Weird mouth state " + pose.mouth)

    return sprite.spriteFromPlacedObjects(partDir, catTree, assembly)

def getCustomCats() -> list[CustomCat]:
    data = gon.parse_gon(CUSTOM_CAT_GON)

    out: list[CustomCat] = []
    for id, cat in data.items():
        if (id == "__COMMENTS__"):
            continue

        out.append(CustomCat(id, cat))

    return out

def assembleCat(cat: CustomCat, partDir: str, palettes: list[palette.Palette], anim: list[animations.CatFrame], catTree: swf.SWF_Tree) -> list[sprite.Sprite]:

    out = []

    headx, face = makeCatHead(cat, partDir, palettes, catTree)
    equip = getCatEquipment(partDir, catTree, None, "HuntersPatch", None)
    outhead = headWithPose(cat, partDir, catTree, equip, face, FacePose({
            "face_offset": [10, 0]
        }), palettes)

    for frame in anim:
        head = copy.deepcopy(outhead)
        head.applyTransform(frame.head)

        # @TODO items

        colors = palettes[cat.palette]
        body = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatBody"), cat.body.frame, cat.body.texture))
        body.applyTransform(frame.body)
        palette.applyPalette(colors, body.data)

        # left/right arms and legs are flipped @TODO fix that :)
        arm1 = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatLeg"), cat.arm1.frame, cat.arm1.texture))
        arm1.applyTransform(frame.arm1)
        palette.applyPalette(colors, arm1.data)

        arm2 = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatLeg"), cat.arm2.frame, cat.arm2.texture))
        arm2.applyTransform(frame.arm2)
        palette.applyPalette(colors, arm2.data)

        leg1 = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatLeg"), cat.leg1.frame, cat.leg1.texture))
        leg1.applyTransform(frame.leg1)
        palette.applyPalette(colors, leg1.data)


        leg2 = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatLeg"), cat.leg2.frame, cat.leg2.texture))
        leg2.applyTransform(frame.leg2)
        palette.applyPalette(colors, leg2.data)

        tail = copy.deepcopy(catpart.getCatComponent(partDir, catTree, catTree.get("CatTail"), cat.tail.frame, cat.tail.texture))
        tail.applyTransform(frame.tail)
        palette.applyPalette(colors, tail.data)


        # @TODO body, animations, etc...


        assembly = [
            sprite.PlacedSprite(head, 0, 5, None, "Whole Head"),
            sprite.PlacedSprite(body, 0, 0, None, "Body"),
            sprite.PlacedSprite(arm1, 0, 3, None, "Right Arm"),
            sprite.PlacedSprite(arm2, 0, -2, None, "Left Arm"),
            sprite.PlacedSprite(leg1, 0, 2, None, "Right Leg"),
            sprite.PlacedSprite(leg2, 0, -3, None, "Left Leg"),
            sprite.PlacedSprite(tail, 0, -4, None, "Tail")
        ]

        out.append(sprite.spriteFromPlacedObjects(partDir, catTree, assembly))
  
    return out
   
from wand.image import Image
from wand.color import Color


def exportCustomCats(svgCropper: svg.SvgCropper, ffdecPath: str, cats: list[CustomCat], outdir: str):
    partDir = ffdec.exportShapesIfNeeded(ffdecPath, catpart.CATPARTS_SWF)
    palettes = palette.loadPalettes("./data/textures/palette.png")
    catpartTree = swf.getSwfTree(catpart.CATPARTS_SWF)

    outdir += "/custom_cats"
    if (os.path.isdir(outdir)):
        shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)

    anims = animations.getCatAnims()

    count = 0
    for cat in cats:
        if ("HunterCat_" not in cat.id):
            continue

        frames = assembleCat(cat, partDir, palettes, anims["HunterIdleF"], catpartTree)
        outfolder = f"{outdir}/{cat.id}"
        os.makedirs(outfolder, exist_ok=True)

        # hacky solution to put the cat in frame...
        translate = swf.swf.Matrix()
        translate.xoffset = 90
        translate.yoffset = 50

        scaling = 3.0

        with Color('transparent') as bg:
            with Image(background=bg) as gif:
                for i in range(len(frames)):
                    outfile = f"{outfolder}/{i}.svg"
                    
                    frames[i].applyTransform(translate)
                    svgData = frames[i].compile()

                    if (i == 0):
                        with open(outfile, "w") as ocat:
                            ocat.write(svgData)

                        

                    with Image(blob=svgData.encode("utf-8"), background=bg, resolution=72 * scaling) as frame:
                        frame.delay = 2
                        frame.dispose = "background"
                        gif.sequence.append(frame)

                        if (i == 0):
                            frame.trim()
                            frame.format = 'png'
                            frame.save(filename=outfile.removesuffix(".svg") + ".png")
                            return 1

                    #svgCropper.cropForAnimation(outfile, outfile)

                gif.type = "optimize"
                gif.loop = 0
                gif.coalesce()
                gif.trim() # this doesn't work :)
                gif.save(filename=f"{outfolder}/animation.gif")


        count += 1

    return count

    

    


