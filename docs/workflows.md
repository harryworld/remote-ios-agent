# Bounded workflows

`remote-ios workflow run FILE --max-actions 20 --workflow-timeout 120 --stop-file /tmp/stop-ios` executes a list of explicit operations in one device session. It checkpoints a private JSON report before/after every step and preserves earlier results on failure. The stop-file is checked between operations; each operation has its own deadline.

Available operations: build, sign, package, install, launch, terminate, screenshot, observe, tap, swipe, long_press, type_text, press, logs, wait, interact_verify, compare, assert_equal. Arguments match the Python methods. No arbitrary shell command, Python expression, or Swift evaluation operation is provided.

Arguments can reference an earlier completed result:

```json
{"operation":"install","arguments":{"path":{"from_step":1,"field":"path"}}}
```

Only prior completed steps and existing object fields are accepted. Dot-separated fields can select nested results. This avoids accidentally installing a stale, separately named IPA after a new build. It is data selection, not an expression language.

- [Build and inspect](../examples/agent-workflows/build-inspect.example.json): build → sign exact build result → install exact signing result → launch → screenshot → logs. Replace signing input paths and choose a new output path; the signer refuses overwriting an existing IPA. Run with a prepared real device and `--workflow-timeout 900` for compilation. Mock selection does not fake compiler/signing success.
- [Interact and verify / smoke](../examples/agent-workflows/smoke.json): capture → tap → capture → compare. Its supplied coordinates/ROI target the mock; choose actual device coordinates for hardware.
- [Visual regression](../examples/agent-workflows/visual-regression.example.json): launch → wait → capture → assert_equal against a reviewed baseline. Add explicit navigation actions and an ROI for the real app. Mismatches fail with `visual_regression` and retain comparison metrics. Masks, perceptual metrics and baseline approval tooling are deferred.
- Feedback-driven debugging is not implemented end-to-end because SDK feedback ingestion is deferred. An external agent can inspect saved artifacts/logs, modify source and run the build/inspect recipe, but this is not claimed as an automated feedback pipeline.
- Exploratory testing can submit bounded explicit steps selected by an agent using observe results. There is no unbounded built-in autonomous agent loop; each batch needs a stop condition and action budget.

Set `REMOTE_IOS_LOG_LEVEL=INFO` for structured operation start/completion/failure events on stderr. Events omit operation arguments and input text. CLI JSON and MCP stdio stay on stdout. Captures and workflow reports carry session IDs for correlation.
