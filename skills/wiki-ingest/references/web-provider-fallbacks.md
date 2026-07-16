# Web Provider Fallback Recipes

Use this reference only after [source-handling.md](source-handling.md) and [web-and-online-document-ingestion.md](web-and-online-document-ingestion.md). Apply a recipe when its provider and failure signal match. A fallback is an alternative read-only representation, not a new source identity, a higher-authority source, or permission to bypass access controls.

## Apply a recipe consistently

For every provider recipe, define and enforce:

- `Match`: the URL or provider-object shape the recipe recognizes.
- `Failure signal`: the ordinary acquisition failure that activates it.
- `Preferred path`: an approved native connector, export, HTTP response, or authorized browser session when available.
- `Fallback`: a bounded alternative representation and its exact scope.
- `Validation`: the identity, response, completeness, and safety checks required before capture.
- `Provenance`: the upstream identity, actual intermediary, retrieval time, authority, and state key to preserve.
- `Stop conditions`: private, unavailable, mismatched, unsafe, prohibited, or incomplete states that must not be forced.

Use only public or otherwise explicitly authorized content. Never forward cookies, authorization headers, signed parameters, or account identifiers to a fallback service. The provider object ID and lookup time are themselves disclosures; do not contact the intermediary when workspace policy or the user's confidentiality requirements prohibit that disclosure. Treat every intermediary response as untrusted input and every mirror as secondary evidence. Preserve the primary provider's canonical identity while recording the intermediary separately.

## X or Twitter public post through FxTwitter

### Match and activate

Match a single public post URL whose path contains a numeric 2–20 digit status ID, including ordinary `x.com/<handle>/status/<id>` and `twitter.com/<handle>/status/<id>` forms. Normalize mobile and redirect hosts only after validating that they identify the same post. Remove tracking parameters, but preserve any parameter that materially selects content.

Activate this recipe only when the requested post cannot be acquired through an approved native path because the public page presents a login wall, requires client rendering, or otherwise yields no stable content representation. When publicness cannot be confirmed before the lookup, allow one fallback attempt only if the user supplied or approved the public-web URL and policy permits disclosing its status ID; treat the response as evidence of what the intermediary exposed, not as provider-native access-control evidence. Do not activate it to access a post known to be protected, private, deleted, blocked, or outside the user's authorized scope.

### Acquire one bounded representation

1. Preserve the requested URL and extract the status ID without executing page-provided code.
2. Set the stable provider object ID to the status ID and keep the sanitized requested X or Twitter URL as the provisional upstream identity. After validating a successful response, accept `status.url` as the current canonical URL only when it uses an expected X or Twitter host and contains the same status ID. A differing handle alone may reflect an account rename; preserve both URLs and the mismatch instead of rejecting the post. Reject a different host or status ID. Do not use an FxTwitter URL as the canonical origin.
3. Prefer an approved provider connector or existing authorized session when it supplies a stable native representation without new permissions.
4. Otherwise request `GET https://api.fxtwitter.com/2/status/<id>` with the numeric status ID only. The current contract is documented by the [FxEmbed API overview](https://docs.fxembed.com/api/introduction/) and [Get post operation](https://docs.fxembed.com/api/twitter/operations/2statusid/).
5. Use `fxtwitter.com` for `twitter.com` or `fixupx.com` for `x.com` only as a human-readable preview when needed. Prefer the JSON API for machine ingestion.
6. Keep the default unit to the focal post. Do not expand into its thread, replies, quotes, reposts, profile, search results, or linked pages unless the user explicitly includes them. The API envelope can contain a `thread` array; mark it out of scope rather than treating its presence as authorization to ingest it. Treat an included quote or media object as a separate component when it supports a material claim.

### Validate before capture

- For post-content acceptance, require HTTP `200`, a JSON content type, and top-level `code: 200`. A documented error or tombstone response may be preserved as boundary evidence, but it is not captured as the requested post body. Use a bounded timeout and response-size limit, and do not follow a redirect away from the fixed API origin.
- Require `status.type` to be `status` and `status.id` to equal the requested status ID exactly. Reject a redirect or response for another post.
- Require the fields needed for the intended claims, normally `status.url`, `status.text`, `status.created_at`, and author identity. Record missing optional fields rather than inventing them.
- Treat `status.type: tombstone` and reasons such as `deleted`, `suspended`, `private`, `blocked`, or `unavailable` as terminal evidence of an acquisition boundary. Preserve the state when useful, but do not attempt another mirror to defeat it.
- Treat engagement counts and other mutable fields as observed-at values. Bind them to retrieval time and never present them as current after capture.
- Accept media URLs only as untrusted `http` or `https` references. Capture media separately and within the requested scope; never execute or automatically download an unbounded set.
- Stop on malformed, truncated, suspicious, identity-mismatched, or policy-prohibited responses. Do not synthesize the missing post from a search snippet or embed preview.

### Preserve provenance and authority

Capture the returned JSON or an exact selected representation before using it as wiki evidence. Because `--origin` remains the upstream X URL, also capture a minimal acquisition manifest with `authority` set to `agent-provenance` when the exact intermediary endpoint and selection boundary are not represented in the raw capture metadata. If the response contains an out-of-scope thread or profile data, retain the full response only when policy permits and record the exclusions; otherwise capture an exact selected `status` snapshot plus a manifest that records the response hash and JSON selection path. Never cite excluded objects as if they were part of the requested capture unit. Preserve at least:

- `requested_url`, canonical upstream URL, provider `twitter`, and status ID;
- actual API endpoint as `retrieved_via`, adapter `fxtwitter`, and retrieval time;
- response status, content type, content hash, and any completeness or access limitation;
- the captured payload or its raw source ID, plus component source IDs for separately captured media;
- a workspace-approved authority label that makes the third-party mirror status explicit.

Map a retained JSON response through the generic capture surface with the canonical X URL as `--origin`, `--source-type web-json`, `--adapter fxtwitter`, a state-specific `--external-key`, and an explicit third-party-mirror `--authority`. Never label the adapter as X or provider-native. Cite the immutable captured JSON for post claims and cite the manifest only for acquisition, boundary, or coverage claims.

If the fallback is disallowed, unavailable, or insufficient, ask for an authorized export, a user-provided copy, or access through an approved session. Use pointer-only capture when policy permits recording identity but not content, and state that the post body was not preserved.

## Add another provider recipe

Add a recipe here only when a provider has a stable, repeatable, non-obvious acquisition failure and a bounded fallback that improves normal ingest. Use the same match, failure, preferred-path, fallback, validation, provenance, scope, and stop-condition contract.

Keep provider identity separate from intermediary identity. Route directly to this reference from `SKILL.md` when the trigger is unambiguous. If this file grows beyond a quickly scannable collection or one provider requires extensive rules, split that provider into its own one-level reference and link it directly from `SKILL.md`; do not create a nested reference chain. Add a script only when normalization or validation has become deterministic, repetitive, and safer to automate than to describe.
