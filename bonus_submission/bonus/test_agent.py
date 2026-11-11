"""Kiểm tra agent với tools bonus mà không gọi LLM API."""
import json
import sys
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from agent import run_agent
from bonus.tools import BonusTools


def call(call_id,name,args):
    raw=json.dumps(args)
    c={'id':call_id,'name':name,'arguments':raw}
    m={'role':'assistant','content':None,'tool_calls':[{'id':call_id,'type':'function','function':{'name':name,'arguments':raw}}]}
    return {'message':m,'calls':[c],'finish':'tool_calls','usage':{}}

def final(answer='Đã kiểm tra'):
    return {'message':{'role':'assistant','content':answer},'calls':[],'finish':'stop','usage':{}}


class ScriptedProvider:
    def __init__(self,responses): self.responses=iter(responses); self.histories=[]; self.schemas=[]
    def complete(self,messages,schemas):
        self.histories.append(list(messages));self.schemas.append(schemas)
        return next(self.responses)


class BonusAgentTests(unittest.TestCase):
    def test_bonus_schemas_and_system_prompt(self):
        t=BonusTools();p=ScriptedProvider([final()])
        self.assertEqual(run_agent('Kiểm tra',p,t)['status'],'completed')
        names={x['function']['name'] for x in p.schemas[0]}
        self.assertTrue({'get_github_status','get_cloudflare_status','get_vercel_status','get_npm_status','get_digitalocean_status'}.issubset(names))
        self.assertIn('DigitalOcean',p.histories[0][0]['content'])
    def test_429_observation_returns_to_model(self):
        t=BonusTools(scenario='rate_limit_once')
        p=ScriptedProvider([call('a','get_vercel_status',{}),call('b','get_vercel_status',{}),final()])
        result=run_agent('Kiểm tra',p,t,max_steps=5)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(json.loads(p.histories[1][-1]['content'])['error'],'RATE_LIMITED')
        self.assertEqual(json.loads(p.histories[2][-1]['content'])['provider'],'vercel')
    def test_invalid_arguments_observation_returns_to_model(self):
        t=BonusTools()
        bad={'provider':'npm','incident_id':'cc0t2r4403sy','offset':'zero'}
        good={'provider':'npm','incident_id':'cc0t2r4403sy','offset':0}
        details=t.execute('get_incident_details',good)
        p=ScriptedProvider([call('a','get_incident_details',bad),call('b','get_incident_details',good),final('Nguồn: '+details['url'])])
        result=run_agent('Kiểm tra',p,t,max_steps=5)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(json.loads(p.histories[1][-1]['content'])['error'],'INVALID_ARGUMENTS')
        self.assertTrue(json.loads(p.histories[2][-1]['content'])['ok'])

    def test_persistent_429_is_capped_and_reported_as_unknown(self):
        tools=BonusTools(scenario='rate_limit_always')
        p=ScriptedProvider([call(str(i),'get_vercel_status',{}) for i in range(4)]+[final()])
        result=run_agent('Kiểm tra Vercel',p,tools,max_steps=6)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(tools.calls[('get_vercel_status','vercel')],3)
        self.assertEqual(sum(e['event']=='tool' and e['name']=='get_vercel_status' for e in result['trace']),3)
        blocked=[e for e in result['trace'] if e['event']=='tool_blocked']
        self.assertEqual(len(blocked),1)
        self.assertEqual(blocked[0]['tool_call_id'],'3')
        observation=json.loads(p.histories[4][-1]['content'])
        self.assertIn('unknown',observation['message'])

    def test_retry_after_seconds_and_http_date_wait_are_capped(self):
        class RetryTools:
            schemas=[]
            system_prompt='retry-test'
            def __init__(self, retry_fields): self.results=iter([
                {'ok':False,'error':'RATE_LIMITED',**retry_fields},
                {'ok':True,'provider':'vercel','source':'https://vercel.test'}])
            def execute(self,name,args): return next(self.results)

        retry_values=({'retry_after_seconds':5},
                      {'retry_after':format_datetime(datetime.now(timezone.utc)+timedelta(seconds=60), usegmt=True)})
        for retry_fields in retry_values:
            with self.subTest(retry_fields=retry_fields), patch('agent.time.sleep') as sleeper:
                p=ScriptedProvider([call('a','get_vercel_status',{}),call('b','get_vercel_status',{}),final()])
                result=run_agent('Kiểm tra',p,RetryTools(retry_fields),max_steps=4)
                self.assertEqual(result['status'],'completed')
                sleeper.assert_called_once()
                self.assertGreater(sleeper.call_args.args[0],0)
                self.assertLessEqual(sleeper.call_args.args[0],10)

    def test_rate_limit_budget_is_per_tool_provider_pair(self):
        class PairTools:
            schemas=[]
            system_prompt='pair-test'
            def __init__(self): self.calls=[]
            def execute(self,name,args):
                self.calls.append(name)
                if name=='get_vercel_status':
                    return {'ok':False,'error':'RATE_LIMITED','retry_after_seconds':0}
                return {'ok':True,'provider':'npm'}

        tools=PairTools()
        calls=[call(str(i),'get_vercel_status',{}) for i in range(3)]
        calls += [call('npm','get_npm_status',{}),call('blocked','get_vercel_status',{})]
        p=ScriptedProvider(calls+[final()])
        result=run_agent('Kiểm tra Vercel và npm',p,tools,max_steps=6)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(tools.calls,['get_vercel_status']*3+['get_npm_status'])
        self.assertEqual(sum(e['event']=='tool_blocked' for e in result['trace']),1)

    def test_model_controls_pagination_across_separate_steps(self):
        tools=BonusTools()
        first=tools.execute('get_incident_details',{'provider':'vercel','incident_id':'sps6n39gm4sg','offset':0})
        second=tools.execute('get_incident_details',{'provider':'vercel','incident_id':'sps6n39gm4sg','offset':2})
        p=ScriptedProvider([
            call('page-1','get_incident_details',{'provider':'vercel','incident_id':'sps6n39gm4sg','offset':0}),
            call('page-2','get_incident_details',{'provider':'vercel','incident_id':'sps6n39gm4sg','offset':2}),
            final('Incident lịch sử. Nguồn: '+second['url'])])
        result=run_agent('Tìm update ở trang sau',p,tools,max_steps=4)
        events=[e for e in result['trace'] if e['event']=='tool' and e['name']=='get_incident_details']
        self.assertEqual([e['step'] for e in events],[1,2])
        self.assertEqual(events[1]['arguments']['offset'],2)
        self.assertEqual(result['status'],'completed')
        self.assertIsNotNone(first['next_offset'])

if __name__=='__main__': unittest.main()
