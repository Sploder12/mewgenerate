from .util import parse_csv as csv

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

TRANSLATIONS = Translations("./data/data/text")
