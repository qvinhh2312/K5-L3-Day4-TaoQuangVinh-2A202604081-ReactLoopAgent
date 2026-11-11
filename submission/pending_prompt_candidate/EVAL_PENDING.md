# Pending evaluation: scope and unsupported-provider guidance

This source adds two prompt rules after the complete evaluation in `../final_candidate/`:

1. For a request limited to current overall status, return the requested provider's indicator, description, snapshot time, and source; omit incident history unless requested.
2. If the requested provider has no matching tool, say status and incident URL cannot be verified. Do not substitute unrelated providers or invent links.

These rules target B7 (45) and B9 (30). This source has not been evaluated; the 87.95 core and 76.5 bonus scores belong to the preceding source commit `16290ee`.

Run in PowerShell after setting `OPENROUTER_API_KEY` in the current process. Do not paste the key into chat:

```powershell
$env:PYTHONUTF8 = "1"
& "C:\Users\qvinh\AppData\Local\Python\bin\python.exe" evals/run_evals.py --provider openrouter --model openai/gpt-4o-mini --judge-provider openrouter --judge-model openai/gpt-4o-mini --max-steps 8 --workers 1 --output eval_next_prompt.json
& "C:\Users\qvinh\AppData\Local\Python\bin\python.exe" evals/run_evals.py --bonus --provider openrouter --model openai/gpt-4o-mini --judge-provider openrouter --judge-model openai/gpt-4o-mini --max-steps 16 --workers 1 --output eval_bonus_next_prompt.json
```

Student: Tao Quang Vinh · 2A202604081 · L3B. Target repo: `K5-L3B-DAY04-TaoQuangVinh-2A202604081-ReactLoopAgent`.
