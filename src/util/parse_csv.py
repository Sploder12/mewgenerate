# this file handles parsing CSVs for language strings
import csv

class csv_values:
    notes: str
    translations: dict[str, str]

    def __init__(self):
        self.notes = ""
        self.translations = {}

    def get(self, language: str = "en"):
        return self.translations.get(language)


class csv_data:
    header: list[str]
    data: dict[str, csv_values]

    def __init__(self, header: list[str]):
        if ("KEY" not in header):
            # we don't know what to do with this
            raise RuntimeError(f"invalid csv header {header}")

        self.header = header
        self.data = {}

    def get(self, id: str):
        return self.data.get(id)

    def add_row(self, row: list[str]):
        if (len(self.header) != len(row)):
            # we don't know what to do with this
            raise RuntimeError(f"invalid csv row {row}")

        values = csv_values()
        key = ""

        for i in range(len(self.header)):
            currentType = self.header[i]
            currentValue = row[i]

            if (currentType == "KEY"):
                key = currentValue
            elif (currentType == "notes"):
                values.notes = currentValue
            else:
                values.translations[currentType] = currentValue
        
        self.data[key] = values

def parse_csv(filepath: str) -> csv_data:
    with open(filepath, newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        
        out = csv_data(next(reader))
        for row in reader:
            out.add_row(row)

        return out

        