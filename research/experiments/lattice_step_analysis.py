from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from math import log2, sqrt
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MIN_D = 20.0
MAX_D = 200.0
MIN_T = int((MIN_D / 2) ** 2)
MAX_T = int((MAX_D / 2) ** 2)
OUT_DIR = Path(__file__).resolve().parent

BLUE = (36, 116, 191)
RED = (201, 70, 55)
DARK = (36, 38, 42)
MID = (78, 84, 92)
GRID = (224, 228, 232)
AXIS = (90, 96, 104)
LIGHT_BLUE = (170, 205, 235)
LIGHT_RED = (236, 185, 177)
GRAY = (130, 136, 144)
LIGHT_GRAY = (247, 248, 250)


@dataclass(frozen=True)
class Event:
    t: int
    diameter: float
    square_points: int
    hex_points: int
    square_edge_step: int
    hex_edge_step: int
    residue12: int
    square_ok: bool
    hex_ok: bool
    factor_class: str

    @property
    def signed_log_ratio(self) -> float:
        return log2((self.hex_edge_step + 1) / (self.square_edge_step + 1))

    @property
    def signed_advantage(self) -> int:
        return self.hex_edge_step - self.square_edge_step

    @property
    def normalized_advantage(self) -> float:
        total = self.hex_edge_step + self.square_edge_step
        return self.signed_advantage / total if total else 0.0

    @property
    def tick_type(self) -> str:
        if self.square_edge_step and self.hex_edge_step:
            return "both"
        if self.square_edge_step:
            return "square_only"
        if self.hex_edge_step:
            return "hex_only"
        return "none"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


F_TITLE = font(28, True)
F_SUB = font(17)
F_AXIS = font(15)
F_SMALL = font(13)
F_TINY = font(11)


def factorize(n: int) -> dict[int, int]:
    factors: dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def square_representable(factors: dict[int, int]) -> bool:
    return all(exp % 2 == 0 for p, exp in factors.items() if p % 4 == 3)


def hex_representable(factors: dict[int, int]) -> bool:
    return all(exp % 2 == 0 for p, exp in factors.items() if p % 3 == 2)


def factor_class(factors: dict[int, int]) -> str:
    has_square_split = any(p % 4 == 1 for p in factors)
    has_hex_split = any(p % 3 == 1 for p in factors)
    if has_square_split and has_hex_split:
        return "both_split_primes"
    if has_square_split:
        return "square_split_only"
    if has_hex_split:
        return "hex_split_only"
    return "no_split_prime"


def edge_delta(
    new_points: list[tuple[int, int]],
    present_before: set[tuple[int, int]],
    directions: list[tuple[int, int]],
) -> int:
    new = set(new_points)
    old_new = 0
    new_new_directed = 0
    for a, b in new:
        for da, db in directions:
            q = (a + da, b + db)
            if q in present_before:
                old_new += 1
            elif q in new:
                new_new_directed += 1
    return old_new + new_new_directed // 2


def build_events() -> list[Event]:
    bound = int(2 * (MAX_D / 2)) + 4
    square_by_t: defaultdict[int, list[tuple[int, int]]] = defaultdict(list)
    hex_by_t: defaultdict[int, list[tuple[int, int]]] = defaultdict(list)

    for a in range(-bound, bound + 1):
        for b in range(-bound, bound + 1):
            square_t = a * a + b * b
            if square_t <= MAX_T:
                square_by_t[square_t].append((a, b))
            hex_t = a * a + a * b + b * b
            if hex_t <= MAX_T:
                hex_by_t[hex_t].append((a, b))

    square_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    hex_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
    square_present: set[tuple[int, int]] = set()
    hex_present: set[tuple[int, int]] = set()
    events: list[Event] = []

    for t in sorted(set(square_by_t) | set(hex_by_t)):
        if t > MAX_T:
            break
        square_new = square_by_t.get(t, [])
        hex_new = hex_by_t.get(t, [])
        square_step = edge_delta(square_new, square_present, square_dirs) if square_new else 0
        hex_step = edge_delta(hex_new, hex_present, hex_dirs) if hex_new else 0
        square_present.update(square_new)
        hex_present.update(hex_new)
        if t <= MIN_T or not (square_step or hex_step):
            continue
        factors = factorize(t)
        events.append(
            Event(
                t=t,
                diameter=2 * sqrt(t),
                square_points=len(square_new),
                hex_points=len(hex_new),
                square_edge_step=square_step,
                hex_edge_step=hex_step,
                residue12=t % 12,
                square_ok=square_representable(factors),
                hex_ok=hex_representable(factors),
                factor_class=factor_class(factors),
            )
        )
    return events


def xmap(x: float, panel: tuple[int, int, int, int], xmin: float, xmax: float) -> float:
    x0, _, x1, _ = panel
    return x0 + (x - xmin) / (xmax - xmin) * (x1 - x0)


def draw_axes(
    draw: ImageDraw.ImageDraw,
    panel: tuple[int, int, int, int],
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    xticks: list[float],
    yticks: list[float],
    title: str,
    subtitle: str,
    xlabel: str,
) -> tuple:
    x0, y0, x1, y1 = panel
    draw.rectangle(panel, outline=(210, 214, 219), width=1)
    draw.text((x0, y0 - 32), title, fill=DARK, font=F_SUB)
    if subtitle:
        draw.text((x0, y0 - 55), subtitle, fill=MID, font=F_SMALL)

    def ym(y: float) -> float:
        return y1 - (y - ymin) / (ymax - ymin) * (y1 - y0)

    for tick in xticks:
        px = xmap(tick, panel, xmin, xmax)
        draw.line((px, y0, px, y1), fill=GRID, width=1)
        label = f"{tick:g}"
        tw = draw.textlength(label, font=F_AXIS)
        draw.text((px - tw / 2, y1 + 10), label, fill=MID, font=F_AXIS)
    for tick in yticks:
        py = ym(tick)
        draw.line((x0, py, x1, py), fill=GRID, width=1)
        label = f"{tick:g}"
        tw = draw.textlength(label, font=F_AXIS)
        draw.text((x0 - tw - 10, py - 8), label, fill=MID, font=F_AXIS)
    draw.text((x0 + (x1 - x0) / 2 - 34, y1 + 40), xlabel, fill=MID, font=F_AXIS)
    return (
        lambda x: xmap(x, panel, xmin, xmax),
        ym,
    )


def save_events_csv(events: list[Event]) -> None:
    path = OUT_DIR / "lattice_step_events_20_200.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "t",
                "diameter",
                "square_points",
                "hex_points",
                "square_edge_step",
                "hex_edge_step",
                "signed_advantage",
                "normalized_advantage",
                "signed_log_ratio",
                "residue12",
                "tick_type",
                "square_ok",
                "hex_ok",
                "factor_class",
            ],
        )
        writer.writeheader()
        for e in events:
            writer.writerow(
                {
                    "t": e.t,
                    "diameter": f"{e.diameter:.12f}",
                    "square_points": e.square_points,
                    "hex_points": e.hex_points,
                    "square_edge_step": e.square_edge_step,
                    "hex_edge_step": e.hex_edge_step,
                    "signed_advantage": e.signed_advantage,
                    "normalized_advantage": f"{e.normalized_advantage:.12f}",
                    "signed_log_ratio": f"{e.signed_log_ratio:.12f}",
                    "residue12": e.residue12,
                    "tick_type": e.tick_type,
                    "square_ok": e.square_ok,
                    "hex_ok": e.hex_ok,
                    "factor_class": e.factor_class,
                }
            )


def plot_events_by_r2(events: list[Event]) -> None:
    w, h = 1600, 980
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    draw.text((92, 30), "Boundary step events in native R^2 coordinate", fill=DARK, font=F_TITLE)
    draw.text(
        (92, 70),
        "Each threshold is an integer value of R^2. This removes the square-root warp from diameter.",
        fill=MID,
        font=F_SUB,
    )

    p1 = (92, 150, w - 44, 555)
    p2 = (92, 680, w - 44, h - 72)
    xticks = [100, 2000, 4000, 6000, 8000, 10000]
    top = 200
    x1, y1 = draw_axes(
        draw,
        p1,
        MIN_T,
        MAX_T,
        -top,
        top,
        xticks,
        [-200, -100, 0, 100, 200],
        "Raw event sizes: hex steps above zero, square steps below zero",
        "new unit edges at a boundary threshold",
        "R^2",
    )
    zero = y1(0)
    draw.line((p1[0], zero, p1[2], zero), fill=AXIS, width=2)
    for e in events:
        px = x1(e.t)
        if e.hex_edge_step:
            py = y1(e.hex_edge_step)
            draw.line((px, zero, px, py), fill=LIGHT_BLUE, width=1)
            draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=BLUE)
        if e.square_edge_step:
            py = y1(-e.square_edge_step)
            draw.line((px, zero, px, py), fill=LIGHT_RED, width=1)
            draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=RED)

    bound = 8
    x2, y2 = draw_axes(
        draw,
        p2,
        MIN_T,
        MAX_T,
        -bound,
        bound,
        xticks,
        [-8, -4, 0, 4, 8],
        "Signed step ratio: log2((hex_edge_step + 1) / (square_edge_step + 1))",
        "positive = hex event larger; negative = square event larger",
        "R^2",
    )
    zero = y2(0)
    draw.line((p2[0], zero, p2[2], zero), fill=AXIS, width=2)
    points = [(x2(e.t), y2(e.signed_log_ratio)) for e in events]
    for a, b in zip(points, points[1:]):
        draw.line((*a, *b), fill=(214, 218, 223), width=1)
    for e in events:
        px, py = x2(e.t), y2(e.signed_log_ratio)
        color = BLUE if e.hex_edge_step > e.square_edge_step else RED
        draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=color)
    img.save(OUT_DIR / "lattice_step_events_by_r2.png")


def binned(events: list[Event], key: str, width: int) -> list[dict]:
    rows: list[dict] = []
    if key == "t":
        start = MIN_T
        end = MAX_T
        value = lambda e: e.t
    else:
        start = int(MIN_D)
        end = int(MAX_D)
        value = lambda e: e.diameter
    bins = list(range(start, end, width))
    for lo in bins:
        hi = lo + width
        items = [e for e in events if lo < value(e) <= hi]
        square = sum(e.square_edge_step for e in items)
        hex_ = sum(e.hex_edge_step for e in items)
        total = square + hex_
        rows.append(
            {
                "lo": lo,
                "hi": hi,
                "mid": (lo + hi) / 2,
                "events": len(items),
                "square": square,
                "hex": hex_,
                "advantage": hex_ - square,
                "normalized": (hex_ - square) / total if total else 0.0,
            }
        )
    return rows


def save_bins_csv(rows: list[dict], name: str) -> None:
    path = OUT_DIR / name
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def plot_bins(rows: list[dict], name: str, x_label: str, title: str) -> None:
    w, h = 1500, 860
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    draw.text((90, 30), title, fill=DARK, font=F_TITLE)
    draw.text(
        (90, 70),
        "Top: edge-step sums. Bottom: normalized advantage (hex - square) / (hex + square).",
        fill=MID,
        font=F_SUB,
    )
    p1 = (90, 145, w - 54, 465)
    p2 = (90, 590, w - 54, h - 70)
    xmin, xmax = rows[0]["lo"], rows[-1]["hi"]
    max_abs = max(abs(r["advantage"]) for r in rows)
    top = ((max_abs + 499) // 500) * 500 or 500
    xticks = [xmin] + [r["hi"] for r in rows if (r["hi"] - xmin) % ((xmax - xmin) // 5 or 1) == 0]
    xticks = sorted(set([round(x) for x in xticks if xmin <= x <= xmax]))
    x1, y1 = draw_axes(
        draw,
        p1,
        xmin,
        xmax,
        -top,
        top,
        xticks,
        [-top, -top / 2, 0, top / 2, top],
        "Binned signed edge-step advantage",
        "positive = hex added more edges in the bin; negative = square did",
        x_label,
    )
    zero = y1(0)
    draw.line((p1[0], zero, p1[2], zero), fill=AXIS, width=2)
    bar_half = (p1[2] - p1[0]) / len(rows) * 0.42
    for r in rows:
        px = x1(r["mid"])
        py = y1(r["advantage"])
        color = BLUE if r["advantage"] >= 0 else RED
        draw.rectangle((px - bar_half, min(zero, py), px + bar_half, max(zero, py)), fill=color)

    x2, y2 = draw_axes(
        draw,
        p2,
        xmin,
        xmax,
        -1,
        1,
        xticks,
        [-1, -0.5, 0, 0.5, 1],
        "Binned normalized advantage",
        "",
        x_label,
    )
    zero = y2(0)
    draw.line((p2[0], zero, p2[2], zero), fill=AXIS, width=2)
    pts = [(x2(r["mid"]), y2(r["normalized"])) for r in rows]
    for a, b in zip(pts, pts[1:]):
        draw.line((*a, *b), fill=GRAY, width=2)
    for r, (px, py) in zip(rows, pts):
        color = BLUE if r["normalized"] >= 0 else RED
        draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=color)
    img.save(OUT_DIR / name)


def plot_decomposition(events: list[Event]) -> dict:
    tick_counts = Counter(e.tick_type for e in events)
    type_sums = defaultdict(lambda: {"events": 0, "square": 0, "hex": 0})
    for e in events:
        row = type_sums[e.tick_type]
        row["events"] += 1
        row["square"] += e.square_edge_step
        row["hex"] += e.hex_edge_step

    w, h = 1300, 720
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    draw.text((90, 30), "Timing versus magnitude decomposition", fill=DARK, font=F_TITLE)
    draw.text(
        (90, 70),
        "Left: which lattice ticks at a threshold. Right: total edge magnitude by tick type.",
        fill=MID,
        font=F_SUB,
    )
    labels = ["square_only", "hex_only", "both"]

    def panel_bar(panel, values, title, ylabel):
        x0, y0, x1, y1 = panel
        ymax = max(values) or 1
        ymax = ((ymax + 499) // 500) * 500 if ymax > 1000 else ((ymax + 49) // 50) * 50
        draw.rectangle(panel, outline=(210, 214, 219), width=1)
        draw.text((x0, y0 - 32), title, fill=DARK, font=F_SUB)
        draw.text((x0, y0 - 55), ylabel, fill=MID, font=F_SMALL)
        for i, (label, val) in enumerate(zip(labels, values)):
            cx = x0 + (i + 0.5) * (x1 - x0) / len(labels)
            bw = (x1 - x0) / len(labels) * 0.45
            py = y1 - val / ymax * (y1 - y0)
            color = RED if label == "square_only" else BLUE if label == "hex_only" else (100, 100, 100)
            draw.rectangle((cx - bw / 2, py, cx + bw / 2, y1), fill=color)
            tw = draw.textlength(label, font=F_AXIS)
            draw.text((cx - tw / 2, y1 + 12), label, fill=MID, font=F_AXIS)
            text = str(val)
            tw = draw.textlength(text, font=F_AXIS)
            draw.text((cx - tw / 2, py - 22), text, fill=DARK, font=F_AXIS)

    panel_bar((90, 150, 610, 560), [tick_counts[label] for label in labels], "Threshold-event counts", "number of thresholds")
    panel_bar(
        (740, 150, 1260, 560),
        [type_sums[label]["square"] + type_sums[label]["hex"] for label in labels],
        "Total edge steps contributed",
        "square + hex edge steps",
    )
    img.save(OUT_DIR / "lattice_step_decomposition.png")

    return {
        "tick_counts": dict(tick_counts),
        "type_sums": {k: dict(v) for k, v in type_sums.items()},
    }


def residue_tables(events: list[Event]) -> tuple[list[dict], list[dict]]:
    residues: list[dict] = []
    for residue in range(12):
        items = [e for e in events if e.residue12 == residue]
        if not items:
            continue
        square = sum(e.square_edge_step for e in items)
        hex_ = sum(e.hex_edge_step for e in items)
        residues.append(
            {
                "residue12": residue,
                "events": len(items),
                "square_edges": square,
                "hex_edges": hex_,
                "advantage": hex_ - square,
                "normalized": (hex_ - square) / (hex_ + square),
                "square_only": sum(e.tick_type == "square_only" for e in items),
                "hex_only": sum(e.tick_type == "hex_only" for e in items),
                "both": sum(e.tick_type == "both" for e in items),
            }
        )
    classes: list[dict] = []
    for name in sorted(set(e.factor_class for e in events)):
        items = [e for e in events if e.factor_class == name]
        square = sum(e.square_edge_step for e in items)
        hex_ = sum(e.hex_edge_step for e in items)
        classes.append(
            {
                "factor_class": name,
                "events": len(items),
                "square_edges": square,
                "hex_edges": hex_,
                "advantage": hex_ - square,
                "normalized": (hex_ - square) / (hex_ + square),
                "square_only": sum(e.tick_type == "square_only" for e in items),
                "hex_only": sum(e.tick_type == "hex_only" for e in items),
                "both": sum(e.tick_type == "both" for e in items),
            }
        )
    return residues, classes


def plot_residue_factor(residues: list[dict], classes: list[dict]) -> None:
    w, h = 1500, 880
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    draw.text((90, 30), "Residue and factor-class diagnostics", fill=DARK, font=F_TITLE)
    draw.text(
        (90, 70),
        "Normalized advantage groups events by R^2 residue or by split-prime availability.",
        fill=MID,
        font=F_SUB,
    )

    def normalized_panel(panel, rows, label_key, title):
        x0, y0, x1, y1 = panel
        draw.rectangle(panel, outline=(210, 214, 219), width=1)
        draw.text((x0, y0 - 32), title, fill=DARK, font=F_SUB)
        zero = y0 + (y1 - y0) / 2
        draw.line((x0, zero, x1, zero), fill=AXIS, width=2)
        for tick in [-1, -0.5, 0, 0.5, 1]:
            py = y1 - (tick + 1) / 2 * (y1 - y0)
            draw.line((x0, py, x1, py), fill=GRID, width=1)
            label = f"{tick:g}"
            tw = draw.textlength(label, font=F_AXIS)
            draw.text((x0 - tw - 10, py - 8), label, fill=MID, font=F_AXIS)
        bar_w = (x1 - x0) / len(rows) * 0.55
        for i, row in enumerate(rows):
            cx = x0 + (i + 0.5) * (x1 - x0) / len(rows)
            val = row["normalized"]
            py = y1 - (val + 1) / 2 * (y1 - y0)
            color = BLUE if val >= 0 else RED
            draw.rectangle((cx - bar_w / 2, min(zero, py), cx + bar_w / 2, max(zero, py)), fill=color)
            label = str(row[label_key])
            tw = draw.textlength(label, font=F_AXIS)
            draw.text((cx - tw / 2, y1 + 12), label, fill=MID, font=F_AXIS)
            event_label = str(row["events"])
            tw = draw.textlength(event_label, font=F_TINY)
            draw.text((cx - tw / 2, y1 + 32), event_label, fill=GRAY, font=F_TINY)

    normalized_panel((90, 150, 1410, 450), residues, "residue12", "By R^2 mod 12")
    normalized_panel((90, 590, 1410, 780), classes, "factor_class", "By coarse factor class")
    draw.text((90, 822), "Small labels under bars are event counts.", fill=MID, font=F_SMALL)
    img.save(OUT_DIR / "lattice_step_residue_factor.png")


def autocorrelation(values: list[float], max_lag: int) -> list[tuple[int, float]]:
    mean = sum(values) / len(values)
    centered = [v - mean for v in values]
    denom = sum(v * v for v in centered)
    rows = []
    for lag in range(1, max_lag + 1):
        num = sum(centered[i] * centered[i + lag] for i in range(len(values) - lag))
        rows.append((lag, num / denom if denom else 0.0))
    return rows


def plot_autocorrelation(rows: list[dict]) -> list[tuple[int, float]]:
    values = [r["normalized"] for r in rows]
    corrs = autocorrelation(values, min(80, len(values) - 2))
    w, h = 1400, 700
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    draw.text((90, 30), "Autocorrelation of binned normalized advantage", fill=DARK, font=F_TITLE)
    draw.text(
        (90, 70),
        "Computed on R^2 bins of width 100. No strong clean periodicity means no sine-like driver.",
        fill=MID,
        font=F_SUB,
    )
    panel = (90, 145, w - 60, h - 80)
    max_abs = max(abs(c) for _, c in corrs)
    bound = max(0.25, round(max_abs + 0.1, 1))
    x, y = draw_axes(
        draw,
        panel,
        1,
        corrs[-1][0],
        -bound,
        bound,
        [1, 10, 20, 40, 60, 80],
        [-bound, 0, bound],
        "Lag correlation",
        "",
        "lag in R^2 bins",
    )
    zero = y(0)
    draw.line((panel[0], zero, panel[2], zero), fill=AXIS, width=2)
    pts = [(x(lag), y(corr)) for lag, corr in corrs]
    for a, b in zip(pts, pts[1:]):
        draw.line((*a, *b), fill=GRAY, width=2)
    for lag, corr in corrs:
        px, py = x(lag), y(corr)
        color = BLUE if corr >= 0 else RED
        draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=color)
    img.save(OUT_DIR / "lattice_step_autocorrelation.png")
    return corrs


def write_summary(
    events: list[Event],
    diameter_bins: list[dict],
    r2_bins: list[dict],
    decomposition: dict,
    residues: list[dict],
    classes: list[dict],
    corrs: list[tuple[int, float]],
) -> None:
    top_positive = sorted(events, key=lambda e: e.signed_advantage, reverse=True)[:10]
    top_negative = sorted(events, key=lambda e: e.signed_advantage)[:10]
    strongest_corrs = sorted(corrs, key=lambda row: abs(row[1]), reverse=True)[:10]
    summary = {
        "diameter_range": [MIN_D, MAX_D],
        "r2_range": [MIN_T, MAX_T],
        "event_count": len(events),
        "total_square_edges": sum(e.square_edge_step for e in events),
        "total_hex_edges": sum(e.hex_edge_step for e in events),
        "tick_counts": decomposition["tick_counts"],
        "top_hex_bursts": [
            {
                "t": e.t,
                "diameter": e.diameter,
                "square_edge_step": e.square_edge_step,
                "hex_edge_step": e.hex_edge_step,
                "advantage": e.signed_advantage,
                "residue12": e.residue12,
                "factor_class": e.factor_class,
            }
            for e in top_positive
        ],
        "top_square_bursts": [
            {
                "t": e.t,
                "diameter": e.diameter,
                "square_edge_step": e.square_edge_step,
                "hex_edge_step": e.hex_edge_step,
                "advantage": e.signed_advantage,
                "residue12": e.residue12,
                "factor_class": e.factor_class,
            }
            for e in top_negative
        ],
        "r2_bins_negative": [r for r in r2_bins if r["advantage"] < 0],
        "diameter_bins_negative": [r for r in diameter_bins if r["advantage"] < 0],
        "residue_rows": residues,
        "factor_class_rows": classes,
        "strongest_autocorrelations": [
            {"lag": lag, "correlation": corr} for lag, corr in strongest_corrs
        ],
    }
    with (OUT_DIR / "lattice_step_analysis_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def main() -> None:
    events = build_events()
    save_events_csv(events)

    plot_events_by_r2(events)

    diameter_bins = binned(events, "diameter", 1)
    r2_bins = binned(events, "t", 100)
    save_bins_csv(diameter_bins, "lattice_step_bins_by_diameter.csv")
    save_bins_csv(r2_bins, "lattice_step_bins_by_r2.csv")
    plot_bins(diameter_bins, "lattice_step_bins_by_diameter.png", "diameter", "Binned boundary-step advantage by diameter")
    plot_bins(r2_bins, "lattice_step_bins_by_r2.png", "R^2", "Binned boundary-step advantage by native R^2")

    decomposition = plot_decomposition(events)

    residues, classes = residue_tables(events)
    with (OUT_DIR / "lattice_step_residue_rows.json").open("w", encoding="utf-8") as f:
        json.dump({"residues": residues, "factor_classes": classes}, f, indent=2)
    plot_residue_factor(residues, classes)

    corrs = plot_autocorrelation(r2_bins)
    with (OUT_DIR / "lattice_step_autocorrelation.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["lag", "correlation"])
        writer.writerows(corrs)

    write_summary(events, diameter_bins, r2_bins, decomposition, residues, classes, corrs)

    print(f"events={len(events)}")
    print(f"square_edges={sum(e.square_edge_step for e in events)}")
    print(f"hex_edges={sum(e.hex_edge_step for e in events)}")
    print(f"outputs={OUT_DIR}")


if __name__ == "__main__":
    main()
