from __future__ import annotations

import csv
import json
from bisect import bisect_left, bisect_right
from math import sqrt
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
GRAY = (125, 132, 140)


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


def shell_sets() -> tuple[list[int], list[int]]:
    bound = int(2 * (MAX_D / 2)) + 4
    square: set[int] = set()
    hex_: set[int] = set()
    for a in range(-bound, bound + 1):
        for b in range(-bound, bound + 1):
            s = a * a + b * b
            if MIN_T < s <= MAX_T:
                square.add(s)
            h = a * a + a * b + b * b
            if MIN_T < h <= MAX_T:
                hex_.add(h)
    return sorted(square), sorted(hex_)


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

    def xm(x: float) -> float:
        return xmap(x, panel, xmin, xmax)

    def ym(y: float) -> float:
        return y1 - (y - ymin) / (ymax - ymin) * (y1 - y0)

    for tick in xticks:
        px = xm(tick)
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
    return xm, ym


def window_count(values: list[int], lo: int, hi: int) -> int:
    return bisect_right(values, hi) - bisect_left(values, lo)


def save_threshold_csv(square: list[int], hex_: list[int]) -> list[dict]:
    events: list[dict] = []
    square_set = set(square)
    hex_set = set(hex_)
    for t in sorted(square_set | hex_set):
        square_tick = t in square_set
        hex_tick = t in hex_set
        if square_tick and hex_tick:
            winner = "both"
            score = 0
        elif hex_tick:
            winner = "hex"
            score = 1
        else:
            winner = "square"
            score = -1
        events.append(
            {
                "t": t,
                "diameter": 2 * sqrt(t),
                "square_tick": square_tick,
                "hex_tick": hex_tick,
                "winner": winner,
                "score": score,
            }
        )

    with (OUT_DIR / "lattice_shell_thresholds_20_200.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(events[0].keys()))
        writer.writeheader()
        writer.writerows(events)
    return events


def plot_gap_and_rates(square: list[int], hex_: list[int]) -> list[dict]:
    square_gaps = [(b, b - a) for a, b in zip(square, square[1:])]
    hex_gaps = [(b, b - a) for a, b in zip(hex_, hex_[1:])]
    max_gap = max([g for _, g in square_gaps] + [g for _, g in hex_gaps])

    centers = list(range(MIN_T + 50, MAX_T + 1, 50))
    windows = [100, 250, 500]
    rate_rows: list[dict] = []
    for center in centers:
        row = {"center": center}
        for width in windows:
            lo = center - width // 2
            hi = center + width // 2
            square_count = window_count(square, lo, hi)
            hex_count = window_count(hex_, lo, hi)
            total = square_count + hex_count
            row[f"square_{width}"] = square_count
            row[f"hex_{width}"] = hex_count
            row[f"normalized_{width}"] = (hex_count - square_count) / total if total else 0.0
        rate_rows.append(row)

    with (OUT_DIR / "lattice_shell_rate_windows.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rate_rows[0].keys()))
        writer.writeheader()
        writer.writerows(rate_rows)

    w, h = 1600, 940
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    draw.text((92, 30), "Shell-step spacing and local shell-rate ratio", fill=DARK, font=F_TITLE)
    draw.text(
        (92, 70),
        "Each shell threshold counts once. Multiplicity and edge size are ignored here.",
        fill=MID,
        font=F_SUB,
    )

    p1 = (92, 150, w - 44, 520)
    p2 = (92, 650, w - 44, h - 72)
    xticks = [100, 2000, 4000, 6000, 8000, 10000]
    gap_top = ((max_gap + 9) // 10) * 10
    x1, y1 = draw_axes(
        draw,
        p1,
        MIN_T,
        MAX_T,
        -gap_top,
        gap_top,
        xticks,
        [-gap_top, -gap_top / 2, 0, gap_top / 2, gap_top],
        "Interarrival gap between shell thresholds in R^2",
        "hex gaps above zero; square gaps below zero",
        "R^2",
    )
    zero = y1(0)
    draw.line((p1[0], zero, p1[2], zero), fill=AXIS, width=2)
    for t, gap in hex_gaps:
        px, py = x1(t), y1(gap)
        draw.line((px, zero, px, py), fill=(180, 210, 238), width=1)
        draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=BLUE)
    for t, gap in square_gaps:
        px, py = x1(t), y1(-gap)
        draw.line((px, zero, px, py), fill=(238, 190, 183), width=1)
        draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=RED)

    x2, y2 = draw_axes(
        draw,
        p2,
        MIN_T,
        MAX_T,
        -1,
        1,
        xticks,
        [-1, -0.5, 0, 0.5, 1],
        "Sliding shell-rate advantage",
        "(hex shell count - square shell count) / total shells in window",
        "R^2",
    )
    zero = y2(0)
    draw.line((p2[0], zero, p2[2], zero), fill=AXIS, width=2)
    colors = {100: (36, 116, 191), 250: (34, 145, 95), 500: (137, 82, 180)}
    for width in windows:
        pts = [(x2(row["center"]), y2(row[f"normalized_{width}"])) for row in rate_rows]
        color = colors[width]
        for a, b in zip(pts, pts[1:]):
            draw.line((*a, *b), fill=color, width=2)
        for px, py in pts[::4]:
            draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=color)
    lx, ly = p2[2] - 250, p2[1] + 16
    for i, width in enumerate(windows):
        color = colors[width]
        y = ly + i * 22
        draw.line((lx, y + 7, lx + 24, y + 7), fill=color, width=3)
        draw.text((lx + 34, y), f"window {width}", fill=DARK, font=F_SMALL)
    img.save(OUT_DIR / "lattice_shell_gap_rate_20_200.png")
    return rate_rows


def plot_next_threshold_race(events: list[dict]) -> list[dict]:
    window = 101
    half = window // 2
    rolling: list[dict] = []
    scores = [int(row["score"]) for row in events]
    for i, row in enumerate(events):
        lo = max(0, i - half)
        hi = min(len(events), i + half + 1)
        segment = scores[lo:hi]
        rolling.append(
            {
                "t": row["t"],
                "diameter": row["diameter"],
                "rolling_score": sum(segment) / len(segment),
            }
        )

    with (OUT_DIR / "lattice_shell_rolling_race.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rolling[0].keys()))
        writer.writeheader()
        writer.writerows(rolling)

    w, h = 1500, 820
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    draw.text((90, 30), "Next-threshold race: square shell vs hex shell", fill=DARK, font=F_TITLE)
    draw.text(
        (90, 70),
        "Each unique R^2 threshold is one step. Both-at-once events score 0.",
        fill=MID,
        font=F_SUB,
    )
    p1 = (90, 150, w - 54, 415)
    p2 = (90, 540, w - 54, h - 70)
    xticks = [100, 2000, 4000, 6000, 8000, 10000]
    x1, y1 = draw_axes(
        draw,
        p1,
        MIN_T,
        MAX_T,
        -1.2,
        1.2,
        xticks,
        [-1, 0, 1],
        "Raw shell winner at each threshold",
        "hex = +1; square = -1; both = 0",
        "R^2",
    )
    zero = y1(0)
    draw.line((p1[0], zero, p1[2], zero), fill=AXIS, width=2)
    for row in events:
        px = x1(row["t"])
        py = y1(row["score"])
        color = BLUE if row["score"] > 0 else RED if row["score"] < 0 else GRAY
        draw.ellipse((px - 2, py - 2, px + 2, py + 2), fill=color)

    x2, y2 = draw_axes(
        draw,
        p2,
        MIN_T,
        MAX_T,
        -1,
        1,
        xticks,
        [-1, -0.5, 0, 0.5, 1],
        f"Rolling winner score over {window} shell events",
        "positive = hex shells locally arrive more often; negative = square shells do",
        "R^2",
    )
    zero = y2(0)
    draw.line((p2[0], zero, p2[2], zero), fill=AXIS, width=2)
    pts = [(x2(row["t"]), y2(row["rolling_score"])) for row in rolling]
    for a, b in zip(pts, pts[1:]):
        draw.line((*a, *b), fill=GRAY, width=2)
    for row, (px, py) in zip(rolling[::20], pts[::20]):
        color = BLUE if row["rolling_score"] >= 0 else RED
        draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=color)
    img.save(OUT_DIR / "lattice_shell_next_threshold_race.png")
    return rolling


def write_summary(
    square: list[int],
    hex_: list[int],
    events: list[dict],
    rate_rows: list[dict],
    rolling: list[dict],
) -> None:
    def gap_stats(values: list[int]) -> dict:
        gaps = [b - a for a, b in zip(values, values[1:])]
        gaps_sorted = sorted(gaps)
        return {
            "count": len(gaps),
            "min": gaps_sorted[0],
            "median": gaps_sorted[len(gaps_sorted) // 2],
            "mean": sum(gaps) / len(gaps),
            "max": gaps_sorted[-1],
        }

    winner_counts = {
        "square": sum(row["winner"] == "square" for row in events),
        "hex": sum(row["winner"] == "hex" for row in events),
        "both": sum(row["winner"] == "both" for row in events),
    }
    window_summaries = {}
    for width in [100, 250, 500]:
        vals = [row[f"normalized_{width}"] for row in rate_rows]
        window_summaries[str(width)] = {
            "min": min(vals),
            "max": max(vals),
            "mean": sum(vals) / len(vals),
            "negative_centers": [
                row["center"] for row in rate_rows if row[f"normalized_{width}"] < 0
            ][:20],
            "negative_count": sum(row[f"normalized_{width}"] < 0 for row in rate_rows),
        }
    rolling_vals = [row["rolling_score"] for row in rolling]
    summary = {
        "diameter_range": [MIN_D, MAX_D],
        "r2_range": [MIN_T, MAX_T],
        "square_shell_count": len(square),
        "hex_shell_count": len(hex_),
        "combined_threshold_count": len(events),
        "winner_counts": winner_counts,
        "square_gap_stats_r2": gap_stats(square),
        "hex_gap_stats_r2": gap_stats(hex_),
        "window_summaries": window_summaries,
        "rolling_score_min": min(rolling_vals),
        "rolling_score_max": max(rolling_vals),
        "rolling_score_mean": sum(rolling_vals) / len(rolling_vals),
    }
    with (OUT_DIR / "lattice_shell_step_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def main() -> None:
    square, hex_ = shell_sets()
    events = save_threshold_csv(square, hex_)
    rate_rows = plot_gap_and_rates(square, hex_)
    rolling = plot_next_threshold_race(events)
    write_summary(square, hex_, events, rate_rows, rolling)
    print(f"square_shells={len(square)}")
    print(f"hex_shells={len(hex_)}")
    print(f"combined_thresholds={len(events)}")
    print(f"outputs={OUT_DIR}")


if __name__ == "__main__":
    main()
