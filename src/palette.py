import logging

from PIL import Image
logging.getLogger("PIL").setLevel(logging.WARNING)

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