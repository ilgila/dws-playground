---
name: view-download
description: Download a single package or dataset view for one investment from the Direct Web Services Investment Details API and save the raw JSON response to logs. Use when asked to download/fetch/export a specific view or dataset (e.g. equity-basic-reference) for a given investment (ISIN, CUSIP, ticker, etc.), as opposed to listing available views or a whole universe.
---

# View Download

Fetch a single package or dataset view (e.g. `equity-basic-reference`,
`equity-preferred-stock-details`) for one investment from the Direct Web
Services Investment Details API, and persist the raw JSON response to the
`logs/` folder.

## Steps

1. **Get credentials.** Look for `DWS_USERNAME` / `DWS_PASSWORD` in the
   workspace's `.env` file (or ask the user to add them there). Never print
   these values, or any token derived from them, in chat — only use them
   inside terminal commands. Make sure `.env` is listed in
   [.gitignore](../../../.gitignore).

2. **Pick the region.** Ask the user if not already known:

   | Region | Base URL |
   |--------|----------|
   | Americas | `https://www.us-api.morningstar.com` |
   | APAC | `https://www.apac-api.morningstar.com` |
   | EMEA | `https://www.emea-api.morningstar.com` |

3. **Identify the required inputs.** If not already known, confirm with the
   user (or discover via the `views-list` skill / `exchange-list` skill):
   - `id` — the investment identifier (ISIN, CUSIP, Morningstar performance
     ID, fund identifier, trading symbol, or industry code).
   - `idType` — the type of the `id` above (e.g. `isin`, `cusip`,
     `performanceId`, `fundId`, `tradingSymbol`, `industryCode`).
   - `viewId` — the package or dataset view identifier (e.g.
     `equity-basic-reference`). Use the `views-list` skill first if the
     user doesn't know the exact identifier.
   - Whether the view is a **dataset** view (pass `--view-type dataset`) —
     package views are the default.
   - For time-series-enabled views, a `startDate`/`endDate` range.

4. **Run the helper script**
   [fetch_view.py](./fetch_view.py). It requests the OAuth2 token and the
   view in one go, then writes the response JSON to `logs/`:

   ```bash
   set -a && source .env && set +a
   python3 ".github/skills/view-download/fetch_view.py" \
     --region <americas|apac|emea> \
     --id "<id>" \
     --id-type "<idType>" \
     --view-id "<viewId>"
   ```

   Optional flags:
   - `--view-type dataset` for dataset-level views.
   - `--start-date YYYY-MM-DD --end-date YYYY-MM-DD` for time series views.
   - `--param name=value` (repeatable) for view-specific filters/dependencies
     (e.g. `--param countryId=USA`, `--param period=annual`).
   - `--output <path>` to override the default
     `logs/<id>_<viewId>_<date>.json` path.
   - `--base-url <url>` instead of `--region` if the URL needs to be
     confirmed/overridden from the `dws-mcp-server` documentation tools.

5. **Report back.** Tell the user the output file path and a short summary
   of what was retrieved (investment id, view id, and whether the request
   succeeded).

## Example

```bash
set -a && source .env && set +a
python3 ".github/skills/view-download/fetch_view.py" \
  --region emea \
  --id "US0042391096" \
  --id-type isin \
  --view-id equity-basic-reference
```

This writes the response to
`logs/US0042391096_equity-basic-reference_<date>.json`.

## Notes

- The endpoint pattern is
  `GET {baseUrl}/direct-web-services/v1/investments/{id}/{viewId}`, with
  `idType` (and any view-specific filters) as query parameters.
- Never hardcode credentials or tokens in committed files; read them from
  `.env` (git-ignored) at run time. The script itself never echoes the
  token or credentials.
- Tokens are short-lived (~45-60 minutes); the script requests a fresh
  token on every run, so no manual refresh step is needed.
- If the exact `viewId` isn't known, run the `views-list` skill first to
  list the account's entitled views.
