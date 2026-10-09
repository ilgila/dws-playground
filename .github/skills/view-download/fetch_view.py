#!/usr/bin/env python3
"""Fetch a single view/dataset for an investment from the Direct Web Services
Investment Details API and save the raw JSON response to the logs/ folder.

Credentials are read from the DWS_USERNAME / DWS_PASSWORD environment
variables (export them first, e.g. `set -a && source .env && set +a`) —
never pass them as command-line arguments, since those can end up in shell
history or process listings.

Usage:
    python3 fetch_view.py --region emea --id US0042391096 --id-type isin \\
        --view-id equity-basic-reference

    python3 fetch_view.py --base-url https://www.us-api.morningstar.com \\
        --id US0042391096 --id-type isin --view-id equity-reference-change \\
        --start-date 2020-01-25 --end-date 2024-01-25

    python3 fetch_view.py --region apac --id FS00008NJG --id-type fundId \\
        --view-id equity-preferred-stock-details --view-type dataset \\
        --param countryId=USA --output exports/my_view.json
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

REGION_BASE_URLS = {
    "americas": "https://www.us-api.morningstar.com",
    "apac": "https://www.apac-api.morningstar.com",
    "emea": "https://www.emea-api.morningstar.com",
}


def sanitize(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value)


def get_token(base_url: str, username: str, password: str) -> str:
    request = urllib.request.Request(
        f"{base_url}/token/oauth",
        method="POST",
    )
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    request.add_header("Authorization", f"Basic {credentials}")
    try:
        with urllib.request.urlopen(request) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Token request failed with HTTP {exc.code}: {exc.read().decode(errors='replace')}"
        ) from exc
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("Token response did not contain an 'access_token' field.")
    return token


def fetch_view(
    base_url: str,
    token: str,
    investment_id: str,
    view_id: str,
    params: dict,
) -> dict:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{base_url}/direct-web-services/v1/investments/{urllib.parse.quote(investment_id)}/{urllib.parse.quote(view_id)}"
    if query:
        url = f"{url}?{query}"

    request = urllib.request.Request(url)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"View request failed with HTTP {exc.code}: {exc.read().decode(errors='replace')}"
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    base_url_group = parser.add_mutually_exclusive_group(required=True)
    base_url_group.add_argument(
        "--region", choices=sorted(REGION_BASE_URLS), help="DWS region shorthand"
    )
    base_url_group.add_argument("--base-url", help="Explicit DWS API base URL")

    parser.add_argument("--id", required=True, help="Investment identifier (ISIN, CUSIP, ticker, etc.)")
    parser.add_argument(
        "--id-type",
        required=True,
        help="Identifier type, e.g. isin, cusip, performanceId, fundId, tradingSymbol, industryCode",
    )
    parser.add_argument(
        "--view-id", required=True, help="View identifier, e.g. equity-basic-reference"
    )
    parser.add_argument(
        "--view-type",
        choices=["package", "dataset"],
        default=None,
        help="Set to 'dataset' when requesting a dataset-level view (default: package view)",
    )
    parser.add_argument("--start-date", help="Time series start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Time series end date (YYYY-MM-DD)")
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Additional query parameter (filters/dependencies), repeatable",
    )
    parser.add_argument(
        "--output", help="Output file path (default: logs/<id>_<viewId>_<date>.json)"
    )
    args = parser.parse_args()

    base_url = args.base_url or REGION_BASE_URLS[args.region]

    username = os.environ.get("DWS_USERNAME")
    password = os.environ.get("DWS_PASSWORD")
    if not username or not password:
        print(
            "DWS_USERNAME / DWS_PASSWORD are not set. Run `set -a && source .env && set +a` first.",
            file=sys.stderr,
        )
        return 1

    extra_params = {}
    for item in args.param:
        if "=" not in item:
            print(f"Invalid --param '{item}', expected NAME=VALUE.", file=sys.stderr)
            return 1
        name, value = item.split("=", 1)
        extra_params[name] = value

    params = {
        "idType": args.id_type,
        "startDate": args.start_date,
        "endDate": args.end_date,
        "viewType": args.view_type,
        **extra_params,
    }

    try:
        token = get_token(base_url, username, password)
        data = fetch_view(base_url, token, args.id, args.view_id, params)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.output:
        output_path = args.output
    else:
        import datetime

        today = datetime.date.today().isoformat()
        output_path = os.path.join(
            "logs", f"{sanitize(args.id)}_{sanitize(args.view_id)}_{today}.json"
        )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Wrote view '{args.view_id}' for investment '{args.id}' to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
