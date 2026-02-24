# this file does *magic* :)

from .util import parse_csv as csv
from .util import parse_gon as gon
from .util import parse_swf as swf
from .util import ffdec_tools as ffdec
from .util import svg_tools as svg

CUSTOM_CAT_GON = "./data/data/custom_cats.gon"
CATPARTS_SWF = "./data/swfs/catparts.swf"

class CustomCat:
    class Part:
        frame: int
        texture: int

        def __init__(self, defaultTex: int, defaultFrame: int, data = None):
            if (data == None):
                self.texture = defaultTex
                self.frame = defaultFrame
                return

            if (isinstance(data, str) or isinstance(data, int)):
                self.frame = int(data)
                self.texture = defaultTex
            else:
                self.frame = int(data.setdefault("frame", defaultFrame))
                self.texture = data.setdefault("texture", defaultTex)

    id: str

    voice = ""
    pitch = 1.0

    class_anis = ""
    default_frame = 1

    texture = 1
    palette = 1
   
    body: Part
    tail: Part
    
    leg1: Part
    leg2: Part
    arm1: Part
    arm2: Part
    claws: Part

    head: Part
    lefteye: Part
    righteye: Part
    lefteyebrow: Part
    righteyebrow: Part
    leftear: Part
    rightear: Part
    mouth: Part

    def __init__(self, name: str, gondata):
        self.id = name

        self.voice = gondata.setdefault("voice", self.default_frame)
        self.pitch = float(gondata.setdefault("pitch", self.pitch))

        self.class_anis = gondata.setdefault("class_anis", self.class_anis)
        self.default_frame = int(gondata.setdefault("default_frame", self.default_frame))

        self.texture = int(gondata.setdefault("texture", self.texture))
        self.palette = int(gondata.setdefault("palette", self.palette))

        self.body = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("body", None))
        self.tail = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("tail", None))
        
        self.leg1 = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("leg1", None))
        self.leg2 = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("leg2", None))
        self.arm1 = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("arm1", None))
        self.arm2 = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("arm2", None))
        self.claws = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("claws", None))

        self.head = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("head", None))
        self.lefteye = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("lefteye", None))
        self.righteye = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("righteye", None))
        self.lefteyebrow = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("lefteyebrow", None))
        self.righteyebrow = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("righteyebrow", None))
        self.leftear = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("leftear", None))
        self.rightear = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("rightear", None))
        self.mouth = CustomCat.Part(self.texture, self.default_frame, gondata.setdefault("mouth", None))


def getCustomCats() -> list[CustomCat]:
    data = gon.parse_gon(CUSTOM_CAT_GON)

    out: list[CustomCat] = []
    for id, cat in data.items():
        if (id == "__COMMENTS__"):
            continue

        out.append(CustomCat(id, cat))

    return out

def exportCustomCats(svgCropper: svg.SvgCropper, ffdecPath: str,cats: list[CustomCat]):
    partDir = ffdec.exportSpritesIfNeeded(ffdecPath, CATPARTS_SWF)

    count = 0

    return count


