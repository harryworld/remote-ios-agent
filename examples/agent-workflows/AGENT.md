# Remote iOS agent instructions

Use `remote-ios` as the canonical interface. Read docs/compatibility.md before claiming a platform capability.

1. Run `doctor`, list devices and select one explicitly. Never substitute the mock backend for a real device failure.
2. Confirm the prepared app/project and device. Builds require trusted local source and authorized SDK/signing inputs.
3. Use a workflow or Python session for sequential operations. All steps need deadlines and an action budget (default 20; never unbounded).
4. Observe a full-resolution screenshot. Use its pixels; re-observe after rotation/layout changes.
5. After input, preserve before/after evidence. A dispatched HID report is not proof of UI success. Prefer an expected accessibility ID or app-state assertion; ROI pixel change is weaker evidence.
6. On timeout, observe before retrying. Do not blindly repeat a tap, submission, payment, install or registered app action.
7. Stop on an error, action limit, deadline, stop-file or user cancellation. Retain artifacts and completed-step reports.
8. Read relevant logs. Empty logs are not a clean bill of health.
9. Keep pairing records, signing material and private captures out of Git/issues. No automatic uploads.
10. Report actual host/transport, real versus simulated execution, evidence paths, unavailable capabilities and the next blocking input.

Grok-specific APIs, browser automation and a desktop are unnecessary. If shell works, use CLI JSON. If standard MCP stdio works, use docs/mcp.md. Do not infer provider features from this instruction file.
