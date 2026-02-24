import subprocess
import os
import pathlib
import logging

from datetime import datetime
import threading

SWF_DUMP_DIR = "./cache/swfdump"
FORCE_REDUMP = False

# does not adjust outDir
def export(ffdecPath: str, swfPath: str, types: list[str], outDir: str):
    command = [
        ffdecPath,
        "-importAssets",
        "yes,local",
        "-format",
        "sprite:svg",
        "-onerror",
        "ignore",
        "-export",
        ','.join(types),
        outDir,
        swfPath
    ]
    
    process = subprocess.run(command, capture_output=True, text=True)
    return (process.returncode, process.stdout, process.stderr)

class Cond:
    cv: threading.Condition()
    done: bool

    def __init__(self):
        self.done = False
        self.cv = threading.Condition()


exportConditions: dict[str, Cond] = {}
exportConditionsLock = threading.Lock()

# adjusts outDir to have <swf name>/ appended
def exportSpritesIfNeeded(ffdecPath: str, swfPath: str, outDir: str = SWF_DUMP_DIR):
    needsExport = True

    outDir += "/" + pathlib.Path(swfPath).stem

    producing = False
    with exportConditionsLock:
        if (outDir in exportConditions):
            cond = exportConditions[outDir]
        else:
            producing = True

            cond = Cond()
            exportConditions[outDir] = cond
            
            
    if (not producing):
        waited = False
        with cond.cv:
            if (not cond.done):
                waited = True
                logging.debug(f"thread {threading.get_ident()} waiting on dump for {swfPath}")
                while not cond.done:
                    cond.cv.wait()
        
        if (waited):
            logging.debug(f"thread {threading.get_ident()} done waiting on {swfPath}")

    else:
        logging.debug(f"thread {threading.get_ident()} dumping {swfPath}")
        with cond.cv:
            if (not FORCE_REDUMP):
                try:
                    dirs = os.listdir(outDir)
                    for entry in dirs:
                        fullPath = os.path.join(outDir, entry)
                        if os.path.isdir(fullPath) and "DefineSprite" in entry:
                            needsExport = False
                            break
                except FileNotFoundError:
                    pass

            if (needsExport):
                logging.debug(f"cache miss {"(forced)" if FORCE_REDUMP else ''} for {swfPath}")
                start = datetime.now()
                code, _, stderr = export(ffdecPath, swfPath, ["sprite"], outDir)
                if (len(stderr) > 0):
                    logging.warning(f"FFDec error with code {code}: {stderr}")

                delta = datetime.now() - start
                logging.debug(f"Dumped {swfPath} in {delta.seconds} seconds")
            

            else:
                logging.debug(f"cache hit for {swfPath}")

            cond.done = True
            cond.cv.notify_all()

    return outDir

def findDirectory(dumpDir: str, suffix: str):
    dirs = os.listdir(dumpDir)
    for entry in dirs:
        fullPath = os.path.join(dumpDir, entry)
        if os.path.isdir(fullPath) and entry.endswith(suffix):
            return fullPath
        
    return None
