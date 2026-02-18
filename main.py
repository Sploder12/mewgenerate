import src.parse_csv as csv
import src.parse_gon as gon
import src.status_effects as sf
import src.mutations as mutations

from typing import Any, Tuple

import os
os.makedirs("./out", exist_ok=True)

with open("./out/mutations.txt", "w") as out:
    out.write(mutations.makeAllTables("C:/Program Files (x86)/FFDec/ffdec-cli.exe"))
