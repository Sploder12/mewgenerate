from .util import parse_csv as csv
from .util import parse_gon as gon
from .util import ffdec_tools as ffdec

import os
import shutil

from typing import Any

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

ITEMS_CSV = "./data/data/text/items.csv"
ITEMS_TRANSLATIONS = csv.parse_csv(ITEMS_CSV)
ITEMS_TRANSLATIONS2 = csv.parse_csv("./data/data/text/additions.csv")

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

def exportItems(ffdecPath: str, items: list[Item], outfolder = "./out/items") -> str:
    dumpdir = ffdec.exportSpritesIfNeeded(ffdecPath, ITEMS_SWF, ffdec.SWF_DUMP_DIR)

    foldermap = {}
    dirs = os.listdir(dumpdir)
    for kind, id in KIND_MAP.items():
        for dir in dirs:
            if dir.endswith(id):
                foldermap[kind] = os.path.join(dumpdir, dir)
                break

    for item in items:
        if (item.variant != None):
            continue

        src = foldermap.get(item.kind) + f"/{item.frame}.svg"

        folder = outfolder + "/" + item.kind

        try:
            en = ITEMS_TRANSLATIONS.get(item.translationID).get()
        except:
            en = ITEMS_TRANSLATIONS2.get(item.translationID).get()

        out = folder + "/ITEM " + en + ".svg"
        if os.path.exists(out):
            folder += "/dupes/" 
            os.makedirs(folder, exist_ok=True)
            shutil.copyfile(out, folder + "/ITEM " + en + ".svg")

            i = 2
            out = folder + "/ITEM " + en + ' ' + str(i) + ".svg"
            while os.path.exists(out):
                i += 1
                out = folder + "/ITEM " + en + ' ' + str(i) + ".svg"
            
        os.makedirs(folder, exist_ok=True)
        shutil.copyfile(src, out)

        with open(out, "r") as xml:
            content = xml.readlines()

        outlines = []
        for line in content:
            if ("id=\"sloticon\"" in line):
                continue

            outlines.append(line)

        with open(out, "w") as xmlout:
            xmlout.write('\n'.join(outlines))        

        

    return dumpdir

    
