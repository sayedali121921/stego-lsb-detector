# stego-lsb-detector
CLI-based steganography detection tool using statistical analysis of image pixels (Python)
## Features

- Detects hidden data in images using **statistical analysis**
- Supports single-image analysis and per-channel breakdown (R/G/B separately)
- Batch directory scanning
- Combines three tests:
  1. **Chi-square test** – checks pixel value pair frequencies
  2. **Sample Pair Analysis (SPA)** – estimates fraction of modified pixels
  3. **Histogram pair analysis** – measures even/odd value balance

---
###usage
python src/steg_detector.py
# Enter image path: data/stego.png
python src/steg_detector.py image.png --channel r
python src/steg_detector.py image.png --channel all
python src/steg_detector.py image.png --verbose
####Limitations
JPEG images: Lossy compression alters LSBs, which can lead to false positives.
High-frequency images: Noisy or detailed images can produce higher scores even if clean.
This tool detects statistical anomalies, not the actual hidden message.

######How it works

LSB steganography replaces the least significant bit of pixels with secret data. Changes are imperceptible visually but leave statistical traces.

This tool runs three tests on pixel value distributions and adjacent pairs to detect these anomalies and combines the results into a single confidence score.
