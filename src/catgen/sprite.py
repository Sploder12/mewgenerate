from ..util import svg_tools as svg
from ..util import parse_swf as swf
from . import swf_tree as tree

import os

class Sprite:
    @staticmethod
    def matrixToSVG(matrix: swf.Matrix) -> str:
        return f"matrix({matrix.xscale}, {matrix.skew1}, {matrix.skew2}, {matrix.yscale}, {matrix.xoffset}, {matrix.yoffset})"
    
    @staticmethod
    def matrixFromSVG(matrix: str) -> swf.Matrix:
        components = matrix.removeprefix("matrix(").removesuffix(')').split(',')

        out = swf.Matrix()
        out.xscale = float(components[0])
        out.skew1 = float(components[1])
        out.skew2 = float(components[2])
        out.yscale = float(components[3])
        out.xoffset = float(components[4])
        out.yoffset = float(components[5])
        return out
    
    @staticmethod
    def rgbToSVG(r: int, g: int, b: int) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def rgbFromSVG(rgb: str) -> tuple[int, int, int]:
        rgb = rgb.removeprefix('#')
        s = 1 if len(rgb) == 3 else 2

        r = int(rgb[0:s], 16)
        g = int(rgb[s:s+s], 16)
        b = int(rgb[s+s:s*3], 16)
        return (r, g, b)
        
    data: svg.SvgData

    def __init__(self, data: svg.SvgData):
        self.data = data

    def getImportantComponents(self) -> list[svg.SvgData.Composite]:
        # <svg> is not important
        return self.data.data.subcomponents

    def getDimensions(self) -> tuple[float, float]:
        w = float(self.data.data.getField("width").removesuffix("px"))
        h = float(self.data.data.getField("height").removesuffix("px"))

        return (w, h)

    def applyTransform(self, xform: swf.CXFORM | swf.Matrix):
        def applyCXFORM(data: svg.SvgData.Composite):
            if ("fill=\"#" in data.header):
                r, g, b = Sprite.rgbFromSVG(data.getField("fill"))
                astr = data.getField("opacity")
                a = float(astr if astr != "" else 1.0) * 255.0

                nr, ng, nb, na = xform.transform(float(r), float(g), float(b), a)
                data.setField("fill", Sprite.rgbToSVG(int(nr), int(ng), int(nb)))

                if (na != 255.0 or astr != ""):
                    data.setField("opacity", str(na / 255.0))
            
            if ("stop-color=\"#" in data.header):
                # @TODO handle opacity?
                r, g, b = Sprite.rgbFromSVG(data.getField("stop-color"))
                nr, ng, nb, na = xform.transform(float(r), float(g), float(b), 1.0)
                data.setField("stop-color", Sprite.rgbToSVG(int(nr), int(ng), int(nb)))

        if isinstance(xform, swf.CXFORM):
            self.data.forEach(applyCXFORM)

        else:
            comp = svg.SvgData.Composite(f"<g transform=\"{Sprite.matrixToSVG(xform)}\">\n", self.getImportantComponents())
            self.data.data.subcomponents = [comp]

    def compile(self) -> str:
        dx, dy = self.getDimensions()
        rebaseCenter = swf.Matrix()
        rebaseCenter.xoffset += dx / 2.0
        rebaseCenter.yoffset += dy / 2.0

        self.applyTransform(rebaseCenter)
        return self.data.compile()


# first element is drawn last, last is drawn first
def mergeSprites(sprites: list[Sprite]) -> Sprite:
    mwid = 0.0
    mhig = 0.0
    for sprite in sprites:
        dims = sprite.getDimensions()
        mwid = max(dims[0], mwid)
        mhig = max(dims[1], mhig)

    svgTag = f"<svg width=\"{mwid}px\" height=\"{mhig}px\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:ffdec=\"https://www.free-decompiler.com/flash\">"
    out = Sprite(svg.SvgData(sprites[0].data.xmlVersion, svg.SvgData.Composite(svgTag, [])))

    for sprite in sprites:
        out.data.data.subcomponents += sprite.getImportantComponents()

    return out

def getShape(dumpdir: str, id: int) -> Sprite:
    s = Sprite(svg.parse_svg(os.path.join(dumpdir, "shapes", str(id) + ".svg")))
    dx, dy = s.getDimensions()

    # make everything 0,0 based so it's possible to work with
    def rebaseShape(s: svg.SvgData.Composite):
        t = s.getField("transform")
        if t != "":
            xform = swf.Matrix()
            #xform = Sprite.matrixFromSVG(t)
            #xform.xoffset -= dx / 2.0
            #xform.yoffset -= dy / 2.0
            s.setField("transform", Sprite.matrixToSVG(xform))

    # probably (hopefully) only hits one <g>
    s.data.data.forEach(rebaseShape)

    return s

def getText(dumpdir: str, id: int) -> Sprite:
    s = Sprite(svg.parse_svg(os.path.join(dumpdir, "texts", str(id) + ".svg")))
    dx, dy = s.getDimensions()

    # make everything 0,0 based so it's possible to work with
    def rebaseShape(s: svg.SvgData.Composite):
        t = s.getField("transform")
        if t != "":
            xform = Sprite.matrixFromSVG(t)
            xform.xoffset -= dx / 2.0
            xform.yoffset -= dy / 2.0
            s.setField("transform", Sprite.matrixToSVG(xform))

    # probably (hopefully) only hits one <g>
    s.data.data.forEach(rebaseShape)

    return s

def spriteFromDefineShape(dumpdir: str, tag: swf.DefineShape) -> Sprite:
    return getShape(dumpdir, tag.id)

def spriteFromPlacedObject(dumpdir: str, swfTree: tree.SWF_Tree, obj: tree.PlacedObject, frame: int = 0) -> Sprite:
    refNode = swfTree.get(obj.id)
    assert(refNode != None)

    s = spriteFromNode(dumpdir, swfTree, refNode)

    if (obj.cxform):
        s.applyTransform(obj.cxform)

    if (obj.xform):
        s.applyTransform(obj.xform)

    return s

def spriteFromNode(dumpdir: str, swfTree: tree.SWF_Tree, node: tree.SWF_Tree.ShapeNode | tree.SWF_Tree.TextNode | tree.SWF_Tree.SpriteNode, frame: int = 0) -> Sprite:
    if isinstance(node, tree.SWF_Tree.ShapeNode):
        return getShape(dumpdir, node.id)
    elif isinstance(node, tree.SWF_Tree.TextNode):
        return getText(dumpdir, node.id)

    # @TODO handle clipDepth

    sprites = []
    f = node.frames[frame]
    if (len(f.objs) == 0):
        return Sprite(svg.SvgData("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>", svg.SvgData.Composite("<svg width=\"0.0px\" height=\"0.0px\">", [])))

    objs = sorted(f.objs, key=lambda obj: obj.depth)
    sprites = [spriteFromPlacedObject(dumpdir, swfTree, obj) for obj in objs]
    return mergeSprites(sprites)
        