from ..util import svg_tools as svg
from ..util import parse_swf as swf
from . import swf_tree as tree

import os
import uuid

from typing import Sequence

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

    def applyTransform(self, xform: swf.CXFORM | swf.Matrix | None):
        if (xform == None): # makes things a bit simpler
            return self

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

        return self

    def compile(self) -> str:
        dx, dy = self.getDimensions()
        rebaseCenter = swf.Matrix()
        rebaseCenter.xoffset += dx / 2.0
        rebaseCenter.yoffset += dy / 2.0

        #self.applyTransform(rebaseCenter)
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
    
    if len(sprites) == 0:
        return Sprite(svg.SvgData("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>", svg.SvgData.Composite(svgTag, [])))

    out = Sprite(svg.SvgData(sprites[0].data.xmlVersion, svg.SvgData.Composite(svgTag, [])))

    for sprite in sprites:
        out.data.data.subcomponents += sprite.getImportantComponents()

    return out

def getShape(dumpdir: str, id: int, name: str = "") -> Sprite:
    s = Sprite(svg.parse_svg(os.path.join(dumpdir, "shapes", str(id) + ".svg")))

    # make everything 0,0 based so it's possible to work with
    comps = s.getImportantComponents()
    assert (len(comps) > 0 and comps[0].getTagname() == "g")
    if (comps[0].getField("transform") != ""):
        comps[0].setField("transform", "matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)")

    if (comps[0].getField("id") == ""):
        if name == "":
            comps[0].setField("id", "DefineShape_" + str(id))
        else:
            comps[0].setField("id", name + '_' + str(id))

    return s

def getText(dumpdir: str, id: int, name: str = "") -> Sprite:
    s = Sprite(svg.parse_svg(os.path.join(dumpdir, "texts", str(id) + ".svg")))
    
    # make everything 0,0 based so it's possible to work with
    comps = s.getImportantComponents()
    assert (len(comps) > 0 and comps[0].getTagname() == "g")
    if (comps[0].getField("transform") != ""):
        comps[0].setField("transform", "matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)")

    if (comps[0].getField("id") == ""):
        if name == "":
            comps[0].setField("id", "DefineText_" + str(id))
        else:
            comps[0].setField("id", name + '_' + str(id))

    return s

def spriteFromDefineShape(dumpdir: str, tag: swf.DefineShape) -> Sprite:
    return getShape(dumpdir, tag.id)

def spriteFromPlacedObject(dumpdir: str, swfTree: tree.SWF_Tree, obj: tree.PlacedObject, frame: int = 0) -> Sprite:
    refNode = swfTree.get(obj.id)
    assert(refNode != None)

    s = spriteFromNode(dumpdir, swfTree, refNode)
    s.applyTransform(obj.cxform).applyTransform(obj.xform)

    return s

def spriteFromNode(dumpdir: str, swfTree: tree.SWF_Tree, node: tree.SWF_Tree.ShapeNode | tree.SWF_Tree.TextNode | tree.SWF_Tree.SpriteNode, frame: int = 0) -> Sprite:
    if isinstance(node, tree.SWF_Tree.ShapeNode):
        return getShape(dumpdir, node.id, node.name)
    elif isinstance(node, tree.SWF_Tree.TextNode):
        return getText(dumpdir, node.id, node.name)

    f = node.frames[frame]
    if (len(f.objs) == 0):
        return Sprite(svg.SvgData("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>", svg.SvgData.Composite("<svg width=\"0.0px\" height=\"0.0px\">", [])))

    return spriteFromPlacedObjects(dumpdir, swfTree, f.objs)

class PlacedSprite:
    sprite: Sprite
    id: int
    name: str
    depth: int
    clipDepth: int | None

    def __init__(self, sprite: Sprite, id: int, depth: int, clipDepth: int | None = None, name: str = ""):
        self.sprite = sprite
        self.id = id
        self.name = name
        self.depth = depth
        self.clipDepth = clipDepth
        

def spriteFromPlacedObjects(dumpdir: str, swfTree: tree.SWF_Tree, objs: Sequence[tree.PlacedObject | PlacedSprite]) -> Sprite:
    sprites: list[Sprite] = []
    clips: list[tuple[int, int, str]] = []
    for obj in objs:
        if (obj.clipDepth != None):
            obj.name += '_' + str(obj.id) + str(uuid.uuid4())
            clips.append((obj.depth, obj.clipDepth, obj.name))

            if (isinstance(obj, PlacedSprite)):
                sprite = obj.sprite
            else:
                sprite = spriteFromPlacedObject(dumpdir, swfTree, obj)

            comp = svg.SvgData.Composite(f"<clipPath id=\"{obj.name}\">\n", sprite.getImportantComponents())
            comp.removeRedundantGs(True)

            ic = sprite.getImportantComponents()
            if (len(ic) == 1 and ic[0].getTagname() == "g"):
                comp.setField("transform", ic[0].getField("transform"))
                comp.subcomponents = ic[0].subcomponents
            
            sprite.data.data.subcomponents = [comp]
            sprites.append(sprite)
            
    clips = sorted(clips, key=lambda dn: dn[0], reverse=True)    
    objs = sorted(objs, key=lambda obj: obj.depth)
    for obj in objs:
        if (obj.clipDepth != None and obj.clipDepth != 0):
            continue

        if (isinstance(obj, PlacedSprite)):
            sprite = obj.sprite
        else:
            sprite = spriteFromPlacedObject(dumpdir, swfTree, obj)

        for clipStart, clipEnd, id in clips:
            if (obj.depth >= clipStart and obj.depth <= clipEnd):
                comp = svg.SvgData.Composite(f"<g clip-path=\"url(#{id})\">\n", sprite.getImportantComponents())
                sprite.data.data.subcomponents = [comp]
        
        sprite.data.data.removeRedundantGs()
        sprites.append(sprite)
    
    return mergeSprites(sprites)
        