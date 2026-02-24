from .util import parse_swf as swf
from .util import parse_csv as csv
from .util import parse_gon as gon
from .util import ffdec_tools as ffdec

FURNITURE_SWF = "./data/swfs/furniture.swf"
FURNITURE_CSV = "./data/data/text/furniture.csv"
FURNITURE_GON = "./data/data/furniture_effects.gon"

FURNITURE_STRINGS = csv.parse_csv(FURNITURE_CSV)
FURNITURE_DATA = gon.parse_gon(FURNITURE_GON)
FURNITURE_SWF_TAGS = swf.parse_swf(FURNITURE_SWF)

class Furniture:
    lookup: dict[str, int]
    allSprites: dict[int, swf.DefineSprite]

    def __init__(self):
        self.lookup = {}
        self.allSprites = {}

        symbolTable = {}
        for tag in FURNITURE_SWF_TAGS.tags:
            if (tag.type == swf.SWF.SYMBOL_CLASS):
                sclass = swf.SymbolClass(tag)
                for symbol in sclass.symbols:
                    symbolTable[symbol[1]] = symbol[0]

        for tag in FURNITURE_SWF_TAGS.tags:
            if (tag.type == swf.SWF.DEFINE_SPRITE):
                dsprite = swf.DefineSprite(tag)
                self.allSprites[dsprite.id] = dsprite

        furnitureLUT = self.allSprites.get(symbolTable.get("Furniture"))

        curLabel = ""
        curID = None
        for frame in furnitureLUT.tags:
            if (frame.type == swf.SWF.FRAME_LABEL):
                curLabel = swf.FrameLabel(frame).label
            elif (frame.type == swf.SWF.PLACE_OBJECT2):
                if curID == None: # needed for freaky idols
                    curID = swf.PlaceObject2(frame).character
            elif (frame.type == swf.SWF.SHOW_FRAME):
                if curID != None and curLabel != "":
                    self.lookup[curLabel] = curID

                curLabel = ""
                curID = None

def getFurniture(ffdecPath: str) -> tuple[Furniture, str]:
    dumpdir = ffdec.exportSpritesIfNeeded(ffdecPath, FURNITURE_SWF, ffdec.SWF_DUMP_DIR)
    return (Furniture(), dumpdir)