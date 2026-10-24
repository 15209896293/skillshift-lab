import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/browser-r0-p3-teacher-ack-receipt-lost-2026-09-26')
records=[]; dropped={'v':False}
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True)
 page=b.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
 def route_handler(route):
  req=route.request
  if req.method=='POST' and re.search(r'/api/v1/demo/teacher/submissions/[^/]+/review-actions$',req.url):
   phase='first' if not dropped['v'] else 'retry'
   response=route.fetch()
   rec={'phase':phase,'status':response.status,'method':req.method,'url':req.url,'post_data':req.post_data,'idempotency_key':req.headers.get('idempotency-key'),'if_match':req.headers.get('if-match'),'response_body':response.text()}
   records.append(rec)
   if not dropped['v']:
    dropped['v']=True
    route.abort('failed')
   else: route.fulfill(response=response)
  else: route.continue_()
 page.route('**/api/v1/demo/teacher/submissions/*/review-actions',route_handler)
 page.goto('http://127.0.0.1:8767/demo/teacher/',wait_until='domcontentloaded')
 page.locator('[data-view="reviews"]').click()
 page.wait_for_function("document.querySelectorAll('#review-task-list .review-task-choice').length===3")
 rows=page.locator('#review-task-list .review-task-choice')
 row_a=rows.filter(has_text='教师多任务队列隔离验证 A')
 row_a.locator('button').click()
 page.wait_for_function("document.querySelector('#review-assignment-title').textContent.includes('A') && !document.querySelector('#review-details').hidden")
 initial_title=page.locator('#review-assignment-title').inner_text()
 initial_submission=page.locator('#review-submission-state').inner_text()
 page.locator('#feedback-reason').fill('Synthetic ACK review reason for task A evidence.')
 page.locator('[data-review="approve"]').click()
 page.wait_for_function("!document.querySelector('#review-result').hidden && document.querySelector('[data-review=approve]').disabled===false && document.querySelector('#feedback-reason').disabled")
 unknown={'text':page.locator('#review-result').inner_text(),'assignment_title':page.locator('#review-assignment-title').inner_text(),'submission_state':page.locator('#review-submission-state').inner_text(),'reason_disabled':page.locator('#feedback-reason').is_disabled(),'approve_disabled':page.locator('[data-review="approve"]').is_disabled(),'other_actions_disabled':[page.locator(f'[data-review="{x}"]').is_disabled() for x in ['explanation','evidence','remediation','environment']],'tabs_disabled':[x.is_disabled() for x in page.locator('.submission-tab').all()],'viewport':page.evaluate('({w:innerWidth,cw:document.documentElement.clientWidth,sw:document.documentElement.scrollWidth})')}
 page.screenshot(path=str(out/'ack-unknown-A-390px.png'),full_page=True)
 page.locator('#review-task-list .review-task-choice').filter(has_text='教师多任务队列隔离验证 B').locator('button').click()
 page.wait_for_timeout(250)
 after_attempted_switch={'title':page.locator('#review-assignment-title').inner_text(),'result':page.locator('#review-result').inner_text(),'api_state':page.locator('#api-state').inner_text(),'reason_disabled':page.locator('#feedback-reason').is_disabled()}
 page.screenshot(path=str(out/'ack-unknown-after-B-selection-390px.png'),full_page=True)
 page.locator('[data-review="approve"]').click()
 page.wait_for_function("[...document.querySelectorAll('#review-task-list .review-task-choice')].some(r=>r.innerText.includes('教师多任务队列隔离验证 A') && r.innerText.includes('待复核 0 项'))")
 
 aid=json.loads(records[0]['response_body'])['data']['review_action']['id']
 submission_id=json.loads(records[0]['response_body'])['data']['review_action']['submission_id']
 # Read back the task-specific review history and event stream.
 hist=page.evaluate("async()=>{let r=await fetch('/api/v1/demo/teacher/assignments/assignment-1/review-history?after_sequence=0&limit=50');return await r.json()}")
 history_items=hist.get('data',{}).get('review_actions',[])
 action_items=[x for x in history_items if x.get('id')==aid]
 queues=[x.inner_text() for x in page.locator('#review-task-list .review-task-choice').all()]
 events=page.evaluate("async()=>{let r=await fetch('/api/v1/demo/teacher/workspaces/workspace-1/events?after_sequence=0&limit=50');return await r.json()}")
 created_events=[x for x in events.get('data',{}).get('events',[]) if x.get('event_type')=='review.action_recorded']
 data={'browser':'Edge via Playwright','viewport':'390x844','initial_A_title':initial_title,'initial_A_submission_state':initial_submission,'unknown_state':unknown,'after_attempted_B_selection':after_attempted_switch,'requests':records,'same_request':all(records[0][k]==records[1][k] for k in ('method','url','post_data','idempotency_key','if_match')),'same_review_action_id':json.loads(records[0]['response_body'])['data']['review_action']['id']==json.loads(records[1]['response_body'])['data']['review_action']['id'],'queues_after_retry':queues,'aggregate_review_count':page.locator('#review-count').inner_text(),'review_history_count_for_ack':len(action_items),'review_action_created_events':created_events,'review_history_action':action_items[0] if action_items else None,'viewport_after':page.evaluate('({w:innerWidth,cw:document.documentElement.clientWidth,sw:document.documentElement.scrollWidth})')}
 assert records[0]['status']==201 and records[1]['status']==201
 assert all(records[0][k]==records[1][k] for k in ('method','url','post_data','idempotency_key','if_match'))
 assert json.loads(records[0]['response_body'])['data']['review_action']['id']==json.loads(records[1]['response_body'])['data']['review_action']['id']
 assert after_attempted_switch['title']==initial_title and after_attempted_switch['reason_disabled'] and 'DTO' in after_attempted_switch['api_state']
 assert len(action_items)==1 and action_items[0]['id']==aid and action_items[0]['submission_id']==submission_id
 assert len(created_events)==1 and created_events[0]['resource_ref']==aid
 assert any('教师多任务队列隔离验证 A' in x and '待复核 0 项' in x for x in queues)
 assert any('教师多任务队列隔离验证 B' in x and '待复核 1 项' in x for x in queues)
 assert data['viewport_after']['cw']==data['viewport_after']['sw']==390
 page.screenshot(path=str(out/'ack-retry-queues-history-390px.png'),full_page=True)
 (out/'browser-run.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in data.items() if k not in ('requests','review_history_action')},ensure_ascii=True,indent=2))
 b.close()
