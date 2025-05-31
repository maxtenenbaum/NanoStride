import os
import platform
import webbrowser

def find_prusaslicer():
    system = platform.system().lower()

    if system == "windows":
        path = r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"
        if os.path.exists(path):
            return path
    elif system == "darwin":
        path = "/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer"
        if os.path.exists(path):
            return path
    elif system == "linux":
        candidates = ["/usr/bin/PrusaSlicer", "/usr/local/bin/PrusaSlicer"]
        for p in candidates:
            if os.path.exists(p):
                return p

    print("PrusaSlicer not found.")
    print("Opening download page...")
    webbrowser.open("https://www.prusa3d.com/prusaslicer/")
    raise FileNotFoundError("PrusaSlicer not found. Please install it and try again.")
