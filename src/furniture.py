from .catgen import swf_tree as swf
from .catgen import sprite as sprite
from .util import ffdec_tools as ffdec
from .util import svg_tools as svg

from .util import parse_gon as gon
from . import translations

import os
import shutil
import logging

FURNITURE_SWF = "./data/swfs/furniture.swf"
FURNITURE_GON = "./data/data/furniture_effects.gon"

def exportFurniture(svgCropper: svg.SvgCropper, ffdecPath: str, outfolder = "./out"):
    furnDir = ffdec.exportShapesIfNeeded(ffdecPath, FURNITURE_SWF)
    spriteTree = swf.getSwfTree(FURNITURE_SWF)
    sprites = spriteTree.get("Furniture")

    if (not isinstance(sprites, swf.SWF_Tree.SpriteNode)):
        raise RuntimeError("DefineSprite \"Furniture\" does not exist!")

    outfolder += "/furniture"
    if (os.path.isdir(outfolder)):
        shutil.rmtree(outfolder)
    os.makedirs(outfolder)

    count = 0
    for i in range(len(sprites.frames)):
        furniture = sprites.frames[i]
        if (furniture.name == ""):
            continue

        outName = furniture.name.lower().replace('"', '')

        outnameBase = f"{outfolder}/FURNITURE {outName}"
        if (furniture.name.startswith("special") or furniture.name in {"poop", "corpse", "autofeeder"}):
            basic = sprite.spriteFromNode(furnDir, spriteTree, sprites, i)

        else:
            assert(len(furniture.objs) >= 1)
            if (len(furniture.objs) > 1):
                logging.info(f"{furniture.name} has {len(furniture.objs)} objs")

            basics = []
            rares = []
            for obj in furniture.objs:
                variations = spriteTree.get(obj.id)
                assert(isinstance(variations, swf.SWF_Tree.SpriteNode) and len(variations.frames) == 2)

                basic = sprite.spriteFromNode(furnDir, spriteTree, variations, 0)
                basic.applyTransform(obj.cxform).applyTransform(obj.xform)
                basics.append(basic)

                rare = sprite.spriteFromNode(furnDir, spriteTree, variations, 1)
                rare.applyTransform(obj.cxform).applyTransform(obj.xform)
                rares.append(rare)

            basic = sprite.mergeSprites(basics)
            rare = sprite.mergeSprites(rares)

            with open(outnameBase + " (Rare).svg", "w") as rout:
                rout.write(rare.compile())
            svgCropper.crop(outnameBase + " (Rare).svg", outnameBase + " (Rare).svg")
            count += 1

        with open(outnameBase + ".svg", "w") as bout:
            bout.write(basic.compile())
        svgCropper.crop(outnameBase + ".svg", outnameBase + ".svg")
        count += 1

    return count
