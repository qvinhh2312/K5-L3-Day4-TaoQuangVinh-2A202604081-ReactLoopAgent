"""Validate the committed core before/after eval pair and print a case table."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_KEYS = ('provider', 'model', 'judge_provider', 'judge_model', 'max_steps', 'dataset')
ALLOWED_DIFF = {'agent.py', 'tests/test_robustness.py'}
PROMPT_CHANGE = (
    'get_status chỉ tìm trong 50 incident gần nhất và chỉ trả tối đa 5 kết quả; đây không phải\n'
    'lịch sử đầy đủ. Nếu người dùng yêu cầu mọi incident trong một khoảng thời gian hoặc danh sách\n'
    'đầy đủ, hãy nói rõ snapshot không đủ để xác minh tính đầy đủ. Không suy ra rằng không có\n'
    'incident trong một giai đoạn chỉ vì tìm kiếm không trả kết quả phù hợp.\n'
)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, stderr=subprocess.PIPE).strip()


def load(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def check(condition, message, errors):
    if not condition:
        errors.append(message)


def main():
    errors = []
    before, after = load('eval_before.json'), load('eval_after.json')
    mb, ma = load('eval_manifest_before.json'), load('eval_manifest_after.json')
    before_sha, after_sha = git('rev-parse', 'eval-before^{}'), git('rev-parse', 'eval-after^{}')
    check(before_sha != after_sha, 'eval-before and eval-after point to the same commit', errors)
    check(before['config'] == after['config'], 'Eval configurations differ', errors)
    check(all(before['config'].get(k) == mb['config'].get(k) == ma['config'].get(k)
              for k in CONFIG_KEYS), 'Manifest configuration does not match eval files', errors)

    cases_before, cases_after = before.get('cases', []), after.get('cases', [])
    ids_before = [c.get('id') for c in cases_before]
    ids_after = [c.get('id') for c in cases_after]
    check(len(ids_before) == len(set(ids_before)) == 22, 'Before must contain 22 unique cases', errors)
    check(len(ids_after) == len(set(ids_after)) == 22, 'After must contain 22 unique cases', errors)
    left = {c['id']: c for c in cases_before}
    right = {c['id']: c for c in cases_after}
    check(set(left) == set(right), 'Case IDs differ between eval files', errors)
    if set(left) == set(right):
        check(all((left[i].get('question'), left[i].get('expected'), left[i].get('scenario')) ==
                  (right[i].get('question'), right[i].get('expected'), right[i].get('scenario'))
                  for i in left), 'Question, expected, or scenario changed', errors)

    for label, report in (('before', before), ('after', after)):
        scores = [c.get('grade', {}).get('score') for c in report.get('cases', [])]
        check(all(type(s) is int for s in scores), f'{label} has unscored cases', errors)
        summary = report.get('summary', {})
        check(summary.get('scored_cases') == 22 and summary.get('unscored_cases') == 0,
              f'{label} summary is incomplete', errors)
        if scores and all(type(s) is int for s in scores):
            check(summary.get('score_0_100') == round(sum(scores) / len(scores), 2),
                  f'{label} summary does not match case mean', errors)

    check(mb['checksums']['frozen_files_sha256_normalized_lf'] ==
          ma['checksums']['frozen_files_sha256_normalized_lf'], 'Frozen file hashes differ', errors)
    check(mb['checksums']['preexisting_tests_sha256_normalized_lf'] ==
          ma['checksums']['preexisting_tests_sha256_normalized_lf'], 'Existing test hashes differ', errors)
    diff = set(git('diff', '--name-only', 'eval-before..eval-after').splitlines())
    check(diff == ALLOWED_DIFF, f'Unexpected tag diff: {sorted(diff)}', errors)
    old_agent = git('show', 'eval-before:agent.py')
    new_agent = git('show', 'eval-after:agent.py')
    check(new_agent.replace(PROMPT_CHANGE, '') == old_agent,
          'agent.py has changes beyond the selected prompt addition', errors)

    if errors:
        print('INVALID COMPARISON')
        for error in errors:
            print('-', error)
        return 1

    print(f"Validated {len(left)} cases; score {before['summary']['score_0_100']} -> "
          f"{after['summary']['score_0_100']} ({after['summary']['score_0_100']-before['summary']['score_0_100']:+.2f})")
    print('ID   BEFORE AFTER DELTA CLASS')
    improved = regressions = unchanged = 0
    for case_id in sorted(left):
        old = left[case_id]['grade']['score']
        new = right[case_id]['grade']['score']
        delta = new - old
        old_v = left[case_id]['grade'].get('mechanical', {}).get('violations', [])
        new_v = right[case_id]['grade'].get('mechanical', {}).get('violations', [])
        old_status = left[case_id]['result'].get('status')
        new_status = right[case_id]['result'].get('status')
        if delta <= -10 or (old_status == 'completed' and new_status != 'completed') or len(new_v) > len(old_v):
            category = 'REGRESSION'; regressions += 1
        elif delta >= 10 or len(new_v) < len(old_v):
            category = 'IMPROVED'; improved += 1
        else:
            category = 'UNCHANGED'; unchanged += 1
        print(f'{case_id:<4} {old:>6} {new:>5} {delta:>+6} {category}')
    print(f'Improved: {improved}; regressions: {regressions}; unchanged: {unchanged}')
    if mb['git'].get('tree_dirty_at_run'):
        print('Caveat: baseline manifest records that eval-before was run before its commit/tag was backfilled.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
