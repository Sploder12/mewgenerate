from . import parse_csv as csv
from . import parse_gon as gon
from . import ffdec_tools as ffdec

from typing import Tuple

import os
import shutil
import pathlib

MUTATIONS_OUT_FOLDER = "./out/mutations"

MUTATIONS_FOLDER = "./data/data/mutations"
MUTATION_STRING_FILE = "./data/data/text/mutations.csv"
PARTS_SWF = "./data/swfs/catparts.swf"

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

MUTATION_STRINGS = csv.parse_csv(MUTATION_STRING_FILE)

def int_to_str_signed(value: int) -> str:
    return"+" + str(value) if value >= 0 else str(value)

def stat_to_string(stat: str, value: int):
    return f"{{{{stat|{stat}|{int_to_str_signed(value)}}}}}"

class TableEntry:
    name: str
    imagePath: str
    stats: list[int]
    shield: int
    desc: str

    def __init__(self):
        self.name = "?"
        self.imagePath = ""
        self.stats = [0, 0, 0, 0, 0, 0, 0]
        self.shield = 0
        self.desc = ""

class Table:
    entries: list[TableEntry]
    part: str
    defects: bool

    def __init__(self, part: str, defects: bool = False):
        self.entries = []
        self.part = part
        self.defects = defects

    def toString(self) -> str:
        out = ""

        for entry in self.entries:
            out += "|-\n"

            os.makedirs(MUTATIONS_OUT_FOLDER, exist_ok=True)
            id = pathlib.Path(entry.imagePath).stem
            try:
                filename = f"{"Mutation" if self.defects else "Mutation"}_{self.part.lower()}.{id}.svg"
                newPath = f"{MUTATIONS_OUT_FOLDER}/{filename}"
                shutil.copyfile(entry.imagePath, newPath)
            except FileNotFoundError:
                print(f"WARNING: INVALID MUTATION PART {id}, {entry.name}")
                filename = f"Mutation_{self.part.lower()}.703.svg"
                
            out += f"| [[File:{filename}]] || {entry.name} ||\n"
            
            if (entry.stats[0] != 0):
                out += f"* {stat_to_string("Strength", entry.stats[0])}\n"
            if (entry.stats[1] != 0):
                out += f"* {stat_to_string("Dexterity", entry.stats[1])}\n"
            if (entry.stats[2] != 0):
                out += f"* {stat_to_string("Constitution", entry.stats[2])}\n"
            if (entry.stats[3] != 0):
                out += f"* {stat_to_string("Intelligence", entry.stats[3])}\n"
            if (entry.stats[4] != 0):
                out += f"* {stat_to_string("Speed", entry.stats[4])}\n"
            if (entry.stats[5] != 0):
                out += f"* {stat_to_string("Charisma", entry.stats[5])}\n"
            if (entry.stats[6] != 0):
                out += f"* {stat_to_string("Luck", entry.stats[6])}\n"

            if (entry.shield != 0):
                out += f"* {int_to_str_signed(entry.shield)} Shield\n"
            
            if (len(entry.desc)):
                out += f"* {entry.desc}\n"

            out += "|\n"

        return out


def toTables(part:str, gon, defineSpriteDir: str) -> Tuple[Table, Table]:
    mutations = Table(part, False)
    defects = Table(part, True)

    for id, entry in gon.items():
        if (not isinstance(entry, dict)):
            continue # ignore comments

        out = TableEntry()
        out.imagePath = defineSpriteDir + f"/{id}.svg"

        isDefect = False

        if ("desc" in entry):
            descID = entry.get("desc")
            if (descID not in MUTATION_STRINGS.data):
                raise RuntimeError("description id missing from translations!")
            
            translations = MUTATION_STRINGS.get(descID).translations
            if ("en" not in translations):
                raise RuntimeError("description is missing English translation")

            out.desc = translations.get("en")

        if ("__COMMENTS__" in entry):
            comments = entry.get("__COMMENTS__")
            out.name = comments[0]

        if ("tag" in entry):
            tag = entry.get("tag")
            if (tag == "birth_defect"):
                isDefect = True

        if ("str" in entry):
            out.stats[0] = int(entry.get("str"))

        if ("dex" in entry):
            out.stats[1] = int(entry.get("dex"))

        if ("con" in entry):
            out.stats[2] = int(entry.get("con"))

        if ("int" in entry):
            out.stats[3] = int(entry.get("int"))

        if ("spd" in entry):
            out.stats[4] = int(entry.get("spd"))

        if ("cha" in entry):
            out.stats[5] = int(entry.get("cha"))

        if ("lck" in entry):
            out.stats[6] = int(entry.get("lck"))

        if ("shield" in entry):
            out.shield = int(entry.get("shield"))

        if (not isDefect):
            mutations.entries.append(out)
        else:
            defects.entries.append(out)

    return (mutations, defects)

def makeTable(title: str, data: Table) -> str:
    out = "{| class=\"wikitable mw-collapsible sortable\"\n"
    out += f"|+ {title}\n"
    out += "! Picture !! Name !! Effect !! Description\n"
    out += data.toString()
    out = out.removesuffix('\n')
    out += "}"

    return out

def makeAllTables(ffdecPath: str) -> str:
    dumpdir = ffdec.exportSpritesIfNeeded(ffdecPath, PARTS_SWF, ffdec.SWF_DUMP_DIR)

    mutations = []
    defects = []
    for (part, gonFile, swfID) in CATPARTS:
        data = gon.parse_gon(MUTATIONS_FOLDER + '/' + gonFile)

        key = ""
        for k in data.keys():
            if (k != "__COMMENTS__"):
                key = k
                break

        if (key == ""):
            raise RuntimeError("Invalid mutation gon file")

        muts, defs = toTables(part, data[key], ffdec.findDirectory(dumpdir, swfID))
        mutations.append(muts)
        defects.append(defs)
        
    out = "==Mutations==\n"
    for i in range(len(mutations)):
        if (len(mutations[i].entries) == 0):
            continue

        part = CATPARTS[i][0]

        out += f"==={part}===\n"
        out += makeTable(f"{part} Mutations", mutations[i])
        out += '\n'

    out += "==Birth Defects==\n"
    for i in range(len(defects)):
        if (len(defects[i].entries) == 0):
            continue

        part = CATPARTS[i][0]

        out += f"==={part}===\n"
        out += makeTable(f"{part} Defects", defects[i])
        out += '\n'

    return out
        
