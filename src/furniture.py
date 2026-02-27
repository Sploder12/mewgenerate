from .util import parse_swf as swf
from .util import parse_gon as gon
from .util import ffdec_tools as ffdec
from .util import svg_tools as svg

import os
import shutil
import logging

FURNITURE_SWF = "./data/swfs/furniture.swf"
FURNITURE_GON = "./data/data/furniture_effects.gon"

#FURNITURE_DATA = gon.parse_gon(FURNITURE_GON)
FURNITURE_SWF_TAGS = swf.parse_swf(FURNITURE_SWF)

class Furniture:
    lookup: dict[str, int]
    allSprites: dict[int, swf.DefineSprite]

    def __init__(self):
        self.lookup = {}
        self.allSprites = swf.getAllSprites(FURNITURE_SWF_TAGS)
        symbolTable = swf.getSymbolTable(FURNITURE_SWF_TAGS)
      
        furnitureLUT = self.allSprites.get(symbolTable.get("Furniture"))

        curLabel = ""
        curID = None
        for frame in furnitureLUT.tags:
            if (frame.type == swf.SWF.FRAME_LABEL):
                curLabel = swf.FrameLabel(frame).label
            elif (frame.type == swf.SWF.PLACE_OBJECT2):
                if curID == None: # needed for freaky idols
                    curID = swf.PlaceObject2(frame).character
            elif (frame.type == swf.SWF.SHOW_FRAME):
                if curID != None and curLabel != "":
                    self.lookup[curLabel] = curID

                curLabel = ""
                curID = None

def getFurniture() -> Furniture:
    return Furniture()

def exportFurniture(svgCropper: svg.SvgCropper, ffdecPath: str, furniture: Furniture, outfolder = "./out"):
    furnDir = ffdec.exportSpritesIfNeeded(ffdecPath, FURNITURE_SWF)
    dirs = os.listdir(furnDir)

    count = 0

    dirLUT = {}
    for d in dirs:
        dirLUT[d.split('_')[1]] = d

    outfolder += "/furniture"
    if (os.path.isdir(outfolder)):
        shutil.rmtree(outfolder)

    for name, id in furniture.lookup.items():
        dir = dirLUT.get(str(id))

        if dir != None:
            fullPath = os.path.join(furnDir, dir)

            outBase = outfolder + "/FURNITURE "
            nlower = name.lower().replace('"', '')

            svgCropper.crop(fullPath + "/1.svg", outBase + nlower + ".svg")
            if (os.path.isfile(fullPath + "/2.svg")):
                svgCropper.crop(fullPath + "/2.svg", outBase + nlower + " (Rare)" + ".svg")
                count += 2
            elif (name != "autofeeder" and "special" not in name):
                logging.warning(f"furniture {name} has no rare variant!")
                count += 1
        else:
            logging.warning(f"furniture {name} has no associated DefineSprite!")

    return count
