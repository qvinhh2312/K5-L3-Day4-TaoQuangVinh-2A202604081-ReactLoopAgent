# Bonus implementation status

The optional bonus is implemented in a commit after the immutable core tag. `core-submission` still points to the evaluated core commit.

- Three consecutive 429 responses are allowed per `(tool_name, provider)` pair. The next model-requested call is blocked with a `tool_blocked` trace event and a tool observation that the provider status is unknown; the tool is not executed.
- The agent honors numeric `retry_after_seconds`, numeric `Retry-After`, and HTTP-date `Retry-After`, capped at 10 seconds. It waits only before a later tool execution requested by the model; it does not retry automatically.
- Pagination remains model-directed. Each page result returns to the model, which chooses whether to request the next offset.
- Core tests pass 46/46; bonus offline tests pass 7/7.

The 10-case LLM bonus evaluation and four core regression repeats are pending because the current agent process has no provider credentials. No `eval_bonus.json` or bonus manifest is claimed. `run_remaining_evals.ps1` runs A6/E3/E6/H2 against the `eval-after` worktree and then the 10-case bonus eval once `OPENROUTER_API_KEY` is present in the same PowerShell process. A fully scored bonus run automatically gets `eval_manifest_bonus.json` from `write_eval_manifest.py`.

After setting `PROVIDER`, `MODEL`, `JUDGE_PROVIDER`, `JUDGE_MODEL`, and the matching API key in PowerShell, run:

```powershell
$env:PYTHONUTF8 = "1"
$py = "C:\Users\qvinh\AppData\Local\Python\bin\python.exe"
& $py evals/run_evals.py --bonus --provider openrouter --model openai/gpt-4o-mini --judge-provider openrouter --judge-model openai/gpt-4o-mini --max-steps 16 --workers 1 --output eval_bonus.json
```
