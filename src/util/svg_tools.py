import os
import subprocess

from typing import Callable

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

        data = f"file-open:{src}\nexport-margin:5\nexport-area-drawing\nexport-filename:{dst}\nexport-do\nfile-close\n"

        self.process.stdin.write(data.encode())
        self.process.stdin.flush()

    def crop_handle_duplicate(self, src: str, dst: str, onDuplicate: Callable[[str], str] = defaultDuplicateHandler):
        try:
            self.crop(src, dst)
            return dst
        except FileExistsError:
            return self.crop_handle_duplicate(src, onDuplicate(dst), onDuplicate)

    def finish(self):
        self.process.communicate("quit\n".encode())
        out = self.process.wait()
        return (out, self.process.stdout, self.process.stderr)
    

