import json, re, time
from pathlib import Path
from playwright.sync_api import sync_playwright
out = Path('artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/browser-r0-p3-student-submit-receipt-lost-2026-09-26')
records=[]; first={'dropped':False}
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge', headless=True)
    page=browser.new_page(viewport={'width':390,'height':844}, device_scale_factor=1)
    def intercept(route):
        req=route.request
        if req.method=='POST' and re.search(r'/api/v1/demo/student/workspaces/[^/]+/submissions$', req.url) and not first['dropped']:
            response=route.fetch()
            body=response.text()
            records.append({'phase':'first','status':response.status,'url':req.url,'method':req.method,'post_data':req.post_data,'idempotency_key':req.headers.get('idempotency-key'),'if_match':req.headers.get('if-match'),'response_body':body})
            first['dropped']=True
            route.abort('failed')
        elif req.method=='POST' and re.search(r'/api/v1/demo/student/workspaces/[^/]+/submissions$', req.url):
            response=route.fetch()
            records.append({'phase':'retry','status':response.status,'url':req.url,'method':req.method,'post_data':req.post_data,'idempotency_key':req.headers.get('idempotency-key'),'if_match':req.headers.get('if-match'),'response_body':response.text()})
            route.fulfill(response=response)
        else:
            route.continue_()
    page.route('**/api/v1/demo/student/workspaces/*/submissions', intercept)
    page.goto('http://127.0.0.1:8767/demo/student/', wait_until='domcontentloaded')
    page.wait_for_function("document.querySelectorAll('#task-picker option').length >= 3")
    page.locator('#task-picker').select_option(index=1)
    page.wait_for_function("document.querySelector('#task-picker-state').textContent.includes('进行中')", timeout=15000)
    page.locator('[data-action="open-submit"]').click()
    page.locator('#submission-note').fill('固定合成提交：已逐项核对快照，不确定处已记录。')
    page.locator('#confirm-submit').click()
    page.wait_for_function("document.querySelector('#confirm-submit').textContent.includes('重试同一提交')")
    page.wait_for_timeout(300)
    unknown={'api_state':page.locator('#api-state').inner_text(),'button':page.locator('#confirm-submit').inner_text(),'note_disabled':page.locator('#submission-note').is_disabled(),'textarea_disabled':page.locator('#code-editor').is_disabled(),'modal_open':page.locator('#submit-dialog').evaluate('(e)=>e.open'),'viewport':page.evaluate('({w:innerWidth, cw:document.documentElement.clientWidth, sw:document.documentElement.scrollWidth})')}
    page.screenshot(path=str(out/'submission-unknown-390px.png'),full_page=True)
    page.locator('#confirm-submit').click()
    page.wait_for_function("!document.querySelector('#submit-dialog').open && document.querySelector('#edit-status').textContent.includes('接收')")
    page.wait_for_timeout(200)
    workspace_id=re.search(r'/workspaces/([^/]+)/submissions$', records[0]['url']).group(1)
    latest=page.evaluate("async (id)=>{let r=await fetch('/api/v1/demo/student/workspaces/'+id+'/submissions/latest');return await r.json()}",workspace_id)
    events=page.evaluate("async (id)=>{let r=await fetch('/api/v1/demo/student/workspaces/'+id+'/events?after_sequence=0&limit=50');return await r.json()}",workspace_id)
    result={'browser':'Edge via Playwright','viewport':'390x844','workspace_id':workspace_id,'task_options':[o.inner_text() for o in page.locator('#task-picker option').all()],'unknown_state':unknown,'request_records':records,'same_request':all(records[0][k]==records[1][k] for k in ('method','url','post_data','idempotency_key','if_match')),'latest':latest,'submission_created_events':[e for e in events.get('data',{}).get('events',[]) if e.get('event_type')=='submission.created'],'final_state_label':page.locator('#task-picker-state').inner_text(),'viewport_final':page.evaluate('({w:innerWidth,cw:document.documentElement.clientWidth,sw:document.documentElement.scrollWidth})')}
    page.screenshot(path=str(out/'submission-retry-recovered-390px.png'),full_page=True)
    (out/'browser-run.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    browser.close()
