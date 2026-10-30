# Contributing

Use Python 3.12+ and `uv sync --frozen --all-extras`. Run `uv run pytest -m 'not hardware'`, `uv run ruff check .` and `uv run ruff format --check .`.

Keep device operations behind the backend/session interface. Add regression tests for behavior changes and upstream adapter contracts. Never turn missing hardware into mock success; mock selection must be explicit. Do not automatically replay an action after an unknown-effect timeout. Keep CLI/MCP/Python error semantics consistent and retain partial artifacts on workflow failures.

Hardware receipts must identify OS/device model, host OS/architecture, dependency versions, transport, pairing/DDI prerequisites, actual commands, observed UI effect and limitations. Sanitize identifiers/private paths. A screenshot or command exit alone is not a tap-delivery receipt.

Do not commit pairing records, signing material, proprietary SDKs, private logs/screenshots or account credentials. Report security problems privately to the repository owner rather than publishing a secret in an issue. Contribution code must be compatible with the component's license (root GPL-3.0-only; independent SDK MIT).
