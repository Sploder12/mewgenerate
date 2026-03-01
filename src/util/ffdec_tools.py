import subprocess
import os
import pathlib
import logging

from . import resource_sync as sync

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
        "sprite:svg,shape:svg,text:svg",
        "-onerror",
        "ignore",
        "-export",
        ','.join(types),
        outDir,
        swfPath
    ]
    
    process = subprocess.run(command, capture_output=True, text=True)
    return (process.returncode, process.stdout, process.stderr)

def dumpOnWait(ffdecPath: str, swfPath: str, outDir: str):
    logging.debug(f"thread {threading.get_ident()} waiting on dump for {swfPath}")

def dumpOnWaitEnd(ffdecPath: str, swfPath: str, outDir: str):
    logging.debug(f"thread {threading.get_ident()} done waiting on {swfPath}")

def dumpProduce(ffdecPath: str, swfPath: str, outDir: str):
    logging.debug(f"thread {threading.get_ident()} dumping {swfPath}")
    needsExport = True
    if (not FORCE_REDUMP):
        needsExport = not os.path.exists(os.path.join(outDir, "shapes", "1.svg"))

    if (needsExport):
        logging.debug(f"cache miss {"(forced) " if FORCE_REDUMP else ''}for {swfPath}")
        start = datetime.now()
        code, _, stderr = export(ffdecPath, swfPath, ["shape", "text"], outDir)
        if (len(stderr) > 0):
            logging.warning(f"FFDec error with code {code}: {stderr}")

        delta = datetime.now() - start
        logging.debug(f"Dumped {swfPath} in {delta.seconds} seconds")
            
    else:
        logging.debug(f"cache hit for {swfPath}")

    return outDir

exportMap = sync.MapSync[str](dumpProduce, dumpOnWait, dumpOnWaitEnd)

# adjusts outDir to have <swf name>/ appended
def exportShapesIfNeeded(ffdecPath: str, swfPath: str, outDir: str = SWF_DUMP_DIR):
    outDir += "/" + pathlib.Path(swfPath).stem
    return exportMap.get(outDir, ffdecPath, swfPath, outDir)

def findDirectory(dumpDir: str, suffix: str):
    dirs = os.listdir(dumpDir)
    for entry in dirs:
        fullPath = os.path.join(dumpDir, entry)
        if os.path.isdir(fullPath) and entry.endswith(suffix):
            return fullPath
        
    return None
