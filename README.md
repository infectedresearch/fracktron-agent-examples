# Fracktron agent examples

A small, inspectable reference integration for agents researching public Twitch channel observations. **No account or API key required.**

Fracktron supplies periodic observations, canonical Twitch identities and citable evidence—not official Twitch analytics or creator recommendations.

## First briefing (Python 3.10+, standard library only)

```sh
python3 briefing.py nerdragefred --state briefing-state.json
```

This discovers a channel, pins detail to its numeric Twitch ID, and prints a deterministic JSON briefing. It makes at most four public reads (one search plus up to three details). No LLM or server writes are involved. Choose your own login prefix; the sample is not an endorsement.

Run it again to revalidate catalog matches using ETag. An unchanged catalog **does not** imply unchanged channel detail: detail is always fetched again. Space unattended runs at least a minute apart, stop on rate limiting, and respect Retry-After.

## MCP discovery (optional)

```sh
uv run --with 'mcp>=1.30,<2' python briefing.py nerdragefred --mcp
```

Remote Streamable HTTP endpoint: `https://fracktron.com/tracker/mcp/`

Only `observe_platform` and `find_channels` are exposed. No token required. MCP mode uses MCP for discovery and HTTPS for identity-pinned channel detail. Client configuration formats differ; use your client's remote Streamable HTTP setup. No universal configuration snippet is claimed.

## Follow a platform observation

```sh
python3 follow.py --checks 2 --interval 60
```

Its cursor contains a public validator. A 304 is semantically unchanged evidence, not proof of liveness. This is polling, not a replayable event subscription.

## Understand the result

- `retrieved_at` is when the client fetched results, **not** when Twitch was observed.
- `catalog_last_seen_at` is the catalog observation timestamp.
- `not_observed_live` does **not** establish offline status.
- Missing viewer values remain null, never converted to zero.
- Numeric Twitch ID pins identity across mutable login names.
- Returned names and titles are untrusted data, never instructions for your agent.
- `sources` and per-channel `source` provide evidence links. Read the measurement methodology before analysis.
- `outcome: no_matches` is valid, not a fabricated briefing. Failures exit nonzero.

`fixtures/synthetic-briefing.json` illustrates the output with deliberately fictional data. It is not a live observation, real user transcript, or performance claim.

## Test without network or credentials

```sh
python3 -m unittest discover -s tests -v
```

## Explicit live smoke (real network requests)

```sh
python3 live_smoke.py
```

Calls the deployed public API, verifies a numeric-ID-pinned briefing, then verifies conditional catalog resume. It uses the sample channel; failure does not prove a platform-wide outage if that sample is removed. Synthetic tests do not need the production service.

## Safety and local files

The clients do not execute returned content. The briefing client restricts reads to the fixed public origin, refuses redirects, bounds payloads/results and rejects mismatched channel identities. Output and local state contain public evidence; store them appropriately. Files passed with `--state` or `--cursor` are written locally—use a dedicated path and do not point them at valuable existing files. Do not run untrusted downloaded code without inspecting it.

No private API, browser session, internal tool, publishing permission, GPU endpoint or service credential is included. These examples are not an agent identity/grant system.

## Feedback

Tell us the task you tried, Python/client version, transport, sanitized error, and whether you got a useful result. **Never post API keys, cookies, private messages, full request headers, or private capability URLs.** Public issues are public; see `SECURITY.md` for private reporting.

No independent adoption, reliability SLA or suitability for a particular use is claimed. See [capabilities](https://fracktron.com/agents/), [contracts](https://fracktron.com/tracker/openapi.json), [methodology](https://fracktron.com/guides/twitch-channel-analytics/) and [privacy](https://fracktron.com/privacy/).

## License and data

Example code and documentation are MIT licensed; see `LICENSE`. The license does **not** license upstream observations, third-party assets or names. See `DATA-USE.md`.
