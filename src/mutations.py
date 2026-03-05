from . import translations as translations
from .catgen import sprite
from .catgen import palette
from .catgen import swf_tree as swf

from .util import parse_gon as gon
from .util import ffdec_tools as ffdec

import src.util.svg_tools as svg

import copy
import os
import shutil

MUTATIONS_FOLDER = "./data/data/mutations"
PARTS_SWF = "./data/swfs/catparts.swf"

PALETTE = 43

CATPARTS = [
    ("Body", "body.gon", "CatBody"),
    ("Ears", "ears.gon", "CatEar"),
    ("Eyebrows", "eyebrows.gon", "CatEyebrow"),
    ("Eyes", "eyes.gon", "CatEye"),
    ("Texture", "texture.gon", "CatTexture"),
    ("Head", "head.gon", "CatHead"),
    ("Legs", "legs.gon", "CatLeg"),
    ("Mouth", "mouth.gon", "CatMouth"),
    ("Tail", "tail.gon", "CatTail")
]

def exportMutations(svgCropper: svg.SvgCropper, ffdecPath: str, outfolder: str):
    outfolder += "/mutations"
    if (os.path.isdir(outfolder)):
        shutil.rmtree(outfolder)
    os.makedirs(outfolder)

    colors = palette.loadPalettes(palette.PALETTE_PATH)[PALETTE]
    dumpdir = ffdec.exportShapesIfNeeded(ffdecPath, PARTS_SWF)

    catTree = swf.getSwfTree(PARTS_SWF)

    for type, gonFile, swfName in CATPARTS:
        parts = catTree.get(swfName)

        data = gon.parse_gon(MUTATIONS_FOLDER + '/' + gonFile)
        for d in data.values():
            for id in d.keys():
                if (id == "__COMMENTS__"):
                    continue

                if (id != "427"):
                    continue

                s = copy.deepcopy(sprite.spriteFromNode(dumpdir, catTree, parts, int(id) - 1))
                name = f"{outfolder}/Mutation {type.lower()}.{id}.svg"

                if (type == "Legs"):
                    s.data.removeComposite("DefineShape_9086")

                if (type == "Head"):
                    s.data.removeComposite("DefineShape_5963")
                    s.data.removeComposite("DefineShape_5952")

                palette.applyPalette(colors, s.data)

                with open(name, "w") as w:
                    w.write(s.compile())

                #svgCropper.crop(name, name)