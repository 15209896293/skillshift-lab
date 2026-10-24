$base = 'http://127.0.0.1:8000/api/v1/demo'
$schema = 'skillshift-api/v1'
$headers = @{'Content-Type'='application/json'}

function Post($path, $role, $data) {
    $body = @{ schema_version = $schema }
    foreach ($k in $data.Keys) { $body[$k] = $data[$k] }
    $json = $body | ConvertTo-Json -Depth 5
    $resp = Invoke-RestMethod -Uri "$base/$role$path" -Method Post -Headers $headers -Body $json
    return $resp
}

# 1. 创建任务
$r1 = Post '/assignments' 'teacher' @{
    title = '订单数据清洗与异常诊断'
    goal = '使用Python对订单CSV数据进行清洗，识别缺失值和异常记录。'
    student_responsibility = '确认清洗规则，检查每一步结果，解释判断依据。'
    submission_requirement = '提交main.py清洗脚本和README说明文档。'
    starter_project_id = 'orders-audit-v1'
    collaboration_mode = 'PROPOSE_WITH_STUDENT_CONFIRMATION'
}
$aid = $r1.data.id
Write-Host "Created assignment: $aid"

# 2. 发布任务
$r2 = Post "/assignments/$aid/publish" 'teacher' @{}
$wid = $r2.data.workspace.id
Write-Host "Published, workspace: $wid"

# 3. 学生启动
$r3 = Post "/workspaces/$wid/start" 'student' @{}
Write-Host "Started"

# 4. 学生提交
$artifactContents = @{
    'main.py' = "print('hello world')`n"
    'orders.csv' = "id,name,amount`n1,test,100`n"
    'README.md' = "# Data Cleaning`n`nDemo project.`n"
}
$r4 = Post "/workspaces/$wid/submissions" 'student' @{
    artifact_refs = @('main.py', 'orders.csv', 'README.md')
    artifact_contents = $artifactContents
    student_explanation = '我完成了数据清洗脚本的基础版本，包含了数据读取和基本框架，后续将继续完善异常检测功能。'
}
$sid = $r4.data.submission.id
$sver = $r4.data.submission.version
Write-Host "Submitted: $sid v$sver"

# 5. 教师要求补正
$r5 = Post "/submissions/$sid/review-actions" 'teacher' @{
    kind = 'REQUEST_REMEDIATION'
    reason = '代码缺少实际的数据清洗逻辑和异常检测功能，请补充完整的清洗实现。'
}
Write-Host "Remediation requested"

Write-Host ""
Write-Host "=== DONE ==="
Write-Host "Assignment: $aid"
Write-Host "Workspace:  $wid"
Write-Host "Submission: $sid"
