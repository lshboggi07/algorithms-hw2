"""Compare chaining and linear-probing costs and write CSV, SVG, and PDF."""

import csv
import random
from pathlib import Path

from src.hash_table import HashTable, LinearProbingHashTable


CAPACITY = 1000
QUERY_COUNT = 2000
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
OUTPUT_DIR = Path(__file__).parent

RESULT_FIELDS = (
    "load_factor",
    "key_count",
    "measured_chaining_successful",
    "theoretical_chaining_successful",
    "measured_chaining_unsuccessful",
    "theoretical_chaining_unsuccessful",
    "measured_linear_successful",
    "theoretical_linear_successful",
    "measured_linear_unsuccessful",
    "theoretical_linear_unsuccessful",
)


def build_results() -> list[dict[str, float | int]]:
    random_source = random.Random(20261120)
    keys = [
        f"item-{index:04d}-{random_source.getrandbits(64):016x}"
        for index in range(int(CAPACITY * LOAD_FACTORS[-1]))
    ]
    misses = [
        f"miss-{index:04d}-{random_source.getrandbits(64):016x}"
        for index in range(QUERY_COUNT)
    ]

    results: list[dict[str, float | int]] = []
    for load_factor in LOAD_FACTORS:
        key_count = int(CAPACITY * load_factor)
        actual_load = key_count / CAPACITY
        selected_keys = keys[:key_count]
        chaining = HashTable(capacity=CAPACITY)
        linear = LinearProbingHashTable(capacity=CAPACITY)
        for index, key in enumerate(selected_keys):
            chaining.put(key, index)
            linear.put(key, index)

        measured_chaining_successful = sum(
            chaining.probe(key).probes for key in selected_keys
        ) / key_count
        measured_chaining_unsuccessful = sum(
            chaining.probe(key).probes for key in misses
        ) / QUERY_COUNT
        measured_linear_successful = sum(
            linear.probe(key).probes for key in selected_keys
        ) / key_count
        measured_linear_unsuccessful = sum(
            linear.probe(key).probes for key in misses
        ) / QUERY_COUNT

        results.append(
            {
                "load_factor": actual_load,
                "key_count": key_count,
                "measured_chaining_successful": measured_chaining_successful,
                "theoretical_chaining_successful": 1 + actual_load / 2,
                "measured_chaining_unsuccessful": measured_chaining_unsuccessful,
                "theoretical_chaining_unsuccessful": actual_load,
                "measured_linear_successful": measured_linear_successful,
                "theoretical_linear_successful": 0.5
                * (1 + 1 / (1 - actual_load)),
                "measured_linear_unsuccessful": measured_linear_unsuccessful,
                "theoretical_linear_unsuccessful": 0.5
                * (1 + 1 / (1 - actual_load) ** 2),
            }
        )
    return results


def write_csv(results: list[dict[str, float | int]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(results)


def write_svg(results: list[dict[str, float | int]], path: Path) -> None:
    width, height = 1000, 900
    left, right = 90, 35
    plot_width = width - left - right
    panel_height = 340
    panel_tops = (65, 490)
    panels = (
        (
            "Successful search",
            "measured_chaining_successful",
            "theoretical_chaining_successful",
            "measured_linear_successful",
            "theoretical_linear_successful",
            12.0,
            2.0,
        ),
        (
            "Unsuccessful search",
            "measured_chaining_unsuccessful",
            "theoretical_chaining_unsuccessful",
            "measured_linear_unsuccessful",
            "theoretical_linear_unsuccessful",
            60.0,
            10.0,
        ),
    )
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<title>Hash table probe comparison</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="500" y="30" text-anchor="middle" font-size="20">'
        "Measured and theoretical probe counts</text>",
    ]
    series_style = (
        ("chaining", "#1769aa", "Chaining"),
        ("linear", "#d1495b", "Linear probing"),
    )

    for panel_index, panel in enumerate(panels):
        (
            title,
            measured_chain_key,
            theoretical_chain_key,
            measured_linear_key,
            theoretical_linear_key,
            max_y,
            y_step,
        ) = panel
        top = panel_tops[panel_index]
        bottom = top + panel_height
        lines.append(
            f'<text x="500" y="{top - 18}" text-anchor="middle" '
            f'font-size="16">{title}</text>'
        )

        def point(alpha: float, probes: float) -> tuple[float, float]:
            x = left + (alpha - 0.1) / 0.8 * plot_width
            y = top + (max_y - probes) / max_y * panel_height
            return x, y

        tick = 0.0
        while tick <= max_y:
            y = top + (max_y - tick) / max_y * panel_height
            lines.append(
                f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" '
                f'y2="{y:.1f}" stroke="#dddddd"/>'
            )
            lines.append(
                f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" '
                f'font-size="11">{tick:g}</text>'
            )
            tick += y_step

        for row in results:
            alpha = float(row["load_factor"])
            x, _ = point(alpha, 0)
            lines.append(
                f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" '
                f'y2="{bottom}" stroke="#eeeeee"/>'
            )
            lines.append(
                f'<text x="{x:.1f}" y="{bottom + 18}" text-anchor="middle" '
                f'font-size="10">{alpha:.1f}</text>'
            )

        series = (
            (measured_chain_key, "#1769aa", False),
            (theoretical_chain_key, "#1769aa", True),
            (measured_linear_key, "#d1495b", False),
            (theoretical_linear_key, "#d1495b", True),
        )
        for series_index, (key, color, dashed) in enumerate(series):
            coordinates = [
                point(float(row["load_factor"]), float(row[key]))
                for row in results
            ]
            points = " ".join(f"{x:.1f},{y:.1f}" for x, y in coordinates)
            dash = ' stroke-dasharray="6 4"' if dashed else ""
            lines.append(
                f'<polyline points="{points}" fill="none" stroke="{color}" '
                f'stroke-width="2"{dash}/>'
            )
            for x, y in coordinates:
                lines.append(
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{color}"/>'
                )
            if panel_index == 0:
                legend_x = 170 + series_index * 190
                legend_y = 455
                method = series_style[series_index // 2][2]
                measurement = "measured" if series_index % 2 == 0 else "theory"
                lines.append(
                    f'<line x1="{legend_x}" y1="{legend_y - 4}" '
                    f'x2="{legend_x + 25}" y2="{legend_y - 4}" stroke="{color}" '
                    f'stroke-width="2"{dash}/>'
                )
                lines.append(
                    f'<text x="{legend_x + 31}" y="{legend_y}" font-size="11">'
                    f"{method} {measurement}</text>"
                )

        lines.append(
            f'<text x="500" y="{bottom + 38}" text-anchor="middle" '
            'font-size="12">Load factor (items / slots)</text>'
        )

    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pdf_text(value: str) -> str:
    ascii_text = value.encode("ascii", "replace").decode("ascii")
    return ascii_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_pdf(results: list[dict[str, float | int]], path: Path) -> None:
    last = results[-1]
    largest_linear_miss_deviation = max(
        results,
        key=lambda row: abs(
            float(row["measured_linear_unsuccessful"])
            - float(row["theoretical_linear_unsuccessful"])
        ),
    )
    chaining_success_error = sum(
        abs(
            float(row["measured_chaining_successful"])
            - float(row["theoretical_chaining_successful"])
        )
        for row in results
    ) / len(results)
    chaining_failure_error = sum(
        abs(
            float(row["measured_chaining_unsuccessful"])
            - float(row["theoretical_chaining_unsuccessful"])
        )
        for row in results
    ) / len(results)
    linear_success_error = sum(
        abs(
            float(row["measured_linear_successful"])
            - float(row["theoretical_linear_successful"])
        )
        for row in results
    ) / len(results)
    linear_failure_error = sum(
        abs(
            float(row["measured_linear_unsuccessful"])
            - float(row["theoretical_linear_unsuccessful"])
        )
        for row in results
    ) / len(results)

    report_lines = (
        "Method: capacity 1000; identical deterministic keys; load factors 0.1-0.9.",
        "Probe count: inspected nodes for chaining and inspected slots for linear probing.",
        "Theory: chaining success 1+alpha/2; failure alpha.",
        "Theory: linear success (1+1/(1-alpha))/2; failure (1+1/(1-alpha)^2)/2.",
        (
            "Mean absolute error (success/failure): chaining "
            f"{chaining_success_error:.3f}/{chaining_failure_error:.3f}; linear "
            f"{linear_success_error:.3f}/{linear_failure_error:.3f}."
        ),
        (
            "At alpha 0.9, chaining measured success/failure "
            f"{float(last['measured_chaining_successful']):.2f}/"
            f"{float(last['measured_chaining_unsuccessful']):.2f}; theory "
            f"{float(last['theoretical_chaining_successful']):.2f}/"
            f"{float(last['theoretical_chaining_unsuccessful']):.2f}."
        ),
        (
            "At alpha 0.9, linear measured success/failure "
            f"{float(last['measured_linear_successful']):.2f}/"
            f"{float(last['measured_linear_unsuccessful']):.2f}; theory "
            f"{float(last['theoretical_linear_successful']):.2f}/"
            f"{float(last['theoretical_linear_unsuccessful']):.2f}."
        ),
        "Interpretation: chaining stays near its linear-in-load-factor estimates.",
        "Linear probing rises sharply near full capacity because occupied clusters grow.",
        (
            "Largest linear miss deviation: alpha "
            f"{float(largest_linear_miss_deviation['load_factor']):.1f}, measured "
            f"{float(largest_linear_miss_deviation['measured_linear_unsuccessful']):.2f} "
            "vs theory "
            f"{float(largest_linear_miss_deviation['theoretical_linear_unsuccessful']):.2f}; "
            "finite-sample hash clustering violates uniform-hashing assumptions."
        ),
        "At high load, a failed linear search is substantially costlier than chaining.",
        "Reproduce with make experiment; see table_comparison.csv and table_comparison.svg.",
    )
    commands = [
        "BT",
        "/F1 16 Tf",
        "50 790 Td",
        f"({_pdf_text('Hash Table Probe Comparison')}) Tj",
        "/F1 10 Tf",
    ]
    for line in report_lines:
        commands.append("0 -24 Td")
        commands.append(f"({_pdf_text(line)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")

    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    )
    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(
            f"{number} 0 obj\n".encode("ascii")
            + body
            + b"\nendobj\n"
        )
    xref_offset = len(document)
    document.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    document.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(document)


def main() -> None:
    results = build_results()
    csv_path = OUTPUT_DIR / "table_comparison.csv"
    svg_path = OUTPUT_DIR / "table_comparison.svg"
    pdf_path = OUTPUT_DIR / "table_comparison_report.pdf"
    write_csv(results, csv_path)
    write_svg(results, svg_path)
    write_pdf(results, pdf_path)

    print(
        "alpha | chain success/failure | linear success/failure "
        "(measured / theory)"
    )
    for row in results:
        print(
            f"{row['load_factor']:.1f} | "
            f"{row['measured_chaining_successful']:.3f}/"
            f"{row['measured_chaining_unsuccessful']:.3f} "
            f"({row['theoretical_chaining_successful']:.3f}/"
            f"{row['theoretical_chaining_unsuccessful']:.3f}) | "
            f"{row['measured_linear_successful']:.3f}/"
            f"{row['measured_linear_unsuccessful']:.3f} "
            f"({row['theoretical_linear_successful']:.3f}/"
            f"{row['theoretical_linear_unsuccessful']:.3f})"
        )
    print(f"Wrote {csv_path}, {svg_path}, and {pdf_path}")


if __name__ == "__main__":
    main()
