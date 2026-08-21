---
name: infra-scholar-search
description: Directly search scholarly literature through the configured Infra Agent Scholar HTTP API. Use for paper discovery, title or DOI lookup, academic-source searches, or checking whether a paper in docs/references can be found. This is the project-default academic search path; it does not use OpenCLI or a browser.
---

# Infra Scholar Search

Run academic searches through the repository's deterministic API client:

```bash
python3 .agents/skills/infra-scholar-search/scripts/search.py \
  '<paper title or focused academic query>' \
  --format json
```

The client reads `~/.config/infra-agent/credentials.json` by default and calls the configured `/scholar` endpoint directly. Use `--credentials PATH` only when the user has supplied another approved credential file.

## Workflow

1. Build one high-signal query. Use the exact English title when known; otherwise combine the biological object, task, and method. Run one query first.
2. Inspect titles, DOI values, publication venues, URLs, and abstracts. Treat each result as a candidate, not proof that the original text was retrieved.
3. Verify selected candidates through their publisher, DOI, preprint, repository, or project URL using direct HTTP access. Distinguish a valid link from a page whose text is actually accessible.
4. Refine the query once only when the first result set is materially incomplete. Report the query count and unresolved gaps.
5. When the task adds or evaluates project literature, follow the repository rules for `docs/references/INDEX.md`.

For detailed response fields, cost notes, and verified service behavior, read [`docs/Infra-Agent-Research-Search-Guide.md`](../../../docs/Infra-Agent-Research-Search-Guide.md).

## Authentication Check

Use the non-searching probe when credentials or connectivity need validation:

```bash
python3 .agents/skills/infra-scholar-search/scripts/search.py --check
```

Success means the direct HTTP request returned the expected HTTP `400` and API code `1103` for a missing `q`. This validates authentication without executing a scholarly query.

## Output

- `--format json` returns normalized, machine-readable results and is the default for agent workflows.
- `--format markdown` produces a readable candidate list.
- `--format raw` preserves the API response for schema investigation.
- `--max-results N` truncates local output only; it does not change the upstream request or its cost.

The endpoint's verified limit is QPS 3. Run searches sequentially unless concurrency is necessary, and never exceed three simultaneous requests. Only `q` is verified for `/scholar`; the client deliberately sends no undocumented search parameters.

## Credential Boundary

Keep the credential file outside the repository with mode `600`. The client validates its permissions and never emits the AK or configured endpoint. Do not print the file, enable shell tracing around a request, commit credentials, or place secrets in query arguments.
