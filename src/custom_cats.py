# this file does *magic* :)

from .util import parse_csv as csv
from .util import parse_gon as gon
from .util import ffdec_tools as ffdec
from .util import svg_tools as svg

from . import palette

import os
import shutil
import logging

from PIL import Image
logging.getLogger("PIL").setLevel(logging.WARNING)

CUSTOM_CAT_GON = "./data/data/custom_cats.gon"
CATPARTS_SWF = "./data/swfs/catparts.swf"

class CustomCat:
    class Part:
        frame: int
        texture: int

        def __init__(self, defaultTex: int, defaultFrame: int, data = None):
            if (data == None):
                self.texture = defaultTex
                self.frame = defaultFrame
                return

            if (isinstance(data, str) or isinstance(data, int)):
                self.frame = int(data)
                self.texture = defaultTex
            else:
                self.frame = int(data.setdefault("frame", defaultFrame))
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

        self.voice = gondata.setdefault("voice", self.default_frame)
        self.pitch = float(gondata.setdefault("pitch", self.pitch))

        self.class_anis = gondata.setdefault("class_anis", self.class_anis)
        self.default_frame = int(gondata.setdefault("default_frame", self.default_frame))

        self.texture = int(gondata.setdefault("texture", self.texture))
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

def declaw(src: str, dest: str):
    with open(src, "r") as data:
        content = data.readlines()

    out = []
    for line in content:
        if ("use" in line and "xlink:href=\"#sprite2\"" in line):
            continue
    
        out.append(line)

    with open(dest, "w") as outdata:
        outdata.write(''.join(out))
    
def deage(data: svg.SvgData):
    data.removeComposite("wrinkles")
    data.removeComposite("greyhair")

def exportCustomCats(svgCropper: svg.SvgCropper, ffdecPath: str,cats: list[CustomCat], outdir: str):
    partDir = ffdec.exportSpritesIfNeeded(ffdecPath, CATPARTS_SWF)

    partFolderLUT = {}
    for dir in os.listdir(partDir):
        s = dir.split('_')
        if (len(s) > 2):
            label = '_'.join(s[2:])

            partFolderLUT[label] = os.path.join(partDir, dir)

    outdir += "/custom_cats"
    if (os.path.isdir(outdir)):
        shutil.rmtree(outdir)

    textureDir = partFolderLUT.get("CatTexture")

    legDir = partFolderLUT.get("CatLeg")
    tailDir = partFolderLUT.get("CatTail")
    bodyDir = partFolderLUT.get("CatBody")
    headDir = partFolderLUT.get("CatHead")

    headPlacementDir = partFolderLUT.get("CatHeadPlacements")

    earDir = partFolderLUT.get("CatEar")
    rightEyeDir = partFolderLUT.get("CatEye_Right")
    eyeDir = partFolderLUT.get("CatEye")
    eyebrowDir = partFolderLUT.get("CatEyebrow")
    mouthDir = partFolderLUT.get("CatMouth")

    palettes = palette.loadPalettes("./data/textures/palette.png")

    count = 0
    for cat in cats:
        folder = outdir + '/' + cat.id

        os.makedirs(folder)

        # def setComponent(uid: str, id: str, src: svg.SvgData, dest: svg.SvgData, reverseOrder = False):
        #     tag = dest.findComposite(id)
        #     if tag == None:
        #         return False
            
        #     transform = tag.getTransform().split(',')

        #     src.prefixLinks(uid)

        #     if reverseOrder:
        #         dest.defs.subcomponents = src.defs.subcomponents + dest.defs.subcomponents
        #     else:
        #         dest.defs.subcomponents += src.defs.subcomponents

        #     # @TODO figure out transforms (try rebase on 0?)
        #     #src.decl.setTransform(f"matrix({"-1.0" if '-' in transform[0] else "1.0"}, 0.0, 0.0, {"-1.0" if '-' in transform[3] else "1.0"}, {transform[4]}, {transform[5]}")
        #     dest.replaceComposite(id, src.decl)

        #     return True

        # def setTex(uid: str, svgdata: svg.SvgData, texture: int):
        #     tex = svg.parse_svg(textureDir + '/' + str(texture) + ".svg")
        #     return setComponent(uid, "tex", tex, svgdata)

        # out = svg.parse_svg(headPlacementDir + '/' + str(cat.head.frame) + ".svg")
        # keep = []
        # for sub in out.decl.subcomponents:
        #     if sub.getTagname() == "use" and sub.getID() == "":
        #         keep.append(out.defs.findComposite(sub.getHrefID()))

        # out.defs.subcomponents.clear()
        # for k in keep:
        #     if k != None:
        #         out.defs.subcomponents.append(k)

        # setTex("head_", out, cat.head.texture)

        # declaw(legDir + '/' + str(cat.leg1.frame) + ".svg", folder + "/leg1.svg")
        # declaw(legDir + '/' + str(cat.leg2.frame) + ".svg", folder + "/leg2.svg")
        # declaw(legDir + '/' + str(cat.arm1.frame) + ".svg", folder + "/arm1.svg")
        # declaw(legDir + '/' + str(cat.arm2.frame) + ".svg", folder + "/arm2.svg")

        #deage(headDir + '/' + str(cat.head.frame) + ".svg", folder + "/head.svg")
        
        # svgCropper.crop(bodyDir + '/' + str(cat.body.frame) + ".svg", folder + "/body.svg")
        # if (cat.body.texture != cat.texture):
        #     svgCropper.crop(textureDir + '/' + str(cat.body.texture) + ".svg", folder + "/body_texture.svg")

        # svgCropper.crop(tailDir + '/' + str(cat.tail.frame) + ".svg", folder + "/tail.svg")
        # if (cat.tail.texture != cat.texture):
        #     svgCropper.crop(textureDir + '/' + str(cat.tail.texture) + ".svg", folder + "/tail_texture.svg")

        # svgCropper.crop(folder + "/leg1.svg", folder + "/leg1.svg")
        # if (cat.leg1.texture != cat.texture):
        #     svgCropper.crop(textureDir + '/' + str(cat.leg1.texture) + ".svg", folder + "/leg1_texture.svg")

        # svgCropper.crop(folder + "/leg2.svg", folder + "/leg2.svg")
        # if (cat.leg2.texture != cat.texture):
        #     svgCropper.crop(textureDir + '/' + str(cat.leg2.texture) + ".svg", folder + "/leg2_texture.svg")

        # svgCropper.crop(folder + "/arm1.svg", folder + "/arm1.svg")
        # if (cat.arm1.texture != cat.texture):
        #     svgCropper.crop(textureDir + '/' + str(cat.arm1.texture) + ".svg", folder + "/arm1_texture.svg")

        # svgCropper.crop(folder + "/arm2.svg", folder + "/arm2.svg")
        # if (cat.arm2.texture != cat.texture):
        #     svgCropper.crop(textureDir + '/' + str(cat.arm2.texture) + ".svg", folder + "/arm2_texture.svg")

        # claws???

        #svgCropper.crop(folder + "/head.svg", folder + "/head.svg")
        #if (cat.head.texture != cat.texture):
        #    svgCropper.crop(textureDir + '/' + str(cat.head.texture) + ".svg", folder + "/head_texture.svg")

        # mouth = svg.parse_svg(mouthDir + '/' + str(cat.mouth.frame) + ".svg")
        # setTex("mouth_", mouth, cat.mouth.texture)
        # setComponent("mouth_", "mouth", mouth, out)

        # leye = svg.parse_svg(eyeDir + '/' + str(cat.lefteye.frame) + ".svg")
        # setTex("leye_", leye, cat.lefteye.texture)
        # setComponent("leye_", "leye", leye, out)

        # reye = svg.parse_svg(rightEyeDir + '/' + str(cat.righteye.frame) + ".svg")
        # setTex("reye_", reye, cat.righteye.texture)
        # setComponent("reye_", "reye", reye, out)

        # lear = svg.parse_svg(earDir + '/' + str(cat.leftear.frame) + ".svg")
        # setTex("lear_", lear, cat.leftear.texture)

        # palette.applyPalette(palettes[cat.palette], lear)
        # with open(f"{folder}/test_lear.svg", "w") as of:
        #     of.write(lear.compile())

        # setComponent("lear_", "lear", lear, out, True)

        # rear = svg.parse_svg(earDir + '/' + str(cat.rightear.frame) + ".svg")
        # setTex("rear_", rear, cat.rightear.texture)
        # setComponent("rear_", "rear", rear, out, True)
 
        svgCropper.crop(eyebrowDir + '/' + str(cat.lefteyebrow.frame) + ".svg", folder + "/lefteyebrow.svg")
        if (cat.lefteyebrow.texture != cat.texture):
            svgCropper.crop(textureDir + '/' + str(cat.lefteyebrow.texture) + ".svg", folder + "/lefteyebrow_texture.svg")

        svgCropper.crop(eyebrowDir + '/' + str(cat.righteyebrow.frame) + ".svg", folder + "/righteyebrow.svg")
        if (cat.righteyebrow.texture != cat.texture):
            svgCropper.crop(textureDir + '/' + str(cat.righteyebrow.texture) + ".svg", folder + "/righteyebrow_texture.svg")
        
        #palette.applyPalette(palettes[cat.palette], out)
        #with open(f"{folder}/{cat.id}.svg", "w") as of:
        #    of.write(out.compile())

        #svgCropper.crop(f"{folder}/{cat.id}.svg", f"{folder}/{cat.id}.svg")
        count += 1

    return count


