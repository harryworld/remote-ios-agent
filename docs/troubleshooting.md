# Troubleshooting

| Symptom/code | Meaning and next check |
|---|---|
| `device_selection` | No device or ambiguous devices; inspect `devices list`, connect USB or select a configured UDID |
| `dependency_missing` | Install the named optional extra/tool; no fallback to simulation occurs |
| `device_mismatch` | RSD endpoint belongs to another UDID; fix configuration before any mutation |
| `backend_error` with `NotPairedError` | Missing/wrong Apple pairing record; Tailscale cannot replace it |
| Connection refused | Wrong RemotePairing port/address, phone Wi-Fi off, or service unavailable |
| TUN permission failure | Direct RemotePairing needs host capability; use a prepared routed tunnel or configure permissions |
| `timeout` | Operation may have taken effect; reconnect/observe before retrying input or install |
| Missing HID/display service | Developer Mode/DDI/iOS capability gate; inspect status; WDA remains a separate option |
| No visual change after tap | Wrong pixels/focus/orientation, media return path blocked, dropped HID, or genuinely unchanged UI |
| `orientation_mismatch` | Capture dimensions disagree with configured orientation; re-observe, set actual rotation |
| `capability_unavailable` on typing | Non-ASCII text, optional WDA/SDK absent, or explicitly deferred capability |
| Empty logs | No matching live PID records during the window; does not mean the app has no errors |
| `process_failed` on build | Inspect the private build log; check Swift/SDK/linker match and project conversion |
| Install rejected | Check developer identity, profile/device UDID, bundle ID, entitlements, expiry and trust |
| WDA unavailable | Runner not running/signed, session expired, route missing, or XCTest/iOS mismatch |
| Dark screenshot / launch fails | Wake/unlock the phone and verify its state; do not infer a successful screen session |

Use the installed upstream `--help` to diagnose version-specific protocol errors. Default errors expose the upstream exception class, not arbitrary exception bodies that could contain credential data. Pairing state and Tailscale status should be inspected locally; never paste full credential records into issues.

Recovery in 0.1 is explicit: close the session, repair connectivity and create a new session, inspect the screen, then resume from a reviewed workflow step. There are no unlimited retries, automatic device resets, or automatic input replays. Keep reports from failed runs; later steps do not overwrite prior evidence.
