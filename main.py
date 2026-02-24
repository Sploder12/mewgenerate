import src.status_effects as sf
import src.mutations as mutations
import src.items as items
import src.furniture as furniture
import src.util.ffdec_tools as ffdec

import src.util.svg_tools as svg

import logging
import os
import argparse
import threading
from datetime import datetime

ffdecDefault = "C:/Program Files (x86)/FFDec/ffdec-cli.exe" if os.name == "nt" else "ffdec-cli"
inkscapeDefault = "C:/Program Files/Inkscape/bin/inkscape.com" if os.name == "nt" else "inkscape"
outDirDefault = "./out"

def timedExport(name: str, exportFnc, inkscape: str, ffdec: str):
    start = datetime.now()
    with svg.SvgCropper(inkscape) as svgCropper:
        logging.info(f"Exporting {name}...")

        try:
            result = exportFnc(svgCropper, ffdec)
            delta = datetime.now() - start
            logging.info(f"Exported {result} {name} in {delta.seconds} seconds")
        except Exception as e:
            logging.error(f"Failed to export {name}: {e}")


def exportItems(svgCropper: svg.SvgCropper, ffdec: str):
    return items.exportItems(svgCropper, ffdec, items.getItems())

def exportFurniture(svgCropper: svg.SvgCropper, ffdec: str):
    return furniture.exportFurniture(svgCropper, ffdec, furniture.getFurniture())


VALID_VALUES = {
    "items": exportItems,
    "furniture": exportFurniture
}

def main():
    parser = argparse.ArgumentParser(
        prog="Mewgenerate",
        description=
        "A utility for parsing Mewgenics assets.\n"
        "Unpacked .gpak files should be placed in ./data\n"
        "Requires FFDec and Inkscape for full functionality"
    )

    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-o", "--out-dir", nargs=1, default=outDirDefault, help="Output file location, please use an empty directory. (default: %(default)s)")
    parser.add_argument("--ffdec", nargs=1, default=ffdecDefault, help="Path to ffdec-cli executable, used for dumping assets from SWF files. (default: %(default)s)")
    parser.add_argument("--inkscape", nargs=1, default=inkscapeDefault, help="Path to inkscape executable, used for cropping SVG assets. (default: %(default)s)")
    parser.add_argument("--force-redump", action="store_true", help="Ignores asset cache.")
    
    parser.add_argument("components", nargs="*", default=[], help=f"Components to export, blank for all. Valid values are \"{"\", \"".join(VALID_VALUES.keys())}\"")

    args = parser.parse_args()

    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO if not args.verbose else logging.DEBUG)
    if (args.force_redump):
        logging.debug("force-redump=True")
        ffdec.FORCE_REDUMP = True

    all = len(args.components) == 0

    logging.debug(f"components={"all" if all else args.components}")

    threads: list[threading.Thread] = []
    start = datetime.now()

    components = VALID_VALUES.keys() if all else list(dict.fromkeys(args.components))
    for component in components:
        if (component not in VALID_VALUES):
            logging.warning(f"{component} is not a valid component")
            continue

        t = threading.Thread(target=timedExport, args=(component, VALID_VALUES[component], args.inkscape, args.ffdec))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    delta = datetime.now() - start
    logging.info(f"Finished exporting in {delta.seconds} seconds")

#ICONS_SWF = "./data/swfs/portraits.swf"
#
#dumpdir = ffdec.exportSpritesIfNeeded(ffdecPath, ICONS_SWF, ffdec.SWF_DUMP_DIR)
#
#dirs = os.listdir(dumpdir)
#for dir in dirs:
#    break
#    fullPath = os.path.join(dumpdir, dir)
#    if (os.path.isdir(fullPath)) and dir.startswith("DefineSprite"):
#        name = '_'.join(dir.split('_')[2:])
#        if (name == ""):
#            name = dir.split('_')[1]
#
#        files = dirs = os.listdir(fullPath)
#        for file in files:
#            p = os.path.join(fullPath, file)
#            fname = name + "_" + file
#
#            shutil.copyfile(p, f"./out/icons/{fname}")




#ICONS_SWF = "./data/swfs/ability_icons.swf"

#dumpdir = ffdec.exportSpritesIfNeeded(ffdecPath, ICONS_SWF, ffdec.SWF_DUMP_DIR)

# dirs = os.listdir(dumpdir)
# for dir in dirs:
#     break
#     fullPath = os.path.join(dumpdir, dir)
#     if (os.path.isdir(fullPath)) and dir.startswith("DefineSprite"):
#         name = '_'.join(dir.split('_')[2:])
#         if (name == ""):
#             name = dir.split('_')[1]

#         files = dirs = os.listdir(fullPath)
#         for file in files:
#             p = os.path.join(fullPath, file)
#             fname = name + "_" + file

#             shutil.copyfile(p, f"./out/abilities/{fname}")


# areaObjs = {}
# objsArea = {}

# import json
# for root, dirs, files in os.walk("./data/levels"):
#     break
#     for file in files:

#         # we can't parse these :(
#         if (file == "blank.lvl" or file == "flys.lvl" or file == "rats.lvl" or file == "slimeboss.lvl"):
#             continue

#         full_path = os.path.join(root, file)
#         levl = lvl.parsed_lvl_resolved(full_path)

#         outpath = "./out/" + full_path.removeprefix("./data/").removesuffix(".lvl") + ".json"

#         area = root.removeprefix("./data/levels\\").split('\\')[0]
#         if (not area.endswith('.json') and '/' not in area):
#             objs = levl.get_unique_objects()
#             areaObjs.setdefault(area, dict()).update(objs)

#             for obj in objs.items():
#                 objsArea.setdefault(obj[0], {"data": obj[1]}).setdefault("areas", [])

#                 if (area not in objsArea[obj[0]]["areas"]):
#                     objsArea[obj[0]]["areas"].append(area)


#         tiles = []
#         for y in range(10):
#             tiles.append([])
#             for x in range(10):
#                 tile = levl.tiles[y * 10 + x]
#                 tiles[y].append({"id": tile[0], "tile": tile[1]})

#         spawns = []
#         for spawn in levl.spawns:
#             spawns.append({"x": spawn.x, "y": spawn.y, "spawnID": spawn.id, "spawn": spawn.data})
                
#         os.makedirs('\\'.join(outpath.split('\\')[:-1]), exist_ok=True)
#         data = {"spawns": spawns, "tiles": tiles}
#         with open(outpath, "w") as jfile:
#             jfile.write(json.dumps(data, indent=4))

# exit(0)
# with open("./out/levels/computed/areaObjs.json", "w") as jfile:
#     jfile.write(json.dumps(areaObjs, indent=4))

# with open("./out/levels/computed/objsArea.json", "w") as jfile:
#     jfile.write(json.dumps(objsArea, indent=4))





if __name__ == "__main__":
    main()