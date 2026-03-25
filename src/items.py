from .util import parse_csv as csv
from .util import parse_gon as gon
from .util import ffdec_tools as ffdec
from .util import svg_tools as svg

import os
import shutil

from typing import Any

from . import translations

ITEMS_SWF = "./data/swfs/catparts.swf"

ITEMS_FOLDER = "./data/data/items"
ITEMS_GONS = [
    "armor_sets.gon",
    "beanies_quest_items.gon",
    "consumables.gon",
    "cursed_items.gon",
    "face_items.gon",
    "head_items.gon",
    "legacy_quest_items.gon",
    "legendary_items.gon",
    "neck_items.gon",
    "parasites.gon",
    "special_class_items.gon",
    "trinkets.gon",
    "weapons.gon"
]

KIND_MAP = {
    "face": "FaceItemIcon",
    "head": "HeadItemIcon",
    "neck": "NeckItemIcon",
    "trinket": "TrinketIcon",
    "weapon": "WeaponIcon",
}

class Item:
    variant: str | None
    name: str
    translationID: str
    desc: str
    rarity: str
    kind: str
    frame: int

    data: dict[str, Any]

    def __init__(self, name: str, gondata: dict[str, Any]):
        self.name = name

        self.variant = None
        if "variant_of" in gondata:
            self.variant = gondata["variant_of"]

            self.data = gondata.copy()
            self.data.pop("variant_of")
        
        else:
            self.translationID = gondata["name"]
            self.desc = gondata["desc"]
            self.kind = gondata["kind"]
            self.frame = int(gondata["frame"])

            self.data = gondata.copy()
            self.data.pop("name")
            self.data.pop("desc")
            self.data.pop("kind")
            self.data.pop("frame")

        
        
        

def getItems() -> list[Item]:
    items: list[Item] = []
    for gonname in ITEMS_GONS:
        gondata = gon.parse_gon(ITEMS_FOLDER + '/' + gonname)
        for name, data in gondata.items():
            if (name == "__COMMENTS__" or data == None):
                continue

            items.append(Item(name, data))

    return items

def getItemDict() -> dict[str, Item]:
    items: dict[str, Item] = {}
    for gonname in ITEMS_GONS + ["enemy_items.gon"]:
        gondata = gon.parse_gon(ITEMS_FOLDER + '/' + gonname)
        for name, data in gondata.items():
            if (name == "__COMMENTS__" or data == None):
                continue

            items[name] = Item(name, data)

    return items


def exportItems(svgCropper: svg.SvgCropper, ffdecPath: str, items: list[Item], outfolder = "./out") -> int:
    dumpdir = ffdec.exportSpritesIfNeeded(ffdecPath, ITEMS_SWF, ffdec.SWF_DUMP_DIR)

    count = 0

    foldermap = {}
    dirs = os.listdir(dumpdir)
    for kind, id in KIND_MAP.items():
        for dir in dirs:
            if dir.endswith(id):
                foldermap[kind] = os.path.join(dumpdir, dir)
                break

    outfolder += "/items"
    if (os.path.isdir(outfolder)):
        shutil.rmtree(outfolder)

    for item in items:
        if (item.variant != None):
            continue

        src = foldermap.get(item.kind) + f"/{item.frame}.svg"

        folder = outfolder + "/" + item.kind

        en = translations.get(item.translationID)

        out = folder + "/ITEM " + en + ".svg"
        if os.path.exists(out):
            folder += "/dupes/" 
            os.makedirs(folder, exist_ok=True)
            shutil.move(out, folder + "/ITEM " + en + ".svg")

            out = folder + "/ITEM " + en + ".svg"
            
        os.makedirs(folder, exist_ok=True)
        with open(src, "r") as xml:
            content = xml.readlines()

        outlines = []
        for line in content:
            if ("id=\"sloticon\"" in line):
                continue

            outlines.append(line)

        with open(src, "w") as xmlout:
            xmlout.write(''.join(outlines))   

        svgCropper.crop_handle_duplicate(src, out)  
        count += 1

    return count

    
