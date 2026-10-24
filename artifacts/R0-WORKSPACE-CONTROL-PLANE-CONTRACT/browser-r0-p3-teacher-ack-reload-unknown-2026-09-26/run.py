import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/browser-r0-p3-teacher-ack-reload-unknown-2026-09-26')
posts=[]; dropped={'v':False}
with sync_playwright() as p:
 b=p.chromium.launch(channel='msedge',headless=True)
 page=b.new_page(viewport={'width':390,'height':844})
 def handle(route):
  req=route.request
  if req.method=='POST' and re.search(r'/api/v1/demo/teacher/submissions/[^/]+/review-actions$',req.url) and not dropped['v']:
   response=route.fetch(); posts.append({'status':response.status,'idempotency_key':req.headers.get('idempotency-key'),'body':req.post_data,'receipt':response.text()}); dropped['v']=True; route.abort('failed')
  else: route.continue_()
 page.route('**/api/v1/demo/teacher/submissions/*/review-actions',handle)
 page.goto('http://127.0.0.1:8767/demo/teacher/',wait_until='domcontentloaded')
 page.locator('[data-view="reviews"]').click()
 page.wait_for_function("document.querySelectorAll('#review-task-list .review-task-choice').length===3")
 page.locator('#review-task-list .review-task-choice').filter(has_text='教师多任务队列隔离验证 A').locator('button').click()
 page.wait_for_function("!document.querySelector('#review-details').hidden && document.querySelector('#review-assignment-title').textContent.includes('A')")
 page.locator('#feedback-reason').fill('Synthetic ACK reload recovery reason for A.')
 page.locator('[data-review="approve"]').click()
 page.wait_for_function("!document.querySelector('#review-result').hidden && !document.querySelector('[data-review=approve]').disabled && document.querySelector('#feedback-reason').disabled")
 unknown=page.locator('#review-result').inner_text()
 page.reload(wait_until='domcontentloaded')
 page.locator('[data-view="reviews"]').click()
 page.wait_for_function("document.querySelectorAll('#review-task-list .review-task-choice').length===3")
 rows=[x.inner_text() for x in page.locator('#review-task-list .review-task-choice').all()]
 history=page.locator('#review-history-list').inner_text()
 state={'initial_unknown':unknown,'posts_before_refresh':posts,'rows_after_reload':rows,'review_history_after_reload':history,'review_result_visible_after_reload':page.locator('#review-result').is_visible(),'api_state_after_reload':page.locator('#api-state').inner_text(),'storage_keys':page.evaluate("({local:Object.keys(localStorage),session:Object.keys(sessionStorage)})"),'viewport':page.evaluate('({w:innerWidth,cw:document.documentElement.clientWidth,sw:document.documentElement.scrollWidth})')}
 assert posts[0]['status']==201
 assert not state['review_result_visible_after_reload'] and not state['storage_keys']['local'] and not state['storage_keys']['session']
 assert '认可并关闭' in state['review_history_after_reload'] and 'Synthetic ACK reload recovery reason for A.' in state['review_history_after_reload']
 assert '待复核 0 项' in state['rows_after_reload'][0] and '待复核 1 项' in state['rows_after_reload'][1]
 assert state['viewport']['cw']==state['viewport']['sw']==390
 (out/'browser-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
 page.screenshot(path=str(out/'ack-history-after-refresh-390px.png'),full_page=True)
 print(json.dumps(state,ensure_ascii=True,indent=2))
 b.close()
