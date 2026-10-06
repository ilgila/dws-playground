---
name: exchange-list
description: Retrieve entitled equity exchanges from the Investment Details API discovery call to /investments without an investment ID, and save the complete response to JSON. Use when asked to list exchanges, markets, borse, or exchange entitlements.
---

# Exchange List

Retrieve the exchanges available to the authenticated account. This is an
investment discovery request, not the list of package/dataset views.
The MCP server provides documentation only; execute the live request over HTTP.

## Steps

1. **Verify the API contract.** Use the `dws-mcp-server` documentation tools
   to confirm the Investment Details API's exchange discovery operation.
   Consult Universe API documentation for the shared `/investments` endpoint
   if needed. Call `get_api_documentation('base-urls')` before generating a
   request and use the documented regional URL. Confirm authentication via
   the getting-started documentation.

2. **Authenticate securely.** Load `DWS_USERNAME` and `DWS_PASSWORD` from the
   workspace `.env` without displaying its contents. Confirm that it is
   git-ignored. Obtain an OAuth2 token with `POST /token/oauth` using Basic
   authentication. Never print credentials or tokens, enable shell tracing,
   or include secrets in output files. Prefer keeping the token in memory;
   if temporary files are necessary, use a unique private temporary directory
   and arrange cleanup on both success and failure.

3. **Request entitled exchanges.** Send
   `GET {baseUrl}/direct-web-services/v1/investments` with Bearer authentication
   and `Accept: application/json`. Do not append an investment ID, `/views`,
   or a view identifier. Do not pass exchange/country filters or pagination
   parameters. For equity discovery, include `source=equities` if required
   by the verified API contract; this selects the source, not an investment.

4. **Check the response.** Require a successful HTTP status and valid JSON
   before saving a successful result. The previously observed response has
   an `investments` array and `metadata.exchanges`, where each exchange has
   `exchangeCode` and `micCode`. Count `metadata.exchanges`, not `investments`.
   An empty exchange array means zero entitled exchanges; a missing array or
   unexpected structure must be reported rather than treated as an empty list.
   Exchanges are markets, not data-package views.

5. **Save the JSON.** Create `logs/` in the workspace if needed and save the
   complete API response to `logs/exchange-list_<YYYY-MM-DD_HHMMSS>.json`,
   using the actual execution time. Preserve `metadata.exchanges` and all
   response metadata without substituting a `views` response or wrapping it
   in a request log. Use a JSON parser/serializer with UTF-8 and indentation.
   Do not overwrite an existing output file. Reopen the saved JSON and verify
   that its exchange count matches the response.

6. **Clean up and report.** Remove only temporary files created by this run
   and unset temporary credential/token variables. Report the documentation
   tool used, endpoint, HTTP status, exchange count, and saved file path.
   On errors, report the status and sanitized API error message, never secrets;
   do not label an error response as a successful exchange export.

## Related Workflow

Use [views-list](../views-list/SKILL.md) for entitled data-package views via
`/investments/views`. That operation does not return exchange entitlements.