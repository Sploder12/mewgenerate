import subprocess
import os
import pathlib
import logging

SWF_DUMP_DIR = "./cache/swfdump"
FORCE_REDUMP = False

# does not adjust outDir
def export(ffdecPath: str, swfPath: str, types: list[str], outDir: str):
    command = [
        ffdecPath,
        "--enable-native-access=ALL-UNNAMED",
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

# adjusts outDir to have <swf name>/ appended
def exportSpritesIfNeeded(ffdecPath: str, swfPath: str, outDir: str = SWF_DUMP_DIR):
    needsExport = True

    outDir += "/" + pathlib.Path(swfPath).stem
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
        code, _, stderr = export(ffdecPath, swfPath, ["sprite"], outDir)
        if (len(stderr) > 0):
            logging.warning(f"FFDec error with code {code}: {stderr}")

    return outDir

def findDirectory(dumpDir: str, suffix: str):
    dirs = os.listdir(dumpDir)
    for entry in dirs:
        fullPath = os.path.join(dumpDir, entry)
        if os.path.isdir(fullPath) and entry.endswith(suffix):
            return fullPath
        
    return None
