from .util import parse_csv as csv
from .util import resource_sync as sync

import os

class Translations:
    csvs: list[csv.csv_data]

    def __init__(self, textdir: str):
        self.csvs = []

        dirs = os.listdir(textdir)
        for dir in dirs:
            fullpath = os.path.join(textdir, dir)
            self.csvs.append(csv.parse_csv(fullpath))

    def get(self, id: str, lang: str = "en") -> str:
        for translations in self.csvs:
            if (id in translations.data):
                return translations.get(id).get(lang)
            
        raise RuntimeError(f"{id} has no translations")

# not intended for normal use (no caching)
def produceTranslations(textDir: str):
    return Translations(textDir)

TRANSLATIONS = sync.ValueSync[Translations](produceTranslations)
TRANSLATION_DIR = "./data/data/text"

# translations are lazy loaded, this provides some relief for those with partial files
def getTranslations(translationDir: str = TRANSLATION_DIR) -> Translations:
    return TRANSLATIONS.get(translationDir)

def get(id: str, lang: str = "en") -> str:
    return getTranslations().get(id, lang)