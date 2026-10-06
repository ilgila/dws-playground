#!/usr/bin/env python3
"""Convert a JSON array of universe records into an Excel file.

Usage:
    python3 export_to_excel.py --input data.json --output universe.xlsx [--limit 100] [--no-flatten]

The input file must contain a JSON array of records, or an object with a
top-level "investments"/"data"/"records"/"items"/"results" array. Records are
flattened by default, since DWS API responses nest fields under objects like
"companyInformation"/"shareClassInformation" and wrap enums as {"value":..,"code":..}.
"""
import argparse
import json
import sys


def load_records(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("investments", "data", "records", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value

    raise ValueError(
        "Input JSON must be an array of records, or an object containing an "
        "'investments'/'data'/'records'/'items'/'results' array."
    )


def flatten_record(record: dict, parent_key: str = "") -> dict:
    flat: dict = {}
    for key, value in record.items():
        full_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            # collapse {"value": ..., "code": ...} enum objects to a single column
            if set(value.keys()) <= {"value", "code"} and "value" in value:
                flat[full_key] = value.get("value")
            else:
                flat.update(flatten_record(value, full_key))
        else:
            flat[full_key] = value
    return flat


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the input JSON file")
    parser.add_argument("--output", required=True, help="Path to the output .xlsx file")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only export the first N records",
    )
    parser.add_argument(
        "--no-flatten",
        action="store_true",
        help="Write records as-is instead of flattening nested objects into columns",
    )
    args = parser.parse_args()

    try:
        import pandas as pd
    except ImportError:
        print(
            "Missing dependencies. Install them with: pip install pandas openpyxl",
            file=sys.stderr,
        )
        return 1

    records = load_records(args.input)
    if args.limit is not None:
        records = records[: args.limit]
    if not args.no_flatten:
        records = [flatten_record(r) for r in records]

    df = pd.DataFrame(records)
    df.to_excel(args.output, index=False, engine="openpyxl")

    print(f"Wrote {len(df)} record(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
