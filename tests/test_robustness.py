"""Additional offline checks for error handling and trace integrity."""
import json
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent import SYSTEM_PROMPT, run_agent


class Provider:
    def __init__(self, responses=None, error=None):
        self.responses = iter(responses or [])
        self.error = error
        self.histories = []

    def complete(self, messages, schemas):
        self.histories.append(list(messages))
        if self.error:
            raise self.error
        return next(self.responses)


class Tools:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error
        self.schemas = []
        self.system_prompt = 'custom'

    def execute(self, name, args):
        if self.error:
            raise self.error
        if name != 'known':
            return {'ok': False, 'error': 'UNKNOWN_TOOL'}
        return self.result


def response(calls=None, content='done', finish='stop', usage=None):
    calls = calls or []
    message = {'role': 'assistant', 'content': content}
    if calls:
        message['tool_calls'] = [{'id': c['id'], 'type': 'function', 'function': {
            'name': c['name'], 'arguments': c['arguments']}} for c in calls]
    return {'message': message, 'calls': calls, 'finish': finish, 'usage': usage or {}}


def call(arguments, name='known', call_id='call-id'):
    return {'id': call_id, 'name': name, 'arguments': arguments}


class RobustnessTests(unittest.TestCase):
    def test_system_prompt_states_status_search_completeness_limit(self):
        self.assertIn('50 incident gần nhất', SYSTEM_PROMPT)
        self.assertIn('không đủ để xác minh tính đầy đủ', SYSTEM_PROMPT)

    def test_empty_and_non_object_arguments(self):
        for raw, expected_error in [('', None), (None, None), ('null', 'INVALID_ARGUMENTS'),
                                    ('[]', 'INVALID_ARGUMENTS'), ('"x"', 'INVALID_ARGUMENTS')]:
            with self.subTest(raw=raw):
                p = Provider([response([call(raw)]), response()])
                result = run_agent('q', p, Tools({'ok': True}))
                self.assertEqual(result['status'], 'completed')
                observation = json.loads(p.histories[1][-1]['content'])
                if expected_error:
                    self.assertEqual(observation['error'], expected_error)
                else:
                    self.assertEqual(observation, {'ok': True})

    def test_tool_exception_and_unknown_name_are_observations(self):
        for tool, args, error in [(Tools(error=KeyError('bad')), call('{}'), 'KeyError'),
                                  (Tools({'ok': True}), call('{}', name='missing'), 'UNKNOWN_TOOL')]:
            p = Provider([response([args]), response()])
            self.assertEqual(run_agent('q', p, tool)['status'], 'completed')
            observation = json.loads(p.histories[1][-1]['content'])
            self.assertEqual(observation['error'], error)

    def test_nonstandard_tool_values_are_json_safe(self):
        cycle = []
        cycle.append(cycle)
        p = Provider([response([call('{}')]), response()])
        result = run_agent('q', p, Tools({'ok': True, 'values': {1, 2}, 'nan': math.nan, 'cycle': cycle}))
        self.assertEqual(result['status'], 'completed')
        observed = json.loads(p.histories[1][-1]['content'])
        self.assertEqual(set(observed['values']), {1, 2})
        self.assertEqual(observed['nan'], 'nan')
        self.assertEqual(observed['cycle'], ['[circular reference]'])

    def test_provider_error_and_usage_count(self):
        failed = run_agent('q', Provider(error=RuntimeError('offline')), Tools())
        self.assertEqual(failed['status'], 'error')
        p = Provider([response(usage={'n': 1}), response(usage={'n': 2})])
        result = run_agent('q', p, Tools())
        self.assertEqual(len(result['usage']), len(p.histories))

    def test_anthropic_malformed_arguments_history_returns_agent_error(self):
        from providers import Provider as AnthropicAdapter

        class MalformedHistoryProvider:
            def __init__(self, adapter):
                self.adapter, self.first = adapter, True

            def complete(self, messages, schemas):
                if self.first:
                    self.first = False
                    return response([call('{', name='known')], finish='tool_calls')
                return self.adapter.complete(messages, schemas)

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            adapter = AnthropicAdapter('anthropic', 'test-model')
        result = run_agent('q', MalformedHistoryProvider(adapter), Tools({'ok': True}))
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['trace'][-1]['event'], 'provider_error')

    def test_source_gate_only_tracks_successful_incident_urls(self):
        p = Provider([response([call('{}', name='get_status')]), response()])
        self.assertEqual(run_agent('q', p, Tools({'source': 'https://status.test'}))['status'], 'completed')
        p = Provider([response([call('{}', name='get_incident_details')]), response()])
        result = run_agent('q', p, Tools({'ok': False, 'url': 'https://status.test'}))
        self.assertEqual(result['status'], 'completed')
        self.assertFalse(any(e['event'] == 'validation_missing_source' for e in result['trace']))

    def test_strict_source_gate_is_opt_in_and_reports_partial_sources(self):
        class MultiTools:
            def execute(self, name, args):
                return {'ok': True, 'provider': args['provider'],
                        'url': f"https://{args['provider']}.test/inc"}

        calls = [call('{"provider":"github"}', name='get_incident_details', call_id='g'),
                 call('{"provider":"npm"}', name='get_incident_details', call_id='n')]
        no_strict = Provider([response(calls), response(content='https://github.test/inc')])
        result = run_agent('q', no_strict, MultiTools())
        self.assertEqual(result['status'], 'completed')
        self.assertFalse(any(e['event'] == 'validation_partial_source' for e in result['trace']))

        strict = Provider([response(calls), response(content='https://github.test/inc'),
                           response(content='https://github.test/inc')])
        result = run_agent('q', strict, MultiTools(), strict_sources=True)
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(any(e['event'] == 'validation_partial_source' for e in result['trace']))

    def test_trace_keeps_call_id_and_compacts_large_result(self):
        long_id = 'id-' + 'x' * 500
        p = Provider([response([call('{}', call_id=long_id)]), response()])
        result = run_agent('q', p, Tools({'ok': True, 'provider': 'npm', 'url': 'https://x.test/i',
                                          'status': 'resolved', 'updates': ['x' * 30000]}))
        event = next(e for e in result['trace'] if e['event'] == 'tool')
        self.assertEqual(event['tool_call_id'], long_id)
        json.loads(event['result'])
        self.assertLess(len(json.dumps(result['trace'])), 24000)


if __name__ == '__main__':
    unittest.main()
