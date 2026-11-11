"""Create a reproducible manifest for a fully scored bonus evaluation."""
import argparse
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FROZEN = [
    'providers.py', 'run.py', 'status_tools.py', 'evals/run_evals.py',
    'evals/cases.json', 'evals/scenarios.py', 'evals/grading.py',
    'bonus/tools.py', 'bonus/cases.json', 'RUBRIC.md',
]
ARTIFACTS = {
    'eval_before.json', 'eval_after.json', 'eval_bonus.json',
    'eval_manifest_before.json', 'eval_manifest_after.json',
    'eval_manifest_bonus.json', 'eval_results_e2.json',
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, stderr=subprocess.PIPE).strip()


def normalized_hash(data):
    data = data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    return hashlib.sha256(data).hexdigest()


def tracked_paths(commit):
    return set(git('ls-tree', '-r', '--name-only', commit).splitlines())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--eval-file', default='eval_bonus.json')
    parser.add_argument('--output', default='eval_manifest_bonus.json')
    args = parser.parse_args()
    report = json.loads((ROOT / args.eval_file).read_text(encoding='utf-8'))
    summary = report.get('summary', {})
    if summary.get('total_cases') != 10 or summary.get('scored_cases') != 10 or summary.get('unscored_cases') != 0 or summary.get('score_0_100') is None:
        raise SystemExit('Refusing to manifest an incomplete or unscored bonus evaluation.')

    commit = git('rev-parse', 'HEAD')
    paths = tracked_paths(commit)
    frozen_paths = FROZEN + sorted(p for p in paths if p.startswith(('fixtures/', 'bonus/fixtures/')) and p.endswith('.json'))
    test_paths = sorted(p for p in paths if (p.startswith('tests/') or p.startswith('bonus/')) and p.endswith('.py') and ('test' in Path(p).name))
    status_lines = git('status', '--porcelain=v1', '--untracked-files=all').splitlines()
    unexpected = []
    for line in status_lines:
        state, path = line[:2], line[3:]
        if state != '??' or (path not in ARTIFACTS and not path.startswith('eval_results_repeat_')):
            unexpected.append(path)
    if unexpected:
        raise SystemExit('Refusing manifest because the source tree has non-artifact changes: ' + ', '.join(unexpected))

    eval_path = ROOT / args.eval_file
    run_time = datetime.datetime.fromtimestamp(eval_path.stat().st_mtime, datetime.timezone.utc).isoformat()
    manifest = {
        'version': 1,
        'evaluation': 'bonus',
        'eval_file': args.eval_file,
        'eval_file_sha256': hashlib.sha256(eval_path.read_bytes()).hexdigest(),
        'run_timestamp_utc_from_file_mtime': run_time,
        'manifest_generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'git': {
            'tag': None,
            'full_sha': commit,
            'tracked_tree_clean_at_run': True,
            'tree_dirty': False,
            'allowed_untracked_artifacts': [line[3:] for line in status_lines],
        },
        'python_version': subprocess.check_output([r'C:\Users\qvinh\AppData\Local\Python\bin\python.exe', '--version'], text=True).strip(),
        'config': {
            'provider': report['config']['provider'],
            'model': report['config']['model'],
            'judge_provider': report['config']['judge_provider'],
            'judge_model': report['config']['judge_model'],
            'max_steps': report['config']['max_steps'],
            'workers': 1,
            'mode': 'snapshot',
            'dataset': 'bonus',
        },
        'checksums': {
            'normalization': 'CRLF and CR normalized to LF before SHA-256',
            'agent_py_sha256': normalized_hash(subprocess.check_output(['git', 'show', f'{commit}:agent.py'], cwd=ROOT)),
            'frozen_files_sha256_normalized_lf': {p: normalized_hash(subprocess.check_output(['git', 'show', f'{commit}:{p}'], cwd=ROOT)) for p in frozen_paths},
            'tests_sha256_normalized_lf': {p: normalized_hash(subprocess.check_output(['git', 'show', f'{commit}:{p}'], cwd=ROOT)) for p in test_paths},
        },
        'summary': summary,
    }
    (ROOT / args.output).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Wrote {args.output}; score={summary['score_0_100']}; commit={commit}")


if __name__ == '__main__':
    main()
