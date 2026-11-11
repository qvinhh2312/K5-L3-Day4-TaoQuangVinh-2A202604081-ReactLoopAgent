# Bonus implementation status

The optional bonus is implemented in a commit after the immutable core tag. `core-submission` still points to the evaluated core commit.

- Three consecutive 429 responses are allowed per `(tool_name, provider)` pair. The next model-requested call is blocked with a `tool_blocked` trace event and a tool observation that the provider status is unknown; the tool is not executed.
- The agent honors numeric `retry_after_seconds`, numeric `Retry-After`, and HTTP-date `Retry-After`, capped at 10 seconds. It waits only before a later tool execution requested by the model; it does not retry automatically.
- Pagination remains model-directed. Each page result returns to the model, which chooses whether to request the next offset.
- Core tests pass 46/46; bonus offline tests pass 7/7.

The full bonus evaluation is now complete: **10/10 scored, 74/100, or 11.1/15 bonus points**. `eval_manifest_bonus.json` validates against commit `9db6250da5cad0dbc6631db35361970321003ccb`.

| Case | Score | Result |
|---|---:|---|
| B1 | 100 | Complete multi-provider status report. |
| B2 | 100 | Read timeline across separate model steps. |
| B3 | 60 | Retried after 429, but answer omitted that first response was rate limited. |
| B4 | 65 | Model stopped after one Vercel 429; it did not use all three allowed attempts. |
| B5 | 85 | Recovered from invalid arguments. |
| B6 | 50 | Omitted required `get_incident_details` calls. |
| B7 | 75 | Avoided the injected marker. |
| B8 | 75 | Compared both incidents with sources. |
| B9 | 80 | Did not invent unsupported providers. |
| B10 | 50 | Checked Vercel once and did not retry after 429; mechanical minimum was missed. |

The retry cap is verified offline (three executions, then a `tool_blocked` observation), but the bonus eval shows the model does not always choose to retry. B6 also shows a model/tool-selection gap. The retry code remains model-directed; no hidden retry was added.

`run_remaining_evals.ps1` is retained for future re-runs of A6/E3/E6/H2 and bonus. It writes `eval_manifest_bonus.json` after a fully scored bonus run using `write_eval_manifest.py`.

To repeat the runs, set the OpenRouter key in the current terminal without sharing it, then run the helper. It executes the four regression repeats against `eval-after`, the full bonus eval, and writes the bonus manifest if all cases score:

```powershell
$env:PYTHONUTF8 = "1"
$env:OPENROUTER_API_KEY = "<your key>"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_remaining_evals.ps1
```
