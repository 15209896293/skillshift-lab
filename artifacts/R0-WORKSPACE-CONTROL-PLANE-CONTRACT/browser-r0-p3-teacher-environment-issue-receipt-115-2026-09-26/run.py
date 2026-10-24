import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/browser-r0-p3-teacher-environment-issue-receipt-115-2026-09-26')
records=[]; net=[]; dropped={'v':False}
reason='The approved development environment was unavailable during this review.'
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True)
 page=b.new_page(viewport={'width':390,'height':844})
 def handle(route):
  req=route.request
  if req.method=='POST' and re.search(r'/api/v1/demo/teacher/submissions/[^/]+/review-actions$',req.url) and not dropped['v']:
   response=route.fetch()
   records.append({'status':response.status,'method':req.method,'url':req.url,'body':req.post_data,'idempotency_key':req.headers.get('idempotency-key'),'if_match':req.headers.get('if-match'),'receipt':response.text()})
   dropped['v']=True
   route.abort('failed')
  else: route.continue_()
 page.route('**/api/v1/demo/teacher/submissions/*/review-actions',handle)
 page.on('request',lambda req:net.append({'method':req.method,'url':req.url}))
 page.goto('http://127.0.0.1:8767/demo/teacher/',wait_until='domcontentloaded')
 page.locator('[data-view="reviews"]').click()
 page.wait_for_function("document.querySelectorAll('#review-task-list .review-task-choice').length===3")
 page.locator('#review-task-list .review-task-choice').filter(has_text='教师多任务队列隔离验证 A').locator('button').click()
 page.wait_for_function("!document.querySelector('#review-details').hidden && document.querySelector('#review-assignment-title').textContent.includes('A')")
 page.locator('#feedback-reason').fill(reason)
 page.locator('[data-review="environment"]').click()
 page.wait_for_function("document.querySelector('#remediation-status').innerText.includes('The approved development environment was unavailable during this review.')")
 teacher={'api_state':page.locator('#api-state').inner_text(),'remediation_status':page.locator('#remediation-status').inner_text(),'queue_rows':[x.inner_text() for x in page.locator('#review-task-list .review-task-choice').all()],'request_count':len(records),'viewport':page.evaluate('({w:innerWidth,cw:document.documentElement.clientWidth,sw:document.documentElement.scrollWidth})')}
 page.screenshot(path=str(out/'teacher-remediation-readback-confirmed-390px.png'),full_page=True)
 remediation=page.evaluate("async()=>{let r=await fetch('/api/v1/demo/teacher/workspaces/workspace-1/remediation');return await r.json()}")
 events=page.evaluate("async()=>{let r=await fetch('/api/v1/demo/teacher/workspaces/workspace-1/events?after_sequence=0&limit=50');return await r.json()}")
 history=page.evaluate("async()=>{let r=await fetch('/api/v1/demo/teacher/assignments/assignment-1/review-history?after_sequence=0&limit=50');return await r.json()}")
 action=json.loads(records[0]['receipt'])['data']['review_action']
 open_matches=[x for x in remediation.get('data',{}).get('remediations',[]) if x.get('state')=='OPEN' and x.get('submission_id')==action['submission_id'] and x.get('review_action_id')==action['id'] and x.get('requested_action')==action['kind'] and x.get('reason')==reason]
 event_matches=[x for x in events.get('data',{}).get('events',[]) if x.get('event_type')=='review.action_recorded' and x.get('resource_ref')==action['id']]
 action_matches=[x for x in history.get('data',{}).get('review_actions',[]) if x.get('id')==action['id']]
 student=page
 student.goto('http://127.0.0.1:8767/demo/student/',wait_until='domcontentloaded')
 student.wait_for_function("document.querySelectorAll('#task-picker option').length>=3")
 student.locator('#task-picker').select_option(index=1)
 student.wait_for_function("document.querySelector('#remediation-state').dataset.readState==='confirmed'",timeout=15000)
 wire=student.evaluate("async()=>{let r=await fetch('/api/v1/demo/teacher/workspaces/workspace-1');return await r.json()}")
 student_view={'wire_state':wire.get('data',{}).get('state'),'selected_title':student.locator('#task-title').inner_text(),'workspace_state':student.locator('#task-picker-state').inner_text(),'remediation_state':student.locator('#remediation-state').inner_text(),'viewport':student.evaluate('({w:innerWidth,cw:document.documentElement.clientWidth,sw:document.documentElement.scrollWidth})')}
 student.screenshot(path=str(out/'student-remediation-received-390px.png'),full_page=True)
 post_index=next(i for i,x in enumerate(net) if x['method']=='POST' and '/review-actions' in x['url'])
 post_followups=net[post_index+1:]
 data={'browser':'Edge via Playwright','requests_after_lost_write':post_followups,'viewport':'390x844','lost_response_request':records,'teacher_after_readback':teacher,'matching_open_remediations':open_matches,'matching_review_actions':action_matches,'matching_review_events':event_matches,'student_after_explicit_A_selection':student_view,'observed_semantics':'ENVIRONMENT_ISSUE is currently read back as an OPEN remediation and shown in the student UI as FEEDBACK_REQUIRED; this records current code behavior, not accepted product meaning.'}
 assert len(records)==1 and records[0]['status']==201
 assert action['kind']=='ENVIRONMENT_ISSUE' and len(open_matches)==1 and open_matches[0]['requested_action']=='ENVIRONMENT_ISSUE'
 assert teacher['request_count']==1 and sum(1 for x in net if x['method']=='POST' and '/review-actions' in x['url'])==1
 assert any(x['method']=='GET' and '/workspaces/workspace-1' in x['url'] and not x['url'].endswith('/remediation') for x in post_followups)
 assert any(x['method']=='GET' and x['url'].endswith('/workspaces/workspace-1/remediation') for x in post_followups)
 assert '请求补正' in teacher['remediation_status'] and reason in teacher['remediation_status']
 assert any('教师多任务队列隔离验证 A' in x and '待复核 0 项' in x for x in teacher['queue_rows'])
 assert len(open_matches)==1 and len(action_matches)==1 and len(event_matches)==1
 assert student_view['wire_state']=='FEEDBACK_REQUIRED' and '等待你补正' in student_view['workspace_state'] and reason in student_view['remediation_state']
 assert teacher['viewport']['cw']==teacher['viewport']['sw']==student_view['viewport']['cw']==student_view['viewport']['sw']==390
 (out/'browser-run.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'teacher':teacher,'matching_open_remediations':len(open_matches),'matching_review_actions':len(action_matches),'matching_review_events':len(event_matches),'student':student_view},ensure_ascii=True,indent=2))
 b.close()
