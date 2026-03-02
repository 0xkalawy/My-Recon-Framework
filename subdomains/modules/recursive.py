#!/usr/bin/env python3

"""
Recursive multi-level subdomain extractor.

Extracts parent domains from subdomains that exceed a given depth
to enable recursive fuzzing or re-enumeration.
"""

import argparse
from pathlib import Path


def extract_recursive_targets(
    input_file: Path,
    output_file: Path,
    min_depth: int = 4,
    exclude_www: bool = True,
    base_domain: str | None = None,
):
    """
    Extract parent domains from deep subdomains.

    Example:
        a.b.c.example.com -> b.c.example.com
        b.c.example.com   -> c.example.com
    """

    seen = set()
    results = set()

    with input_file.open("r") as f:
        for line in f:
            domain = line.strip().lower()
            if not domain or domain in seen:
                continue

            seen.add(domain)

            parts = domain.split(".")

            # optional base-domain filter
            if base_domain and not domain.endswith(base_domain):
                continue

            if len(parts) >= min_depth:

                if exclude_www and parts[0].startswith(("www", "ww")):
                    continue

                parent = ".".join(parts[1:])
                results.add(parent)

    if results:
        with output_file.open("w") as f:
            for item in sorted(results):
                f.write(item + "\n")

    return len(results)


def main():
    parser = argparse.ArgumentParser(
        description="Extract recursive multi-level domains for further fuzzing."
    )

    parser.add_argument("input", help="Input file containing subdomains")
    parser.add_argument(
        "-o", "--output", default="recursive_targets.txt",
        help="Output file"
    )
    parser.add_argument(
        "--min-depth", type=int, default=4,
        help="Minimum label depth to trigger extraction (default: 4)"
    )
    parser.add_argument(
        "--base-domain", help="Only process subdomains of this base domain"
    )
    parser.add_argument(
        "--include-www", action="store_true",
        help="Do not exclude www/ww prefixes"
    )

    args = parser.parse_args()

    count = extract_recursive_targets(
        input_file=Path(args.input),
        output_file=Path(args.output),
        min_depth=args.min_depth,
        exclude_www=not args.include_www,
        base_domain=args.base_domain,
    )

    print(f"[+] Extracted {count} recursive targets")


if __name__ == "__main__":
    main()
