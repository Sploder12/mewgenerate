import os
import subprocess

class SvgCropper:
    process: subprocess.Popen[bytes]

    def __init__(self, inkscapePath: str):
        command = [
            inkscapePath,
            "--shell",
        ]
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)

    def crop(self, src: str, dst: str):
        if (not os.path.isfile(src)):
            # exception is far better than uncapturable stderr
            raise FileNotFoundError(f"{src} is not an existing file")

        data = f"file-open:{src}\nexport-margin:5\nexport-area-drawing\nexport-filename:{dst}\nexport-do\nfile-close\n"

        self.process.stdin.write(data.encode())
        self.process.stdin.flush()

    def finish(self):
        self.process.communicate("quit\n".encode())
        out = self.process.wait()
        return (out, self.process.stdout, self.process.stderr)