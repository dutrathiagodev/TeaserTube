import subprocess
import sys

if "--diagnostico" in sys.argv:
    from teasertube import core

    ffmpeg = core.find_ffmpeg()
    print("ffmpeg:", ffmpeg or ("do sistema" if core.has_ffmpeg() else "NAO ENCONTRADO"))
    runtimes = core.js_runtimes()
    print("js runtimes:", runtimes or "NENHUM")
    if "deno" in runtimes:
        out = subprocess.run([runtimes["deno"]["path"], "--version"], capture_output=True, text=True)
        print("deno:", (out.stdout or out.stderr).splitlines()[0])
        sys.exit(out.returncode)
    sys.exit(0 if runtimes else 1)

from teasertube.gui import main

main()
