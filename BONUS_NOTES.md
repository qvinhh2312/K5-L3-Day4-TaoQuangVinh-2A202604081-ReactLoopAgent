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

After this run, the system prompt was extended to tell the model to retry on an explicit request, disclose an earlier 429 even after recovery, and inspect details for the newest relevant incident. A full candidate run then scored **73.7/100 (11.05/15), 10/10 cases**, using the same provider/model/judge and 16-step limit.

| Case | Previous | Candidate | Change | Observation |
|---|---:|---:|---:|---|
| B1 | 100 | 75 | -25 | Lower judge score despite all five status tools being called. |
| B2 | 100 | 80 | -20 | Pagination calls completed; judge score fell. |
| B3 | 60 | 67 | +7 | Still omitted the first 429 and retry from the final answer. |
| B4 | 65 | 80 | +15 | Answer correctly said Vercel status was unknown after 429; no second Vercel call. |
| B5 | 85 | 80 | -5 | Recovered from invalid arguments, but score fell slightly. |
| B6 | 50 | 50 | 0 | Still omitted required `get_incident_details`; mechanical cap remains. |
| B7 | 75 | 100 | +25 | Full score. |
| B8 | 75 | 80 | +5 | Slight improvement. |
| B9 | 80 | 75 | -5 | Slight regression. |
| B10 | 50 | 50 | 0 | Still made only one Vercel call after 429; mechanical cap remains. |

Overall bonus moved from **74.0 to 73.7** (11.10 to 11.05 points). The prompt improved B3/B4/B7/B8, but did not make the model follow the required detail lookup in B6 or second Vercel call in B10; it also reduced B1/B2. The candidate evaluation is saved as `eval_bonus_candidate.json`. Do not replace the previous bonus report or its manifest: they document a different source commit.

The current working agent loop now sends the model a trace-based follow-up when an explicit retry request is still pending or when the requested latest/linked incident has not yet been inspected. This is a new, unevaluated change intended to address B3/B4/B6/B10. The 73.7 result above predates it. A fresh full bonus run is still required.

`run_remaining_evals.ps1` is retained for future re-runs of A6/E3/E6/H2 and bonus. It writes `eval_manifest_bonus.json` after a fully scored bonus run using `write_eval_manifest.py`.

To repeat the runs, set the OpenRouter key in the current terminal without sharing it, then run the helper. It executes the four regression repeats against `eval-after`, the full bonus eval, and writes the bonus manifest if all cases score:

```powershell
$env:PYTHONUTF8 = "1"
$env:OPENROUTER_API_KEY = "<your key>"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_remaining_evals.ps1
```
