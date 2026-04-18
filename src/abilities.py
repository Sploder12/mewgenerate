from . import translations

from .util import ffdec_tools as ffdec
from .util import parse_gon as gon
from .util import svg_tools as svg
from .util import parse_swf as swf

from typing import Any

import logging
import os
import shutil

ICONS_SWF = "./data/swfs/ability_icons.swf"

ABILITIES_CSV = "./data/data/text/abilities.csv"
PASSIVES_CSV = "./data/data/text/passives.csv"

ABILITIES_FOLDER = "./data/data/abilities"
PASSIVES_FOLDER = "./data/data/passives"

class Passive:
    name: str
    desc: str
    multiclass: str
    collar: str

    id: str
    frame: int

    data: Any

    def __init__(self, id: str, frame: int, gondata):
        self.name = gondata.get("name")
        self.desc = gondata.get("desc")
        self.multiclass = gondata.setdefault("desc_multiclass", "")
        self.collar = gondata.setdefault("class", "")

        self.id = id
        self.frame = frame

        self.data = gondata

    def resolve(self, lang = "en"):
        self.name = translations.get(self.name, lang)

        # who cares (handling variants is for another day)
        # self.desc = translations.get(self.desc, lang)
        if (self.multiclass != ""):
            self.multiclass = translations.get(self.multiclass, lang)


class Active:
    name: str
    desc: str
    collar: str

    id: str
    frame: int

    data: Any

    def __init__(self, id: str, frame: int, gondata):
        meta = gondata.get("meta")
        self.name = meta.get("name")
        self.desc = meta.get("desc")
        self.collar = meta.setdefault("class", "")

        self.id = id
        self.frame = frame

        self.data = gondata

    def resolve(self, lang = "en"):
        self.name = translations.get(self.name, lang)

        # who cares (handling variants is for another day)
        #self.desc = translations.get(self.desc, lang)

        if '/' in self.name:
            logging.warning(f"Active {self.name} being truncated")
            self.name = self.name.split('/')[-1]



def getPassives() -> list[Passive]:
    swftags = swf.parse_swf(ICONS_SWF)

    dsprites = swf.getAllSprites(swftags)
    stable = swf.getSymbolTable(swftags)
    frames = swf.splitSpriteFrames(dsprites[stable["PassiveIcon"]])

    frameDict = {frame.name: i for i, frame in enumerate(frames)}
    
    out = []

    files = os.listdir(PASSIVES_FOLDER)
    for file in files:
        fullpath = os.path.join(PASSIVES_FOLDER, file)
        gondata = gon.parse_gon(fullpath)

        for id, data in gondata.items():
            if (id == "__COMMENTS__" or id not in frameDict):
                continue

            out.append(Passive(id, frameDict[id], data))

    return out

def exportPassives(svgCropper: svg.SvgCropper, ffdecPath: str, passives: list[Passive], outfolder = "./out"):
    dumpdir = ffdec.exportSpritesIfNeeded(ffdecPath, ICONS_SWF)
    dirs = os.listdir(dumpdir)
    for dir in dirs:
        if (dir.endswith("PassiveIcon")):
            dumpdir = os.path.join(dumpdir, dir)
            break
    
    outfolder += "/abilities/passive"
    if (os.path.isdir(outfolder)):
        shutil.rmtree(outfolder)

    count = 0
    for passive in passives:
        passive.resolve()
        src = os.path.join(dumpdir, f"{passive.frame}.svg")
        dst = os.path.join(outfolder, f'ABILITY {passive.name.replace("?", "%3F")}.svg')
        svgCropper.crop_handle_duplicate(src, dst)
        count += 1

    return count


def getActives() -> list[Active]:
    swftags = swf.parse_swf(ICONS_SWF)

    dsprites = swf.getAllSprites(swftags)
    stable = swf.getSymbolTable(swftags)
    frames = swf.splitSpriteFrames(dsprites[stable["AbilityIcon"]])

    frameDict = {frame.name: i for i, frame in enumerate(frames)}
    
    out = []

    files = os.listdir(ABILITIES_FOLDER)
    for file in files:
        fullpath = os.path.join(ABILITIES_FOLDER, file)
        gondata = gon.parse_gon(fullpath)

        for id, data in gondata.items():
            if (id == "__COMMENTS__" or id not in frameDict):
                continue

            if ("meta" not in data):
                continue

            out.append(Active(id, frameDict[id], data))

    return out

def exportActives(svgCropper: svg.SvgCropper, ffdecPath: str, actives: list[Active], outfolder = "./out"):
    dumpdir = ffdec.exportSpritesIfNeeded(ffdecPath, ICONS_SWF)
    dirs = os.listdir(dumpdir)
    for dir in dirs:
        if (dir.endswith("AbilityIcon")):
            dumpdir = os.path.join(dumpdir, dir)
            break

    outfolder += "/abilities/active"
    if (os.path.isdir(outfolder)):
        shutil.rmtree(outfolder)

    count = 0
    for active in actives:
        active.resolve()
        src = os.path.join(dumpdir, f"{active.frame}.svg")
        dst = os.path.join(outfolder, f"ABILITY {active.name.replace('?', "%3F")}.svg")
        svgCropper.crop_handle_duplicate(src, dst)
        count += 1

    return count

