import os
import subprocess
import logging

from typing import Callable, Self


def defaultDuplicateHandler(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    
    splitted = name.split(' ')
    if (len(splitted) <= 1):
        return name + " 2" + ext

    base = ' '.join(splitted[:-1])
    num = splitted[-1]

    try:
        return base + f" {int(num) + 1}" + ext
    except:
        return name + " 2" + ext

class SvgCropper:
    process: subprocess.Popen[bytes]

    def __init__(self, inkscapePath: str):
        command = [
            inkscapePath,
            "--shell",
        ]
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.finish()
        return False

    def crop(self, src: str, dst: str):
        if (not os.path.isfile(src)):
            # exception is far better than uncapturable stderr
            raise FileNotFoundError(f"{src} is not an existing file")
        
        if (src != dst and os.path.isfile(dst)):
            raise FileExistsError(f"{dst} already exists")

        if (os.path.getsize(src) <= 1):
            logging.warning(f"{src} is an empty file")
            return

        data = f"file-open:{src}\nexport-margin:5\nexport-area-drawing\nexport-filename:{dst}\nexport-do\nfile-close\n"

        self.process.stdin.write(data.encode())
        #self.process.stdin.flush()

    def crop_handle_duplicate(self, src: str, dst: str, onDuplicate: Callable[[str], str] = defaultDuplicateHandler):
        try:
            self.crop(src, dst)
            return dst
        except FileExistsError:
            return self.crop_handle_duplicate(src, onDuplicate(dst), onDuplicate)

    def finish(self):
        self.process.stdin.flush()
        self.process.communicate("quit\n".encode())
        out = self.process.wait()
        return (out, self.process.stdout, self.process.stderr)
    

class SvgData:
    @staticmethod 
    def getTagname(line: str) -> str:
        s = line.find('<') + 1
        if (s == -1):
            return ""
        
        if "</" in line:
            s += 1

        e = line.find(' ', s)
        if (e == -1):
            e = line.find('/>', s)
            if (e == -1):
                e = line.find('>', s)

        if (e == -1):
            logging.warning(f"Invalid SVG line: {line}")
            return ""

        return line[s:e]

    class Composite:
        header: str # <g>/<clipPath>/<use>
        subcomponents: list[Self]

        def __init__(self, header: str, subcomponents: list[Self]):
            self.header = header
            self.subcomponents = subcomponents

        def isSingleLine(self):
            return "/>" in self.header
        
        def getTagname(self):
            return SvgData.getTagname(self.header)

        def getID(self) -> str:
            if "id=\"" in self.header:
                s = self.header.find("id=\"") + 4
                e = self.header.find('"', s)

                return self.header[s:e]
        
            return ""
        
        def setID(self, id: str):
            if ("id=\"" in self.header):
                s = self.header.find("id=\"") + 4
                e = self.header.find('"', s)

                self.header = self.header[:s] + id + self.header[e:]
            else:
                tag = self.getTagname()
                s = self.header.find(tag) + len(tag)
                
                self.header = self.header[:s] + " id=\"" + id + "\" " + self.header[s:]

        def getHrefID(self):
            if "xlink:href=\"#" in self.header:
                s = self.header.find("xlink:href=\"#") + 13
                e = self.header.find('"', s)

                return self.header[s:e]
        
            return ""
        
        def setHrefID(self, id: str):
            if "xlink:href=\"#" in self.header:
                s = self.header.find("xlink:href=\"#") + 13
                e = self.header.find('"', s)

                self.header = self.header[:s] + id + self.header[e:]
            else:
                raise RuntimeError(f"setting href of non <use> tag {self.getTagname()}")

        def getTransform(self):
            if "transform=\"" in self.header:
                s = self.header.find("transform=\"") + 11
                e = self.header.find('"', s)

                return self.header[s:e]

            return ""
        
        def setTransform(self, transform: str):
            if "transform=\"" in self.header:
                s = self.header.find("transform=\"") + 11
                e = self.header.find('"', s)

                self.header = self.header[:s] + transform + self.header[e:]
            else:
                tag = self.getTagname()
                s = self.header.find(tag) + len(tag)
                
                self.header = self.header[:s] + " transform=\"" + transform + "\" " + self.header[s:]

        def replaceComposite(self, id: str, replacement: Self | None):
            count = 0
            i = 0
            while i < len(self.subcomponents):
                sub = self.subcomponents[i]
                if sub.getID() == id:
                    if (replacement == None):
                        del self.subcomponents[i]
                        i -= 1
                    else:
                        self.subcomponents[i] = replacement
                    count += 1

                count += sub.replaceComposite(id, replacement)
                i += 1

            return count
        
        def findComposite(self, id: str) -> Self | None:
            for sub in self.subcomponents:
                if sub.getID() == id:
                    return sub
                
                r = sub.findComposite(id)
                if (r != None):
                    return r
                
            return None
        
        def prefixIds(self, prefix: str):
            if (self.getID() != ""):
                self.setID(prefix + self.getID())

            for sub in self.subcomponents:
                sub.prefixIds(prefix)
        
        def prefixLinks(self, prefix: str):
            if self.getTagname() == "use":
                self.setHrefID(prefix + self.getHrefID())

            for sub in self.subcomponents:
                sub.prefixLinks(prefix)
            
        def compile(self) -> str:
            out = self.header
            for sub in self.subcomponents:
                out += sub.compile()

            if (not self.isSingleLine()):
                out += f"</{self.getTagname()}>\n"

            return out
       
    xmlVersion: str
    header: str # <svg>
    decl: Composite
    defs: Composite

    def __init__(self, xmlVersion: str, header: str, decl: Composite, defs: Composite):
        self.xmlVersion = xmlVersion
        self.header = header
        self.decl = decl
        self.defs = defs

    def compile(self) -> str:
        out = self.xmlVersion + self.header + self.decl.compile() + self.defs.compile()
        out += "</svg>\n"
        return out
    
    def replaceComposite(self, id: str, replacement: Composite | None):
        return self.decl.replaceComposite(id, replacement) + self.defs.replaceComposite(id, replacement)

    def removeComposite(self, id: str):
        return self.replaceComposite(id, None)

    def findComposite(self, id: str) -> Composite | None:
        r = self.decl.findComposite(id)
        if (r != None):
            return r
        
        return self.defs.findComposite(id)
    
    def prefixLinks(self, prefix: str):
        self.decl.prefixLinks(prefix)

        self.defs.prefixIds(prefix)
        self.defs.prefixLinks(prefix)
    
    @staticmethod 
    def parseComposite(lines: list[str]) -> Composite:
        header = lines[0]
        subcomponents = []

        inTag = False
        tag = ""
            
        counter = 0
        start = 0
        for i in range(len(lines) - 1):
            line = lines[i + 1]

            if inTag:
                name = SvgData.getTagname(line)
                if (name == tag):
                    if "</" in line:
                        counter -= 1
                        if (counter == 0):
                            subcomponents.append(SvgData.parseComposite(lines[start:i + 1]))
                            inTag = False
                            continue
                    else:
                        counter += 1
                        continue

            else:   
                if ("<use " in line or "/>" in line):
                    subcomponents.append(SvgData.parseComposite([line]))
                    continue
                
                tag = SvgData.getTagname(line)
                if (tag != ""):
                    start = i + 1
                    counter = 1
                    inTag = True

        if inTag:
            raise RuntimeError(f"SVG tag {tag} has no end tag")

        return SvgData.Composite(header, subcomponents)
    
    @staticmethod
    def parseSVG(lines: list[str]):
        end = 1
        for i in range(1, len(lines)):
            if ("</" in lines[i] and SvgData.getTagname(lines[i]) == "svg"):
                end = i

        ts = SvgData.parseComposite(lines[1:end])

        if (len(ts.subcomponents) != 2):
            if (len(ts.subcomponents) == 1):
                return SvgData(lines[0], lines[1], ts.subcomponents[0], SvgData.Composite("<defs></defs>", []))
            else:
                return SvgData(lines[0], lines[1], SvgData.Composite("<g></g>", []), SvgData.Composite("<defs></defs>", []))

        return SvgData(lines[0], lines[1], ts.subcomponents[0], ts.subcomponents[1])

def parse_svg(filename: str) -> SvgData:
    with open(filename, "r") as f:
        content = f.readlines()

    return SvgData.parseSVG(content)


if __name__ == "__main__":
    cropper = SvgCropper("C:/Program Files/Inkscape/bin/inkscape.com")
    for i in range(1, 11):
        test = parse_svg("./cache/swfdump/catparts/DefineSprite_601/1.svg")
        test2 = parse_svg(f"./cache/swfdump/catparts/DefineSprite_599/{i}.svg")
        test2.prefixLinks("bg_")

        test.defs.subcomponents += test2.defs.subcomponents

        bgtag = test.findComposite("bg")
        transform = bgtag.getTransform()

        test2.decl.setTransform(transform)
        test.replaceComposite("bg", test2.decl)

        with open(f"./out/frozen_bone {i}.svg", "w") as o:
            o.write(test.compile())

        
        cropper.crop(f"./out/frozen_bone {i}.svg", f"./out/frozen_bone {i}.svg")

    cropper.finish()