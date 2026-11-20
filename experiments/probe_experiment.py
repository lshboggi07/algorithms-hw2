"""Measure separate-chaining probes across load factors and write CSV/SVG output."""

import csv
import random
from pathlib import Path

from src.hash_table import HashTable


CAPACITY = 400
QUERY_COUNT = 1000
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))
OUTPUT_DIR = Path(__file__).parent


def build_results() -> list[dict[str, float | int]]:
    random_source = random.Random(2026)
    keys: list[str] = []
    for index in range(CAPACITY * 4):
        keys.append(f"item-{index:04d}-{random_source.getrandbits(64):016x}")

    misses = [
        f"miss-{index:04d}-{random_source.getrandbits(64):016x}"
        for index in range(QUERY_COUNT)
    ]

    results: list[dict[str, float | int]] = []
    for load_factor in LOAD_FACTORS:
        key_count = int(CAPACITY * load_factor)
        table = HashTable(capacity=CAPACITY)
        selected_keys = keys[:key_count]
        for index, key in enumerate(selected_keys):
            table.put(key, index)

        measured_successful = sum(
            table.probe(key).probes for key in selected_keys
        ) / key_count
        measured_unsuccessful = sum(
            table.probe(key).probes for key in misses
        ) / QUERY_COUNT
        results.append(
            {
                "load_factor": load_factor,
                "key_count": key_count,
                "measured_successful": measured_successful,
                "theoretical_successful": 1 + load_factor / 2,
                "measured_unsuccessful": measured_unsuccessful,
                "theoretical_unsuccessful": load_factor,
            }
        )
    return results


def write_csv(results: list[dict[str, float | int]], path: Path) -> None:
    fieldnames = (
        "load_factor",
        "key_count",
        "measured_successful",
        "theoretical_successful",
        "measured_unsuccessful",
        "theoretical_unsuccessful",
    )
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def write_svg(results: list[dict[str, float | int]], path: Path) -> None:
    width, height = 900, 520
    left, right, top, bottom = 75, 30, 45, 80
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_alpha, max_probes = 4.0, 6.0

    def point(alpha: float, probes: float) -> tuple[float, float]:
        x = left + alpha / max_alpha * plot_width
        y = top + (max_probes - probes) / max_probes * plot_height
        return x, y

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<title>Separate chaining probe counts by load factor</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="25" text-anchor="middle" font-size="18">'
        "체이닝 적재율과 평균 탐색 횟수</text>",
    ]

    for tick in range(0, 7):
        y = top + (max_probes - tick) / max_probes * plot_height
        lines.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" '
            f'y2="{y:.1f}" stroke="#dddddd"/>'
        )
        lines.append(
            f'<text x="{left - 12}" y="{y + 5:.1f}" text-anchor="end" '
            f'font-size="12">{tick}</text>'
        )
    for tick in range(0, 17, 2):
        alpha = tick / 4
        x, _ = point(alpha, 0)
        lines.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" '
            f'y2="{height - bottom}" stroke="#eeeeee"/>'
        )
        lines.append(
            f'<text x="{x:.1f}" y="{height - bottom + 22}" '
            f'text-anchor="middle" font-size="12">{alpha:g}</text>'
        )

    series = (
        ("measured_successful", "#1769aa", "성공 측정", False),
        ("theoretical_successful", "#1769aa", "성공 이론", True),
        ("measured_unsuccessful", "#d1495b", "실패 측정", False),
        ("theoretical_unsuccessful", "#d1495b", "실패 이론", True),
    )
    for series_index, (key, color, label, dashed) in enumerate(series):
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        coordinates = [
            point(float(row["load_factor"]), float(row[key])) for row in results
        ]
        points = " ".join(f"{x:.1f},{y:.1f}" for x, y in coordinates)
        lines.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            f'stroke-width="2"{dash}/>'
        )
        for x, y in coordinates:
            lines.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{color}"/>'
            )
        legend_x = 160 + (series_index % 2) * 270
        legend_y = height - 27
        lines.append(
            f'<line x1="{legend_x}" y1="{legend_y - 4}" '
            f'x2="{legend_x + 28}" y2="{legend_y - 4}" stroke="{color}" '
            f'stroke-width="2"{dash}/>'
        )
        lines.append(
            f'<text x="{legend_x + 36}" y="{legend_y}" font-size="12">'
            f"{label}</text>"
        )

    lines.extend(
        [
            f'<text x="{left + plot_width / 2}" y="{height - 5}" '
            'text-anchor="middle" font-size="13">적재율 (원소 수 / 버킷 수)</text>',
            f'<text x="18" y="{top + plot_height / 2}" '
            'transform="rotate(-90 18 '
            f'{top + plot_height / 2})" text-anchor="middle" font-size="13">'
            "평균 비교 노드 수</text>",
            "</svg>",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    results = build_results()
    csv_path = OUTPUT_DIR / "probe_results.csv"
    svg_path = OUTPUT_DIR / "probe_experiment.svg"
    write_csv(results, csv_path)
    write_svg(results, svg_path)

    print("α | 성공(측정/이론) | 실패(측정/이론)")
    for row in results:
        print(
            f"{row['load_factor']:.2f} | "
            f"{row['measured_successful']:.3f}/{row['theoretical_successful']:.3f} | "
            f"{row['measured_unsuccessful']:.3f}/"
            f"{row['theoretical_unsuccessful']:.3f}"
        )
    print(f"Wrote {csv_path} and {svg_path}")


if __name__ == "__main__":
    main()
