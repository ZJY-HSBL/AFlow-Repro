#!/usr/bin/env python3
"""Convert real AFlow results.json into an honest SVG score-per-round plot."""
import argparse
import html
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


def summarize(records):
    buckets = defaultdict(list)
    for record in records:
        if not isinstance(record, dict) or "round" not in record or "score" not in record:
            raise ValueError("Every result requires 'round' and 'score'.")
        round_number = int(record["round"])
        score = float(record["score"])
        if round_number < 1 or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("Round must be positive and scores in [0, 1].")
        buckets[round_number].append(score)
    if not buckets:
        raise ValueError("No measured scores to plot; refusing to invent results.")
    return [(round_number, statistics.mean(scores), len(scores))
            for round_number, scores in sorted(buckets.items())]


def render_svg(summary, title):
    width, height = 840, 340
    left, right, top, bottom = 80, 28, 64, 58
    w, h = width - left - right, height - top - bottom
    rounds = [r for r, _, _ in summary]
    low, high = min(rounds), max(rounds)

    def xcoord(round_number):
        return left + w * (round_number - low) / max(1, high - low)

    def ycoord(score):
        return top + h * (1 - score)

    ticks = "".join(
        f'<line x1="{left}" y1="{ycoord(i/4):.1f}" x2="{width-right}" '
        f'y2="{ycoord(i/4):.1f}" stroke="#d5dce3" />'
        f'<text x="{left-12}" y="{ycoord(i/4)+4:.1f}" text-anchor="end" '
        f'font-size="12" fill="#566">{25*i}%</text>'
        for i in range(5)
    )
    coords = " ".join(f"{xcoord(r):.1f},{ycoord(score):.1f}" for r, score, _ in summary)
    circles = "".join(
        f'<circle cx="{xcoord(r):.1f}" cy="{ycoord(score):.1f}" r="5" '
        f'fill="#067f85"><title>round {r}: {score:.4f}; n={n}</title></circle>'
        for r, score, n in summary
    )
    labels = "".join(
        f'<text x="{xcoord(r):.1f}" y="{height-bottom+20}" '
        f'text-anchor="middle" font-size="11" fill="#566">{r}</text>'
        for r, _, _ in summary
    ) if len(summary) <= 16 else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
        f'<title>{html.escape(title)}</title>'
        f'<rect width="{width}" height="{height}" fill="#fff"/>'
        f'<text x="{left}" y="35" font-size="20" font-family="Arial" '
        f'fill="#172e39">{html.escape(title)}</text>'
        f'{ticks}<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#789"/>'
        f'<polyline points="{coords}" fill="none" stroke="#067f85" stroke-width="3"/>'
        f'{circles}{labels}'
        f'<text x="{width/2}" y="{height-12}" text-anchor="middle" '
        f'font-family="Arial" font-size="13" fill="#566">Optimization round</text>'
        f'</svg>'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Actual workflows/results.json")
    parser.add_argument("--output", required=True, help="SVG destination")
    parser.add_argument("--title", default="AFlow validation scores (measured)")
    args = parser.parse_args()
    records = json.loads(Path(args.input).read_text(encoding="utf-8"))
    summary = summarize(records)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_svg(summary, args.title), encoding="utf-8")
    print(f"Saved {len(summary)} measured rounds to {dest}")


if __name__ == "__main__":
    main()
