import os
import subprocess
import logging
import uuid
import tempfile
import shutil

from typing import Any, Callable, Self


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
    id: uuid.UUID

    def __init__(self, inkscapePath: str):
        self.id = uuid.uuid4()

        tmpdir = f"{tempfile.gettempdir()}/inkscape_{self.id}"
        os.makedirs(tmpdir, exist_ok=True)

        # there is no way to disable GTK's recent files
        # and it doesn't handle multiple writers properly
        env = os.environ.copy()
        env["XDG_DATA_HOME"] = tmpdir

        command = [
            inkscapePath,
            "--shell",
        ]
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, env=env)

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
        shutil.rmtree(f"{tempfile.gettempdir()}/inkscape_{self.id}", ignore_errors=True)
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
        
        def getField(self, field: str) -> str:
            field += "=\""
            if field not in self.header:
                return ""
            
            s = self.header.find(field) + len(field)
            e = self.header.find('"', s)
            return self.header[s:e]
        
        def setField(self, field: str, value: str):
            field += "=\""
            if field in self.header:
                s = self.header.find(field) + len(field)
                e = self.header.find('"', s)

                self.header = self.header[:s] + value + self.header[e:]
            else:
                tag = self.getTagname()
                s = self.header.find(tag) + len(tag)
                
                self.header = f"{self.header[:s]} {field}{value}\" {self.header[s:]}"


        def getID(self) -> str:
            return self.getField("id")
        
        def setID(self, id: str):
            self.setField("id", id)

        def getHrefID(self):
            return self.getField("xlink:href")
        
        def setHrefID(self, id: str):
            self.setField("xlink:href", '#' + id)

        def getTransform(self):
            return self.getField("transform")
        
        def setTransform(self, transform: str):
            self.setField("transform", transform)

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

        def removeRedundantGs(self, aggressive: bool = False):
            remain = []
            IDENTITY_MATRIX = "matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)"
            for sub in self.subcomponents:
                sub.removeRedundantGs(aggressive)
                if (sub.header == "<g/>" or sub.header == f"<g transform=\"{IDENTITY_MATRIX}\">"):
                    if (len(sub.subcomponents) > 0):
                        remain += sub.subcomponents

                    continue

                if (aggressive):
                    if (sub.getTagname() == "g" and (sub.getTransform() == "" or sub.getTransform() == IDENTITY_MATRIX)):
                        if (len(sub.subcomponents) > 0):
                            remain += sub.subcomponents
                        continue
 
                remain.append(sub)

            self.subcomponents = remain
        
        def forEach(self, fn: Callable[[Self], Any]):
            fn(self)
            for child in self.subcomponents:
                child.forEach(fn)
       
    xmlVersion: str
    data: Composite

    def __init__(self, xmlVersion: str, data: Composite):
        self.xmlVersion = xmlVersion
        self.data = data

    def compile(self) -> str:
        return self.xmlVersion + self.data.compile()
    
    def replaceComposite(self, id: str, replacement: Composite | None):
        return self.data.replaceComposite(id, replacement)

    def removeComposite(self, id: str):
        return self.replaceComposite(id, None)

    def findComposite(self, id: str) -> Composite | None:
        return self.data.findComposite(id)
    
    def forEach(self, fn: Callable[[Composite], Any]):
        return self.data.forEach(fn)
    
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
        return SvgData(lines[0], ts)

def parse_svg(filename: str) -> SvgData:
    with open(filename, "r") as f:
        content = f.readlines()

    return SvgData.parseSVG(content)
