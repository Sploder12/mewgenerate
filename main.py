import src.parse_csv as csv
import src.parse_gon as gon
import src.keywords as keywords

from typing import Any, Tuple


words = keywords.collect_keywords()

mutationStrings = csv.parse_csv("./data/data/text/mutations.csv")
passiveStrings = csv.parse_csv("./data/data/text/passives.csv")


bodys = gon.parse_gon("./data/data/mutations/body.gon")
ears = gon.parse_gon("./data/data/mutations/ears.gon")
eyebrows = gon.parse_gon("./data/data/mutations/eyebrows.gon")
eyes = gon.parse_gon("./data/data/mutations/eyes.gon")
heads = gon.parse_gon("./data/data/mutations/head.gon")
legs = gon.parse_gon("./data/data/mutations/legs.gon")
mouths = gon.parse_gon("./data/data/mutations/mouth.gon")
tails = gon.parse_gon("./data/data/mutations/tail.gon")
textures = gon.parse_gon("./data/data/mutations/texture.gon")

def int_to_str_signed(value: int) -> str:
    return"+" + str(value) if value >= 0 else str(value)

def stat_to_string(stat: str, value: int):
    return f"{{{{stat|{stat}|{int_to_str_signed(value)}}}}}"

class TableEntry:
    name: str
    stats: list[int]
    shield: int
    desc: str

    def __init__(self):
        self.name = "?"
        self.stats = [0, 0, 0, 0, 0, 0, 0]
        self.shield = 0
        self.desc = ""

class Table:
    entries: list[TableEntry]

    def __init__(self):
        self.entries = []

    def toString(self) -> str:
        out = ""

        for entry in self.entries:
            out += "|-\n"
            out += f"| TBA || {entry.name} ||\n"
            
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


def toTables(gon) -> Tuple[Table, Table]:
    mutations = Table()
    defects = Table()

    for entry in gon.values():
        if (not isinstance(entry, dict)):
            continue # ignore comments

        out = TableEntry()
        isDefect = False

        if ("desc" in entry):
            descID = entry.get("desc")
            if (descID not in mutationStrings.data):
                raise RuntimeError("description id missing from translations!")
            
            translations = mutationStrings.data.get(descID).translations
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


bodyMutations, bodyDefects = toTables(bodys.get("body"))

print(makeTable("Body Mutations", bodyMutations))