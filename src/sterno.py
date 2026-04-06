import argparse
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import stats as sp_stats

CONFIDENCE_THRESHOLD = 0.60
SUSPICIOUS_THRESHOLD = 0.40

CHANNEL_MAP = {"r": 0, "g": 1, "b": 2}

# ── Chi-Square Test ──────────────────────────────────────────────────────────
def chi_square_test(pixels):
    flat = pixels.flatten().astype(np.int32)
    hist, _ = np.histogram(flat, bins=256, range=(0, 256))

    chi2_stat = 0.0
    for i in range(128):
        even = hist[2*i]
        odd = hist[2*i + 1]
        pair_total = even + odd
        if pair_total == 0:
            continue
        exp = pair_total / 2
        chi2_stat += ((even - exp)**2 + (odd - exp)**2) / exp

    p_value = 1.0 - sp_stats.chi2.cdf(chi2_stat, df=127)
    score = max(0.0, 1.0 - p_value)

    return {"test": "chi_square", "score": score, "detail": f"p={p_value:.4f}"}

# ── SPA ─────────────────────────────────────────────────────────────────────
def sample_pair_analysis(pixels):
    flat = pixels.flatten().astype(np.int32)
    if len(flat) < 100:
        return {"test": "spa", "score": 0.0, "detail": "too small"}

    u = flat[:-1]
    v = flat[1:]

    W = np.sum((u % 2 == 0) & (v == u + 1))
    X = np.sum((u % 2 == 0) & (v == u - 1))
    Y = np.sum((u % 2 == 1) & (v == u + 1))
    Z = np.sum((u % 2 == 1) & (v == u - 1))

    total = W + X + Y + Z
    if total == 0:
        return {"test": "spa", "score": 0.0, "detail": "no pairs"}

    p = 2 * (W + Z) / total
    score = min(p * 2, 1.0)

    return {"test": "spa", "score": score, "detail": f"p≈{p:.2f}"}

# ── Histogram ────────────────────────────────────────────────────────────────
def histogram_pair_analysis(pixels):
    flat = pixels.flatten().astype(np.int32)
    hist, _ = np.histogram(flat, bins=256, range=(0, 256))

    even = hist[0::2].astype(float)
    odd = hist[1::2].astype(float)
    total = even + odd

    valid = total > 10
    if not np.any(valid):
        return {"test": "histogram", "score": 0.0, "detail": "low data"}

    ratios = even[valid] / total[valid]
    dev = np.abs(ratios - 0.5)
    mean_dev = np.mean(dev)

    score = max(0.0, 1.0 - (mean_dev / 0.25))

    return {"test": "histogram", "score": score, "detail": f"dev={mean_dev:.3f}"}

# ── Combine ──────────────────────────────────────────────────────────────────
WEIGHTS = {"chi_square": 0.45, "spa": 0.35, "histogram": 0.20}

def combined_score(results):
    total = sum(r["score"] * WEIGHTS[r["test"]] for r in results)
    return total

def verdict(score):
    if score >= CONFIDENCE_THRESHOLD:
        return "LIKELY STEGO"
    elif score >= SUSPICIOUS_THRESHOLD:
        return "INCONCLUSIVE"
    else:
        return "LIKELY CLEAN"

# ── Image Loader ─────────────────────────────────────────────────────────────
def load_image_channels(path, channel):
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    if channel == "all":
        return {"r": r, "g": g, "b": b}
    elif channel in CHANNEL_MAP:
        return {channel: arr[:, :, CHANNEL_MAP[channel]]}
    elif channel == "luminance":
        luma = (0.299*r + 0.587*g + 0.114*b).astype(np.uint8)
        return {"luma": luma}

# ── Analysis ─────────────────────────────────────────────────────────────────
def analyze(path, channel, verbose):
    channels = load_image_channels(path, channel)
    scores = []

    for name, data in channels.items():
        tests = [
            chi_square_test(data),
            sample_pair_analysis(data),
            histogram_pair_analysis(data),
        ]

        score = combined_score(tests)
        scores.append(score)

        print(f"{name.upper()} → {score:.3f} ({verdict(score)})")

        if verbose:
            for t in tests:
                print(f"  - {t['test']}: {t['score']:.3f} ({t['detail']})")

    overall = max(scores)
    print("\nOverall:", overall, verdict(overall))

# ── Interactive CLI ──────────────────────────────────────────────────────────
def interactive_mode():
    print("\n[ Steganography Detector ]\n")

    path = input("Enter image path: ").strip().strip('"').strip("'")
    if not Path(path).exists():
        print("File not found.")
        return

    print("\nChannel: 1=all 2=R 3=G 4=B 5=luma")
    ch = input("Choice: ").strip()
    channel = {"2":"r","3":"g","4":"b","5":"luminance"}.get(ch,"all")

    verbose = input("Verbose? (y/n): ").lower() == "y"

    print("\nRunning...\n")
    analyze(Path(path), channel, verbose)

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", nargs="?", help="Image path")
    parser.add_argument("--channel", default="all")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not args.image:
        interactive_mode()
    else:
        analyze(Path(args.image), args.channel, args.verbose)

if __name__ == "__main__":
    main()
