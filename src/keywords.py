from . import parse_csv as csv
from . import parse_gon as gon

class Tooltip:
    name: str
    desc: str

    def __init__(self, name, desc):
        self.name = name
        self.desc = desc

    def translate(self, translations: csv.csv_data, language: str = "en"):
        tname = translations.get(self.name).get(language)
        tdesc = translations.get(self.desc).get(language)
        return Tooltip(tname, tdesc)

class Keyword:
    basic: Tooltip | None
    stacks: Tooltip | None
    stackless: Tooltip | None
    singular: Tooltip | None
    positive: Tooltip | None
    negative: Tooltip | None
    referenceApplier: Tooltip | None

    comments: list[str]
    aliasOf: str

    def __init__(self):
        self.basic = None
        self.stacks = None
        self.stackless = None
        self.singular = None
        self.positive = None
        self.negative = None
        self.referenceApplier = None

        comments = []
        aliasOf = "" # if this is populated nothing else will be (except maybe comments)

    def is_alias(self) -> bool:
        return self.aliasOf != ""

    def get(self, stacksize: int) -> Tooltip | None:
        if (stacksize == 1 and self.singular != None):
            return self.singular
        
        if (stacksize > 0 and self.positive != None):
            return self.positive
        
        if (stacksize < 0 and self.negative != None):
            return self.negative
        
        if (stacksize == 0 and self.stackless != None):
            return self.stackless
        
        if (stacksize != 0 and self.stacks != None):
            return self.stacks
        
        return self.basic

    def getApplier(self) -> Tooltip | None:
        if (self.referenceApplier != None):
            return self.referenceApplier
        
        return self.basic
    

class Keywords:
    keywords: dict[str, Keyword]
    translations: csv.csv_data

    def __init__(self, translations: csv.csv_data):
        self.keywords = {}
        self.translations = translations

    def get(self, id: str, resolveAliases = True):
        keyword = self.keywords.get(id)
        
        if (resolveAliases and keyword != None and keyword.is_alias()):
            return self.get(keyword.aliasOf, True)
        
        return keyword


def collect_keywords(tooltipsfile: str = "./data/data/keyword_tooltips.gon", translationsfile: str = "./data/data/text/keyword_tooltips.csv") -> Keywords:
    out = Keywords(csv.parse_csv(translationsfile))

    keywords = gon.parse_gon(tooltipsfile)
    if not isinstance(keywords, dict):
        raise RuntimeError("Invalid keyword_tooltips.gon file")
    
    def getTooltip(keyword: dict[str, str], suffix: str, commonName: str | None, commonTooltip: str | None) -> Tooltip | None:
        name = keyword.get("name" + suffix)
        tooltip = keyword.get("tooltip" + suffix)

        if (tooltip != None):
            return Tooltip(name if name != None else commonName, tooltip)
        
        if (name != None):
            return Tooltip(name, commonTooltip)
        
        return None

    for id, keyword in keywords.items():
        if not isinstance(keyword, dict):
            continue

        current = Keyword()

        if ("__COMMENTS__" in keyword):
            current.comments = keyword.get("__COMMENTS__")

        if ("alias" in keyword):
            current.aliasOf = keyword.get("alias")
            out.keywords[id] = current
            continue

        commonName = keyword.get("name")
        commonTooltip = keyword.get("tooltip")
        if (commonName != None and commonTooltip != None):
            current.basic = Tooltip(commonName, commonTooltip)

        current.stacks = getTooltip(keyword, "_stacks", commonName, commonTooltip)
        current.stackless = getTooltip(keyword, "_stackless", commonName, commonTooltip)
        current.singular = getTooltip(keyword, "_singular", commonName, commonTooltip)
        current.positive = getTooltip(keyword, "_stacks_pos", commonName, commonTooltip)
        current.negative = getTooltip(keyword, "_stacks_neg", commonName, commonTooltip)
        current.referenceApplier = getTooltip(keyword, "_reference_applier", commonName, commonTooltip)
    
        out.keywords[id] = current

    return out