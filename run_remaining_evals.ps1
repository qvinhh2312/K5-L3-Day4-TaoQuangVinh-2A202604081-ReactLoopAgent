$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$root = $PSScriptRoot
$python = 'C:\Users\qvinh\AppData\Local\Python\bin\python.exe'
$worktree = Join-Path $root '.eval-after-repeat-worktree'
$apiKey = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'Process')
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw 'Set OPENROUTER_API_KEY in this PowerShell process, then rerun this script. The key is not read from .env or printed.'
}
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python executable not found: $python"
}
if (Test-Path -LiteralPath $worktree) {
    throw "Worktree path already exists; inspect it before continuing: $worktree"
}

$env:PYTHONUTF8 = '1'
$env:PROVIDER = 'openrouter'
$env:MODEL = 'openai/gpt-4o-mini'
$env:JUDGE_PROVIDER = 'openrouter'
$env:JUDGE_MODEL = 'openai/gpt-4o-mini'

$caseFailures = [System.Collections.Generic.List[string]]::new()
$worktreeAdded = $false
try {
    git -C $root worktree add --detach $worktree 'eval-after'
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the eval-after worktree.' }
    $worktreeAdded = $true
    Push-Location $worktree
    foreach ($caseId in @('A6', 'E3', 'E6', 'H2')) {
        $output = Join-Path $root "eval_results_repeat_$caseId.json"
        & $python evals/run_evals.py --provider openrouter --model openai/gpt-4o-mini `
            --judge-provider openrouter --judge-model openai/gpt-4o-mini `
            --case $caseId --max-steps 8 --workers 1 --output $output
        if ($LASTEXITCODE -ne 0) { $caseFailures.Add($caseId) }
    }
}
finally {
    if ((Get-Location).Path -eq $worktree) { Pop-Location }
    if ($worktreeAdded) {
        git -C $root worktree remove --force $worktree
        if ($LASTEXITCODE -ne 0) { Write-Warning 'Could not remove the temporary worktree; inspect it before deleting.' }
    }
}

$bonusOutput = Join-Path $root 'eval_bonus.json'
& $python evals/run_evals.py --bonus --provider openrouter --model openai/gpt-4o-mini `
    --judge-provider openrouter --judge-model openai/gpt-4o-mini `
    --max-steps 16 --workers 1 --output $bonusOutput
$bonusExit = $LASTEXITCODE

if ($caseFailures.Count -gt 0) {
    Write-Error "These repeat evaluations did not complete with a score: $($caseFailures -join ', ')"
}
if ($bonusExit -ne 0) {
    Write-Error 'Bonus evaluation did not produce a fully scored result; inspect eval_bonus.json.'
}
if ($caseFailures.Count -eq 0 -and $bonusExit -eq 0) {
    Write-Output 'Repeat evaluations and the full bonus evaluation completed.'
}
