# NanoStride

**NanoStride** is a Python toolchain that slices STL files using PrusaSlicer and converts the resulting image layers into binary waveforms for hardware use.

---

## Quick Start

1. **Install PrusaSlicer**  
   https://www.prusa3d.com/prusaslicer/  
   NanoStride requires the `prusa-slicer-console` CLI tool included in the install.

2. **Run the pipeline**
   ```bash
   python scripts/pipeline.py
