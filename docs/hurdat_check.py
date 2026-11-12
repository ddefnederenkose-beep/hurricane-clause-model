"""HURDAT2 check of the hurricane frequency lambda for Grenada (REPORT ONLY: it does not change any parameter).

Counts the years with at least one best-track point of >= 96 kt (Category 3+) within 30, 60 and 100 nautical miles of
Grenada (12.12N, 61.68W), from the raw 6-hourly records and from tracks linearly interpolated to hourly resolution.
Usage:  python -I docs/hurdat_check.py /path/to/hurdat2-1851-YYYY-MMDDYY.txt     (the data file is not stored in the repo)
"""
import sys
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt

GRENADA = (12.12, -61.68)
THRESH_KT = 96
RADII = (30, 60, 100)
PERIODS = ((1980, 2019), (1980, 2024))
NM = 3440.065  # Earth radius in nautical miles


def dist_nm(lat1, lon1, lat2, lon2):
    p1, p2 = radians(lat1), radians(lat2)
    a = sin((p2 - p1) / 2) ** 2 + cos(p1) * cos(p2) * sin(radians(lon2 - lon1) / 2) ** 2
    return 2 * NM * asin(sqrt(a))


def parse(path):
    storms, cur = {}, None
    for line in open(path):
        f = [x.strip() for x in line.split(",")]
        if f[0].startswith("AL") and len(f) >= 3 and len(f[0]) == 8:
            cur = {"id": f[0], "name": f[1], "pts": []}
            storms[f[0]] = cur
        elif cur is not None and len(f) >= 7:
            t = datetime.strptime(f[0] + f[1], "%Y%m%d%H%M")
            lat = float(f[4][:-1]) * (1 if f[4][-1] == "N" else -1)
            lon = float(f[5][:-1]) * (-1 if f[5][-1] == "W" else 1)
            cur["pts"].append((t, lat, lon, float(f[6]), f[2]))
    return storms


def hourly(pts):
    """Linear interpolation (position and wind) between consecutive records, hourly steps."""
    out = []
    for (t0, la0, lo0, w0, _), (t1, la1, lo1, w1, _) in zip(pts[:-1], pts[1:]):
        n = int((t1 - t0).total_seconds() // 3600)
        for h in range(max(n, 1)):
            x = h / max(n, 1)
            out.append((t0 + timedelta(hours=h), la0 + x * (la1 - la0), lo0 + x * (lo1 - lo0), w0 + x * (w1 - w0)))
    t, la, lo, w, _ = pts[-1]
    out.append((t, la, lo, w))
    return out


def qualifying(points, radius):
    return [p for p in points if p[3] >= THRESH_KT and dist_nm(p[1], p[2], *GRENADA) <= radius]


def main(path):
    storms = parse(path)
    print(f"file: {path.split('/')[-1]}   storms: {len(storms)}   threshold {THRESH_KT} kt (Cat 3+), Grenada {GRENADA}")
    raw = {k: [(t, la, lo, w) for t, la, lo, w, _ in s["pts"]] for k, s in storms.items()}
    hr = {k: hourly(s["pts"]) for k, s in storms.items()}
    for kind, tracks in (("RAW 6-hourly (+ special records)", raw), ("INTERPOLATED hourly", hr)):
        print(f"\n=== {kind} ===")
        for r in RADII:
            hits = {}
            for k, pts in tracks.items():
                q = qualifying(pts, r)
                if q:
                    y = int(storms[k]["id"][4:]) if False else min(p[0].year for p in q)
                    hits.setdefault(y, set()).add(storms[k]["name"])
            for y0, y1 in PERIODS:
                yrs = sorted(y for y in hits if y0 <= y <= y1)
                n = y1 - y0 + 1
                print(f"  within {r:3d} nm, {y0}-{y1}: {len(yrs):2d} years / {n} = lambda {len(yrs)/n:.3f}   "
                      + "; ".join(f"{y} {'/'.join(sorted(hits[y]))}" for y in yrs))
    print("\n=== Closest approach (distance in nm, wind in kt at that point) ===")
    for name, year in (("IVAN", 2004), ("EMILY", 2005), ("BERYL", 2024)):
        k = [i for i, s in storms.items() if s["name"] == name and i.endswith(str(year))][0]
        for kind, tracks in (("raw", raw), ("hourly", hr)):
            pts = tracks[k]
            best = min(pts, key=lambda p: dist_nm(p[1], p[2], *GRENADA))
            w100 = max((p[3] for p in pts if dist_nm(p[1], p[2], *GRENADA) <= 100), default=float("nan"))
            print(f"  {name} {year} ({kind}): closest {dist_nm(best[1], best[2], *GRENADA):5.1f} nm at {best[0]:%Y-%m-%d %H:%M}, "
                  f"wind {best[3]:5.1f} kt;  max wind within 100 nm {w100:5.1f} kt")


if __name__ == "__main__":
    main(sys.argv[1])
