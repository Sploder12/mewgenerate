
from .util import parse_gon as gon
from .util import ffdec_tools as ffdec
from .util import svg_tools as svg
from .util import parse_swf as swf

from . import translations

import os
import shutil

STATUS_SWF = "./data/swfs/ui.swf"

STATUS_ID = "StatusIcon"

import pathlib

class Status:
    name: str


def exportStatuses(svgCropper: svg.SvgCropper, ffdecPath: str, statuses: list[Status], outdir: str):
    # this sucks
    statusDir = ffdec.exportSpritesIfNeeded(ffdecPath, STATUS_SWF)

    #ffdec.export(ffdecPath, STATUS_SWF, ["shape"], "./cache/" + pathlib.Path(STATUS_SWF).stem)
    dumpdir = "./cache/ui"

    outdir += "/status"
    if (os.path.isdir(outdir)):
        shutil.rmtree(outdir)

    os.makedirs(outdir)

    statusSwf = swf.parse_swf(STATUS_SWF)
    
    dsprites = swf.getAllSprites(statusSwf)
    stable = swf.getSymbolTable(statusSwf)

    count = 0

    iconTags = dsprites[stable["StatusIcon"]]
    for tag in iconTags.tags:
        if (tag.type == swf.SWF.PLACE_OBJECT2):
            
            po2 = swf.PlaceObject2(tag)
            if (po2.character != 3072):
                if (po2.character not in dsprites):
                    count += 1
                    svgCropper.crop(f"{dumpdir}/{po2.character}.svg", f"{outdir}/{count}.svg")

                    continue
                else:
                    count += 1
                    svgCropper.crop(f"./cache/swfdump/ui/DefineSprite_{po2.character}/1.svg", f"{outdir}/{count}.svg")

                    continue
    
    return count