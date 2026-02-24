import src.util.parse_csv as csv
import src.util.parse_gon as gon
import src.util.parse_swf as swf
import src.status_effects as sf
import src.mutations as mutations
import src.items as items
import src.furniture as furniture
import src.util.ffdec_tools as ffdec

import src.util.svg_tools as svg

import src.util.parse_lvl as lvl

from typing import Any, Tuple

import os
import shutil

os.makedirs("./out", exist_ok=True)
os.makedirs("./out/icons", exist_ok=True)
os.makedirs("./out/furniture", exist_ok=True)
os.makedirs("./out/enemies", exist_ok=True)
os.makedirs("./out/enemies2", exist_ok=True)
os.makedirs("./out/enemies3", exist_ok=True)
os.makedirs("./out/enemies4", exist_ok=True)
os.makedirs("./out/catparts", exist_ok=True)
os.makedirs("./out/abilities", exist_ok=True)
os.makedirs("./out/npcs", exist_ok=True)
os.makedirs("./out/levels/computed", exist_ok=True)

ffdecPath = "C:/Program Files (x86)/FFDec/ffdec-cli.exe"
inkscapePath = "C:/Program Files/Inkscape/bin/inkscape.com"

with open("./out/mutations.txt", "w") as out:
    out.write(mutations.makeAllTables(ffdecPath))

ICONS_SWF = "./data/swfs/portraits.swf"

dumpdir = ffdec.exportSpritesIfNeeded(ffdecPath, ICONS_SWF, ffdec.SWF_DUMP_DIR)

dirs = os.listdir(dumpdir)
for dir in dirs:
    break
    fullPath = os.path.join(dumpdir, dir)
    if (os.path.isdir(fullPath)) and dir.startswith("DefineSprite"):
        name = '_'.join(dir.split('_')[2:])
        if (name == ""):
            name = dir.split('_')[1]

        files = dirs = os.listdir(fullPath)
        for file in files:
            p = os.path.join(fullPath, file)
            fname = name + "_" + file

            shutil.copyfile(p, f"./out/icons/{fname}")


items.exportItems(ffdecPath, items.getItems())

def doFurniture():
    furn, furnDir = furniture.getFurniture(ffdecPath)
    dirs = os.listdir(furnDir)

    dirLUT = {}
    for d in dirs:
        dirLUT[d.split('_')[1]] = d

    cropper = svg.SvgCropper(inkscapePath)
    for name, id in furn.lookup.items():
        dir = dirLUT.get(str(id))

        if dir != None:
            fullPath = os.path.join(furnDir, dir)

            outBase = "./out/furniture/FURNITURE "
            nlower = name.lower().replace('"', '')

            cropper.crop(fullPath + "/1.svg", outBase + nlower + ".svg")
            if (os.path.isfile(fullPath + "/2.svg")):
                cropper.crop(fullPath + "/2.svg", outBase + nlower + " (Rare)" + ".svg")
            else:
                print(f"WARNING:furniture {name} has no rare variant!")
        else:
            print(f"WARNING: furniture {name} has no associated DefineSprite!")

    cropper.finish()

doFurniture()

ICONS_SWF = "./data/swfs/ability_icons.swf"

dumpdir = ffdec.exportSpritesIfNeeded(ffdecPath, ICONS_SWF, ffdec.SWF_DUMP_DIR)

dirs = os.listdir(dumpdir)
for dir in dirs:
    break
    fullPath = os.path.join(dumpdir, dir)
    if (os.path.isdir(fullPath)) and dir.startswith("DefineSprite"):
        name = '_'.join(dir.split('_')[2:])
        if (name == ""):
            name = dir.split('_')[1]

        files = dirs = os.listdir(fullPath)
        for file in files:
            p = os.path.join(fullPath, file)
            fname = name + "_" + file

            shutil.copyfile(p, f"./out/abilities/{fname}")


areaObjs = {}
objsArea = {}

import json
for root, dirs, files in os.walk("./data/levels"):
    break
    for file in files:

        # we can't parse these :(
        if (file == "blank.lvl" or file == "flys.lvl" or file == "rats.lvl" or file == "slimeboss.lvl"):
            continue

        full_path = os.path.join(root, file)
        levl = lvl.parsed_lvl_resolved(full_path)

        outpath = "./out/" + full_path.removeprefix("./data/").removesuffix(".lvl") + ".json"

        area = root.removeprefix("./data/levels\\").split('\\')[0]
        if (not area.endswith('.json') and '/' not in area):
            objs = levl.get_unique_objects()
            areaObjs.setdefault(area, dict()).update(objs)

            for obj in objs.items():
                objsArea.setdefault(obj[0], {"data": obj[1]}).setdefault("areas", [])

                if (area not in objsArea[obj[0]]["areas"]):
                    objsArea[obj[0]]["areas"].append(area)


        tiles = []
        for y in range(10):
            tiles.append([])
            for x in range(10):
                tile = levl.tiles[y * 10 + x]
                tiles[y].append({"id": tile[0], "tile": tile[1]})

        spawns = []
        for spawn in levl.spawns:
            spawns.append({"x": spawn.x, "y": spawn.y, "spawnID": spawn.id, "spawn": spawn.data})
                
        os.makedirs('\\'.join(outpath.split('\\')[:-1]), exist_ok=True)
        data = {"spawns": spawns, "tiles": tiles}
        with open(outpath, "w") as jfile:
            jfile.write(json.dumps(data, indent=4))

exit(0)
with open("./out/levels/computed/areaObjs.json", "w") as jfile:
    jfile.write(json.dumps(areaObjs, indent=4))

with open("./out/levels/computed/objsArea.json", "w") as jfile:
    jfile.write(json.dumps(objsArea, indent=4))
