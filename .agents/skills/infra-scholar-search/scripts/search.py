#!/usr/bin/env python3
"""Direct client for the configured Infra Agent Scholar API."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


DEFAULT_CREDENTIALS = Path.home() / ".config" / "infra-agent" / "credentials.json"
USER_AGENT = "infra-scholar-search/1.0"


class ClientError(Exception):
    pass


def load_credentials(path: Path) -> tuple[str, str]:
    try:
        file_stat = path.stat()
    except OSError as exc:
        raise ClientError(f"Credential file is unavailable: {path}") from exc

    if os.name == "posix" and stat.S_IMODE(file_stat.st_mode) & 0o077:
        raise ClientError(f"Credential file must have mode 600: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClientError(f"Credential file is not valid JSON: {path}") from exc

    scholar_url = data.get("scholar_url")
    access_key = data.get("ak")
    if not isinstance(scholar_url, str) or not isinstance(access_key, str):
        raise ClientError("Credential file must contain scholar_url and ak strings")

    parsed = urlsplit(scholar_url)
    if parsed.scheme != "https" or not parsed.netloc or not parsed.path.endswith("/scholar"):
        raise ClientError("Configured scholar_url is not a valid HTTPS scholar endpoint")
    if not access_key.strip():
        raise ClientError("Configured access key is empty")

    return scholar_url, access_key


def decode_json(body: bytes) -> dict[str, Any]:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClientError("Scholar API returned a non-JSON response") from exc
    if not isinstance(value, dict):
        raise ClientError("Scholar API returned an unexpected JSON value")
    return value


def call_api(
    scholar_url: str,
    access_key: str,
    query: str | None,
    timeout: float,
) -> tuple[int, dict[str, Any]]:
    url = scholar_url
    if query is not None:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urlencode({'q': query})}"

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_key}",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, decode_json(response.read())
    except HTTPError as exc:
        return exc.code, decode_json(exc.read())
    except URLError as exc:
        reason = getattr(exc, "reason", "connection failed")
        raise ClientError(f"Scholar API request failed: {reason}") from exc
    except TimeoutError as exc:
        raise ClientError("Scholar API request timed out") from exc


def api_code(payload: dict[str, Any]) -> Any:
    if "code" in payload:
        return payload["code"]
    error = payload.get("error")
    return error.get("code") if isinstance(error, dict) else None


def api_message(payload: dict[str, Any]) -> str | None:
    for key in ("message", "msg"):
        if isinstance(payload.get(key), str):
            return payload[key]
    error = payload.get("error")
    if isinstance(error, dict) and isinstance(error.get("message"), str):
        return error["message"]
    return None


def normalize_result(item: dict[str, Any]) -> dict[str, Any]:
    extra = item.get("extra_data")
    if not isinstance(extra, dict):
        extra = {}
    return {
        "title": item.get("name") or item.get("title"),
        "url": item.get("url"),
        "date_published": item.get("date_published"),
        "snippet": item.get("snippet"),
        "abstract": item.get("abstract"),
        "authors": extra.get("authors"),
        "citations": extra.get("cite_by"),
        "doi": extra.get("doi"),
        "journal": extra.get("journal_title"),
        "pdf": extra.get("pdf"),
    }


def normalize_response(
    payload: dict[str, Any], query: str, max_results: int | None
) -> dict[str, Any]:
    web_pages = payload.get("web_pages")
    if not isinstance(web_pages, dict):
        web_pages = payload.get("webPages")
    if not isinstance(web_pages, dict):
        web_pages = {}

    values = web_pages.get("value")
    if not isinstance(values, list):
        values = []
    items = [normalize_result(item) for item in values if isinstance(item, dict)]
    if max_results is not None:
        items = items[:max_results]

    return {
        "query": query,
        "request_id": payload.get("requestId") or payload.get("request_id"),
        "returned_by_api": len(values),
        "results_in_output": len(items),
        "results": items,
    }


def markdown_value(value: Any) -> str:
    if value is None or value == "":
        return "Not provided"
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False)
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Scholar search results",
        "",
        f"- Query: `{result['query']}`",
        f"- Returned by API: {result['returned_by_api']}",
        f"- Included below: {result['results_in_output']}",
    ]
    for index, item in enumerate(result["results"], start=1):
        lines.extend(
            [
                "",
                f"## {index}. {markdown_value(item['title'])}",
                "",
                f"- URL: {markdown_value(item['url'])}",
                f"- DOI: {markdown_value(item['doi'])}",
                f"- Journal: {markdown_value(item['journal'])}",
                f"- Published: {markdown_value(item['date_published'])}",
                f"- Authors: {markdown_value(item['authors'])}",
                f"- Citations: {markdown_value(item['citations'])}",
                f"- PDF: {markdown_value(item['pdf'])}",
                "",
                markdown_value(item["abstract"] or item["snippet"]),
            ]
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search scholarly literature through Infra Agent's HTTP API."
    )
    parser.add_argument("query", nargs="?", help="Exact paper title or focused query")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate credentials without performing a search",
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        default=Path(os.environ.get("INFRA_AGENT_CREDENTIALS", DEFAULT_CREDENTIALS)),
        help="credential JSON path (default: %(default)s)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "raw"),
        default="json",
        help="output format (default: %(default)s)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        help="truncate local output; does not alter the API request",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.check and args.query:
        parser.error("query cannot be used with --check")
    if not args.check and not args.query:
        parser.error("query is required unless --check is used")
    if args.max_results is not None and args.max_results < 1:
        parser.error("--max-results must be at least 1")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    try:
        scholar_url, access_key = load_credentials(args.credentials)
        status, payload = call_api(
            scholar_url,
            access_key,
            None if args.check else args.query,
            args.timeout,
        )
    except ClientError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2

    if args.check:
        code = api_code(payload)
        ok = status == 400 and str(code) == "1103"
        print(
            json.dumps(
                {
                    "ok": ok,
                    "transport": "direct-http",
                    "http_status": status,
                    "api_code": code,
                }
            )
        )
        return 0 if ok else 1

    if status != 200:
        print(
            json.dumps(
                {
                    "ok": False,
                    "http_status": status,
                    "api_code": api_code(payload),
                    "message": api_message(payload),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    if args.format == "raw":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    result = normalize_response(payload, args.query, args.max_results)
    if args.format == "markdown":
        print(render_markdown(result), end="")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
