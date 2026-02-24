from .util import parse_csv as csv
from .util import parse_gon as gon
from .util import ffdec_tools as ffdec

from typing import Tuple

import os

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
