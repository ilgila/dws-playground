---
name: views-list
description: Retrieve entitled investment data-package and dataset views from the Investment Details API and save them to JSON. Use when asked to list available views or packages, not exchanges or markets.
---

# Views List

Retrieve the list of investment data views and packages
that your account is entitled to access via the Direct Web Services
Investment Details API, and save the results to a JSON file for reference.

## Steps

1. **Get credentials.** Look for `DWS_USERNAME` / `DWS_PASSWORD` in the
   workspace's `.env` file (or ask the user to add them there). Never print
   these values, or any token derived from them, in chat — only use them
   inside terminal commands. Make sure `.env` is listed in
   [.gitignore](../../../.gitignore).

2. **Pick the base URL for the region.** From the `getting-started` /
   `investment-details-equities-api` docs (use the `dws-mcp-server` MCP
   documentation tools to confirm):

   | Region | Base URL |
   |--------|----------|
   | Americas | `https://www.us-api.morningstar.com` |
   | APAC | `https://www.apac-api.morningstar.com` |
   | EMEA | `https://www.emea-api.morningstar.com` |

3. **Request an OAuth2 token.** Use the `/token/oauth` endpoint with Basic Auth:

   ```bash
   set -a && source .env && set +a
   curl --silent --location --request POST \
     --user "${DWS_USERNAME}:${DWS_PASSWORD}" \
     "<baseUrl>/token/oauth" \
     -o /tmp/dws_token.json -w "HTTP_STATUS=%{http_code}\n"
   ```

   Extract `access_token` from the response (use Python/jq without echoing
   the token to chat).

4. **Call the List Views endpoint.** This endpoint returns all view identifiers
   (package and dataset names) representing exchanges, markets, and data
   packages your account is entitled to:

   ```bash
   TOKEN=$(python3 -c "import json;print(json.load(open('/tmp/dws_token.json'))['access_token'])")
   curl --silent --location \
     "<baseUrl>/direct-web-services/v1/investments/views" \
     --header "Authorization: Bearer ${TOKEN}" \
     --header "Content-Type: application/json" \
     -o /tmp/dws_views.json
   ```

5. **Save to JSON file in the workspace.** Copy the response to a persisted
   location and clean up temporary files:

   ```bash
   mkdir -p logs
   cp /tmp/dws_views.json "logs/views_$(date +%Y-%m-%d).json"
   rm -f /tmp/dws_token.json /tmp/dws_views.json
   ```

6. **Report back.** Tell the user the output file path and confirm the number
   of views retrieved.

## Response Format

The response is a JSON object with a `views` array. Each item contains:

```json
{
  "views": [
    {
      "package": {
        "viewId": "equity-basic-reference"
      },
      "isSync": true,
      "isAsync": false
    },
    ...
  ],
  "metadata": {
    "requestId": "...",
    "time": "..."
  }
}
```

Each `viewId` represents a data package/view available in your entitlements,
with flags indicating whether sync and/or async retrieval is supported.

## Notes

- This endpoint lists all view identifiers (e.g., `equity-basic-reference`,
  `equitySnapshot`, `custom-view1`) that represent different data packages.
- The `views` endpoint does not require filter parameters — it returns your
  complete entitled universe of views in a single call (no paging).
- Tokens are short-lived (~45-60 minutes). If the call fails with 401
  Unauthorized, refresh the token by re-running the `/token/oauth` call.
- Never hardcode credentials or tokens in committed files; read them from
  `.env` (git-ignored) at run time.
