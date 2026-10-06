---
name: universe-export
description: Download the data of a universe via the DWS Universe API (base URL + OAuth2 credentials from .env) and export it to an Excel file, with the option to cap the extraction to the first N records. Use when asked to export, download, or extract a universe (e.g. an exchange/market's equities) to Excel/xlsx.
---

# Universe export to Excel

Export the constituents of a DWS universe (e.g. all equities on a given
exchange) to an `.xlsx` file, with an optional limit on how many records to
extract. This workflow calls the live Direct Web Services APIs directly over
HTTP — the `dws-mcp-server` MCP tools only provide documentation/swagger, they
don't execute requests.

## Steps

1. **Get credentials.** Look for `DWS_USERNAME` / `DWS_PASSWORD` in the
   workspace's `.env` file (or ask the user to add them there). Never print
   these values, or any token derived from them, in chat — only use them
   inside terminal commands. Make sure `.env` is listed in
   [.gitignore](../../../.gitignore) before doing anything else.

2. **Pick the base URL for the region.** From the `getting-started` /
   `universe-api` docs (use the `dws-mcp-server` MCP documentation tools to
   confirm, since this can change):

   | Region | Base URL |
   |--------|----------|
   | Americas | `https://www.us-api.morningstar.com` |
   | APAC | `https://www.apac-api.morningstar.com` |
   | EMEA | `https://www.emea-api.morningstar.com` |

   European markets (e.g. Borsa Italiana) use **EMEA**.

3. **Request an OAuth2 token.** Direct Web Services APIs use OAuth 2.0:

   ```bash
   set -a && source .env && set +a
   curl --silent --location --request POST \
     --user "${DWS_USERNAME}:${DWS_PASSWORD}" \
     "<baseUrl>/token/oauth" \
     -o /tmp/dws_token.json -w "HTTP_STATUS=%{http_code}\n"
   ```

   Use `--user user:pass` (curl Basic Auth) instead of hand-building the
   Base64 header. The response contains `access_token`, `token_type`, and
   `expires_in` (tokens are short-lived, ~45-60 minutes) — read `access_token`
   out of the file with Python/jq without echoing it to chat.

4. **Identify the universe/exchange filter.** If the exchange code isn't
   already known, discover the entitled filters first:

   ```bash
   TOKEN=$(python3 -c "import json;print(json.load(open('/tmp/dws_token.json'))['access_token'])")
   curl --silent --location \
     "<baseUrl>/direct-web-services/v1/investments?source=equities" \
     --header "Authorization: Bearer ${TOKEN}" \
     -o /tmp/dws_universe_filters.json
   ```

   Inspect `metadata.exchanges` (list of `{exchangeCode, micCode}`) for the
   market the user asked about (e.g. search for `MIL`/`XMIL` for Borsa
   Italiana). If more than one candidate matches, prefer the primary market
   code and mention the alternative(s) to the user.

5. **Determine the record limit and fetch the data.** Check if the user asked
   to cap the extraction (e.g. "primi 50 record"):
   - Pass it as the server-side `pageSize` parameter (max 50 per page) to
     avoid downloading unnecessary data.
   - If the requested limit is more than 50, page through results using
     `paginationTokenNext` from the response `metadata` until the limit is
     reached or no token is returned, keeping all other filters identical
     across requests.
   - If no limit is requested, page through everything until
     `paginationTokenNext` is absent.

   ```bash
   curl --silent --location \
     "<baseUrl>/direct-web-services/v1/investments?source=equities&exchangeCode=<code>&pageSize=<N<=50>" \
     --header "Authorization: Bearer ${TOKEN}" \
     -o /tmp/dws_universe_data.json
   ```

6. **Export to Excel** with the helper script
   [export_to_excel.py](./export_to_excel.py). It auto-detects the
   `investments` array in the raw API response and flattens nested objects
   (e.g. `companyInformation.legalName`, `shareClassInformation.isin`) into
   columns, collapsing `{"value":..,"code":..}` enum fields to their `value`:

   ```bash
   mkdir -p exports
   python3 ".github/skills/universe-export/export_to_excel.py" \
     --input /tmp/dws_universe_data.json \
     --output "exports/<market>_universe_<YYYY-MM-DD>.xlsx" \
     --limit <N>
   ```

   - Pass `--limit` again here as a safety net even after a server-side
     `pageSize`, so the Excel file never exceeds what the user asked for.
   - Install dependencies first if missing: `pip install pandas openpyxl`.

7. **Clean up.** Remove the temporary token/response files from `/tmp` (e.g.
   `rm -f /tmp/dws_token.json /tmp/dws_universe_*.json`) so the access token
   doesn't linger on disk.

8. **Report back.** Tell the user the output file path, the number of
   records written, the exchange/filter used, and whether a limit was
   applied.

## Notes

- Never hardcode credentials, tokens, or URLs in committed files; read them
  from `.env` (git-ignored) at run time.
- The `dws-mcp-server` MCP server is documentation-only — use its tools to
  confirm endpoints/parameters before calling them, but make the actual HTTP
  requests yourself (curl/Python) with the token obtained in step 3.
- If the universe is very large, prefer a requested/sane default limit (ask
  the user) rather than exporting an unbounded dataset.
