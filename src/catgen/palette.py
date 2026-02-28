import logging

from PIL import Image
logging.getLogger("PIL").setLevel(logging.WARNING)

from ..util import svg_tools as svg

PALETTE_PATH = "./data/textures/palette.png"

class Palette:
    colors: list[tuple[int, int, int]]

    def __init__(self, colors: list[tuple[int, int, int]]):
        self.colors = colors

    def get(self, red: int, green: int, blue: int) -> tuple[int, int, int]:
        if (abs(red - green) >= 1 or abs(red - blue) >= 1):
            return (red, green, blue)
    
        return self.colors[int(red / 16)]
    
def loadPalettes(src: str) -> list[Palette]:
    with Image.open(src) as img:
        converted = img.convert("RGB")
        pixels = converted.load()
        height = converted.height

    palettes: list[Palette] = []
    for y in range(height):
        cur: list[tuple[int, int, int]] = []
        for x in range(16):
            cur.append(pixels[x, y])

        palettes.append(Palette(cur))

    return palettes

def applyPalette(palette: Palette, svgdata: svg.SvgData | svg.SvgData.Composite):
    if isinstance(svgdata, svg.SvgData):
        applyPalette(palette, svgdata.data)
        return
    
    if "fill=\"#" in svgdata.header:
        f = svgdata.header.find("fill=\"#") + 7
        fe = svgdata.header.find('"', f)

        if fe - f == 3:
            red = int(svgdata.header[f:f + 1], 16)
            green = int(svgdata.header[f + 1:f + 2], 16)
            blue = int(svgdata.header[f + 2:f + 3], 16)
        else:
            red = int(svgdata.header[f:f + 2], 16)
            green = int(svgdata.header[f + 2:f + 4], 16)
            blue = int(svgdata.header[f + 4:f + 6], 16)

        color = palette.get(red, green, blue)

        svgdata.header = svgdata.header[:f] + f"{color[0]:x}{color[1]:x}{color[2]:x}" + svgdata.header[fe:]

    elif "stop-color=\"#" in svgdata.header:
        f = svgdata.header.find("stop-color=\"#") + 13
        fe = svgdata.header.find('"', f)

        red = int(svgdata.header[f:f + 2], 16)
        green = int(svgdata.header[f + 2:f + 4], 16)
        blue = int(svgdata.header[f + 4:f + 6], 16)

        color = palette.get(red, green, blue)

        svgdata.header = svgdata.header[:f] + f"{color[0]:x}{color[1]:x}{color[2]:x}" + svgdata.header[fe:]

    for sub in svgdata.subcomponents:
        applyPalette(palette, sub)