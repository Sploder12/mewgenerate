from .util import parse_gon as gon
from .util import parse_lvl as lvl

from . import translations

import os
import shutil

EVENTS_FOLDER = "./data/data/events"

class Event:
    location: str
    
    def __init__(self, location: str, data):
        self.location = location
        self.data = data

    def getNextEvents(self) -> list[str]:
        def getnexts(data) -> list[str]:
            if isinstance(data, list):
                out: list[str] = []
                for dat in data:
                    out += getnexts(dat)

                return out

            if isinstance(data, dict):
                out: list[str] = []
                if ("event_now_same_cat" in data):
                    out.append(data.get("event_now_same_cat"))
                
                if ("event_now" in data):
                    out.append(data.get("event_now"))

                for id, entry in data.items():
                    out += getnexts(entry)
                
                return out
            
            return []

        return getnexts(self.data)
    
    def getBattles(self) -> list[str]:
        def getbattles(data) -> list[str]:
            if isinstance(data, list):
                out: list[str] = []
                for dat in data:
                    out += getbattles(dat)

                return out

            if isinstance(data, dict):
                out: list[str] = []
                if ("battle" in data):
                    out.append(data.get("battle"))

                for id, entry in data.items():
                    out += getbattles(entry)

                return out
            
            return []

        return getbattles(self.data)

def getEvents() -> dict[str, Event]:
    CHAPNAMES = gon.parse_gon("./data/data/chapter_id_enum.gon").get("chapter_names")
    out = {}

    files = os.listdir(EVENTS_FOLDER)
    for file in files:
        pth = os.path.join(EVENTS_FOLDER, file)
        
        chapter = os.path.basename(pth).split('_')[0]
        if (chapter == "sewer"):
            chapter = "sewers"

        chaptername = CHAPNAMES.setdefault(chapter, "Unknown")
        if (chapter == "dead" or chapter == "monster" or chapter == "misc" or chapter == "npc" or chapter == "treasure" or chapter == "legacy"):
            chaptername = "Common"

        if (chaptername != "Unknown" and chaptername != "Common"):
            chaptername = translations.get(chaptername)
            if ("Das " in chaptername):
                chaptername = "The Future"

        dat = gon.parse_gon(pth)
        for id, data in dat.items():
            if (id == "__COMMENTS__"):
                continue
            
            if (id in out):
                raise RuntimeError(f"Duplicate event {id}")

            out[id] = Event(chaptername, data)

    return out

def exportEvents(events: dict[str, Event], outfolder = "./out"):
    count = 0
    outfolder += "/events"
    if (os.path.isdir(outfolder)):
        shutil.rmtree(outfolder)

    os.makedirs(outfolder)

    areaEvents = {}

    tnames = {}

    for id, event in events.items():
        out = []
        def follow(id: str, event: Event, events: dict[str, Event]) -> list[str]:
            nonlocal out
            if (id in out):
                return []
            
            out.append(id)
            tnames[id] = "(No title)" if "intro" not in event.data else event.data["intro"]["title"]
            adj = event.getNextEvents()
            for other in adj:
                if (other == "random"):
                    continue

                out += follow(other, events[other], events)

            return out
        
        nodes = follow(id, event, events)

        for node in nodes:
            areaEvents.setdefault(event.location, [])

            if (node not in areaEvents.get(event.location)):
                areaEvents.get(event.location).append(node)

    
    SUMMARY_ORDER = [
        "Common",
        
        "The Alley",
        "The Sewers",
        "The Junkyard",
        "The Caves",
        "The Boneyard",
        "The Throbbing Domain",

        "The Desert",
        "The Bunker",
        "The Crater",
        "The Core",
        "The Moon",
        "The Rift",

        "The Lab",
        "The Ice Age",
        "The Future",
        "The Jurassic",
        "The End",
        "The Infinite"
    ]
    with open(outfolder + "/summary.txt", "w") as summary:
        for area in SUMMARY_ORDER:
            summary.write(f"== {area} ==\n")

            eventz = areaEvents.setdefault(area, [])
            for ev in eventz:
                battles = list(dict.fromkeys(events.get(ev).getBattles()))

                if (tnames[ev] == "(No title)"):
                    name = f"{ev} (No title)"
                else:
                    try:
                        name = translations.get(tnames[ev])
                    except:
                        name = f"{tnames[ev]} (No Translation?)"

                summary.write(f"{name}")

                enemies = []
                if (len(battles) > 0):
                    for battle in battles:
                        if (".lvl" not in battle):
                            battle += ".lvl"

                        level = lvl.parse_lvl("./data/levels/" + battle)
                        sgon = gon.parse_gon("./data/data/" + level.spawnGon)
                        for spawn in level.spawns:
                            if (spawn.id == 0 or str(spawn.id) not in sgon):
                                continue
                            
                            d = sgon.get(str(spawn.id))
                            cat = d.get("editor").get("category")
                            if (cat < 2 or cat > 11):
                                continue

                            enemies.append(d["object"])


                    summary.write(f": {', '.join(enemies)}")
                summary.write('\n')

            summary.write('\n')
        
    return count
        

        

            




            


