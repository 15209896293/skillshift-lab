import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/browser-r0-p3-student-proposal-decision-receipt-lost-2026-09-26')
records=[]; net=[]; dropped={'v':False}
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True)
 page=b.new_page(viewport={'width':390,'height':844})
 def handle(route):
  req=route.request
  if req.method=='POST' and '/proposed-actions/' in req.url and req.url.endswith('/decision'):
   phase='first' if not dropped['v'] else 'retry'
   response=route.fetch()
   records.append({'phase':phase,'status':response.status,'method':req.method,'url':req.url,'body':req.post_data,'idempotency_key':req.headers.get('idempotency-key'),'if_match':req.headers.get('if-match'),'receipt':response.text()})
   if not dropped['v']:
    dropped['v']=True
    route.abort('failed')
   else: route.fulfill(response=response)
  else: route.continue_()
 page.route('**/api/v1/demo/student/workspaces/*/proposed-actions/*/decision',handle)
 page.on('request',lambda req:net.append({'method':req.method,'url':req.url}))
 page.goto('http://127.0.0.1:8767/demo/student/',wait_until='domcontentloaded')
 page.wait_for_function("document.querySelectorAll('#task-picker option').length>=3")
 page.locator('#task-picker').select_option(index=1)
 page.wait_for_function("document.querySelector('#task-picker').value==='assignment-1' && !document.querySelector('#agent-input').disabled")
 page.locator('#agent-input').fill('请给出一个可以检查的金额核对建议。')
 page.locator('#send-agent').click()
 page.wait_for_function("document.querySelector('[data-action=show-diff]')!==null")
 page.locator('[data-action="show-diff"]').click()
 page.wait_for_function("!document.querySelector('#diff-card').hidden && document.querySelector('[data-action=reject]').disabled===false")
 before=page.locator('#code-editor').input_value()
 proposal_visible=page.locator('#diff-card').is_visible()
 page.locator('[data-action="reject"]').click()
 page.wait_for_function("document.querySelector('[data-action=reject]').disabled===false && document.querySelector('[data-action=accept]').disabled && document.querySelector('[data-action=takeover]').disabled && document.querySelector('#send-agent').disabled")
 unknown={'proposal_visible':proposal_visible,'proposal_status':page.locator('#proposal-status').inner_text(),'api_state':page.locator('#api-state').inner_text(),'decision_disabled':{x:page.locator(f'[data-action="{x}"]').is_disabled() for x in ['reject','accept','takeover']},'send_disabled':page.locator('#send-agent').is_disabled(),'pause_disabled':page.locator('#pause-task').is_disabled(),'submit_disabled':page.locator('[data-action="open-submit"]').is_disabled(),'editor_before':before,'editor_disabled':page.locator('#code-editor').is_disabled(),'selected_title':page.locator('#task-title').inner_text(),'viewport':page.evaluate('({w:innerWidth,cw:document.documentElement.clientWidth,sw:document.documentElement.scrollWidth})')}
 page.screenshot(path=str(out/'proposal-decision-unknown-390px.png'),full_page=True)
 b_option=page.locator('#task-picker option').nth(2).get_attribute('value')
 page.locator('#task-picker').select_option(b_option)
 page.locator('#pause-task').click()
 blocked={'selected_title':page.locator('#task-title').inner_text(),'picker_value':page.locator('#task-picker').input_value(),'api_state':page.locator('#api-state').inner_text(),'editor':page.locator('#code-editor').input_value(),'pause_button_disabled':page.locator('#pause-task').is_disabled(),'submission_dialog_open':page.locator('#submit-dialog').evaluate('(e)=>e.open')}
 # Attempt the disabled competing decision button; native disabled state should reject its click.
 page.locator('[data-action="takeover"]').evaluate('(e)=>e.click()')
 page.wait_for_timeout(100)
 page.locator('[data-action="reject"]').click()
 page.wait_for_function("!document.querySelector('#send-agent').disabled && document.querySelector('[data-action=reject]').disabled")
 workspace_id=re.search(r'/workspaces/([^/]+)/proposed-actions/',records[0]['url']).group(1)
 proposal_id=re.search(r'/proposed-actions/([^/]+)/decision',records[0]['url']).group(1)
 events=page.evaluate("async(id)=>{let r=await fetch('/api/v1/demo/student/workspaces/'+id+'/events?after_sequence=0&limit=50');return await r.json()}",workspace_id)
 proposal_events=[e for e in events.get('data',{}).get('events',[]) if e.get('event_type')=='agent.proposed_action_decided' and e.get('resource_ref')==proposal_id]
 after=page.locator('#code-editor').input_value()
 workspace=page.evaluate("async(id)=>{let r=await fetch('/api/v1/demo/student/workspaces/'+id);return await r.json()}",workspace_id)
 data={'browser':'Edge via Playwright','viewport':'390x844','workspace_id':workspace_id,'proposal_id':proposal_id,'proposal_generation_status':page.locator('#proposal-status').inner_text(),'api_state_after_retry':page.locator('#api-state').inner_text(),'unknown_state':unknown,'while_unknown_switch_pause_and_submit_attempt':blocked,'decision_requests':records,'same_request':all(records[0][k]==records[1][k] for k in ('method','url','body','idempotency_key','if_match')),'same_decision_receipt':json.loads(records[0]['receipt'])['data']==json.loads(records[1]['receipt'])['data'],'decision_event_matches':proposal_events,'event_count_for_decision':len(proposal_events),'editor_after_retry':after,'workspace_state':workspace.get('data',{}).get('state'),'pause_POSTs':sum(1 for x in net if x['method']=='POST' and x['url'].endswith('/pause')),'submission_POSTs':sum(1 for x in net if x['method']=='POST' and '/submissions' in x['url']),'second_proposal_decision_attempts':sum(1 for x in net if x['method']=='POST' and '/proposed-actions/' in x['url'] and x['url'].endswith('/decision')),'viewport_final':page.evaluate('({w:innerWidth,cw:document.documentElement.clientWidth,sw:document.documentElement.scrollWidth})')}
 assert [x['status'] for x in records]==[200,200] and data['same_request'] and data['same_decision_receipt']
 assert unknown['proposal_visible']
 assert '仍未确认' in unknown['api_state'] and '刷新会丢失本页重试信息' in unknown['api_state']
 assert unknown['decision_disabled']=={'reject':False,'accept':True,'takeover':True}
 assert unknown['send_disabled'] and unknown['submit_disabled'] and unknown['editor_before']==after
 assert blocked['selected_title']==unknown['selected_title'] and blocked['picker_value'] and blocked['editor']==before
 assert data['pause_POSTs']==0 and data['submission_POSTs']==0 and data['second_proposal_decision_attempts']==2
 assert len(proposal_events)==1 and data['workspace_state']=='IN_PROGRESS'
 assert '状态未确认' not in data['api_state_after_retry'] and '已确认提案决定' in data['api_state_after_retry']
 assert data['viewport_final']['cw']==data['viewport_final']['sw']==390
 page.screenshot(path=str(out/'proposal-decision-retried-390px.png'),full_page=True)
 (out/'browser-run.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'unknown':unknown,'blocked':blocked,'requests':[{'phase':x['phase'],'status':x['status'],'url':x['url'],'idempotency_key':x['idempotency_key'],'if_match':x['if_match']} for x in records],'same_request':data['same_request'],'same_decision_receipt':data['same_decision_receipt'],'decision_event_matches':proposal_events,'editor_unchanged':before==after,'workspace_state':data['workspace_state'],'no_pause_or_submission':data['pause_POSTs']==data['submission_POSTs']==0,'width':data['viewport_final']},ensure_ascii=True,indent=2))
 b.close()
