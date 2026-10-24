import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  useAssignments,
  useCreateAssignment,
  usePublishAssignment,
} from '@/api/hooks'
import { errorStateFor } from '@/api/types'
import type { Assignment, CollaborationMode } from '@/api/models'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import {
  AlertCircle,
  ArrowRight,
  Bot,
  FileText,
  LockKeyhole,
  Paperclip,
  Send,
  Sparkles,
} from 'lucide-react'

const DEMO_PROJECT_ID = 'orders-audit-v1'

interface AssignmentForm {
  title: string
  goal: string
  studentResponsibility: string
  submissionRequirement: string
  collaborationMode: CollaborationMode
}

const initialForm: AssignmentForm = {
  title: '订单数据清洗与异常诊断',
  goal: '使用 Python 对订单 CSV 数据进行清洗，识别缺失值、格式错误和异常记录，并输出清洗后的结果与异常清单。',
  studentResponsibility: '你需要确认清洗规则、检查每一步结果、解释异常判断依据，并对最终提交负责。',
  submissionRequirement: '提交 main.py 清洗脚本、README.md 说明文档和清洗后的订单数据。',
  collaborationMode: 'PROPOSE_WITH_STUDENT_CONFIRMATION',
}

const emptyForm: AssignmentForm = {
  title: '',
  goal: '',
  studentResponsibility: '',
  submissionRequirement: '',
  collaborationMode: 'PROPOSE_WITH_STUDENT_CONFIRMATION',
}

const assignmentStateLabel: Record<Assignment['state'], string> = {
  DRAFT: '草稿',
  PUBLISHED: '已发布',
  ARCHIVED: '已归档',
}

export default function TeacherDesigner() {
  const assignmentsQuery = useAssignments('teacher')
  const assignments = assignmentsQuery.data ?? []
  const createMutation = useCreateAssignment()
  const [form, setForm] = useState<AssignmentForm>(initialForm)
  const [formError, setFormError] = useState<string | null>(null)
  const [createdMessage, setCreatedMessage] = useState<string | null>(null)

  const updateField = useCallback(
    <K extends keyof AssignmentForm>(field: K, value: AssignmentForm[K]) => {
      setForm((current) => ({ ...current, [field]: value }))
      setFormError(null)
      setCreatedMessage(null)
    },
    [],
  )

  const handleCreateDraft = useCallback(async () => {
    setFormError(null)
    setCreatedMessage(null)
    try {
      const assignment = await createMutation.mutateAsync({
        title: form.title.trim(),
        goal: form.goal.trim(),
        student_responsibility: form.studentResponsibility.trim(),
        submission_requirement: form.submissionRequirement.trim(),
        starter_project_id: DEMO_PROJECT_ID,
        collaboration_mode: form.collaborationMode,
      })
      setCreatedMessage(`已创建草稿：${assignment.task.title}`)
      setForm(emptyForm)
    } catch (error) {
      setFormError(errorStateFor(error, '创建任务草稿').message)
    }
  }, [createMutation, form])

  const canCreate =
    form.title.trim().length > 0 &&
    form.goal.trim().length > 0 &&
    form.studentResponsibility.trim().length > 0 &&
    form.submissionRequirement.trim().length > 0 &&
    form.title.length <= 128 &&
    form.goal.length <= 4096 &&
    form.studentResponsibility.length <= 2048 &&
    form.submissionRequirement.length <= 2048

  return (
    <div className="mx-auto w-full max-w-[1500px] space-y-4">
      <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold tracking-tight">作业设计 Agent</h2>
            <Badge variant="secondary">本机合成演示</Badge>
          </div>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            对话区预留 Agent 工作流；右侧字段通过当前合成 API 创建任务草稿。
          </p>
        </div>
        <Link to="/teacher" className="text-xs text-primary hover:underline">
          ← 返回课程与任务
        </Link>
      </header>

      {(createdMessage || formError) && (
        <Alert variant={formError ? 'destructive' : 'default'}>
          {formError ? <AlertCircle className="h-4 w-4" /> : <FileText className="h-4 w-4" />}
          <AlertTitle>{formError ? '草稿创建失败' : '任务草稿已保存'}</AlertTitle>
          <AlertDescription className="text-xs">{formError ?? createdMessage}</AlertDescription>
        </Alert>
      )}

      <div className="grid min-h-[680px] gap-4 xl:grid-cols-[minmax(300px,0.82fr)_minmax(470px,1.18fr)]">
        <section aria-label="作业设计对话" className="flex min-h-[500px] flex-col overflow-hidden rounded-xl border bg-card shadow-sm xl:min-h-0">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Bot className="h-4 w-4" />
              </span>
              <span>
                <span className="block text-sm font-medium">和 Agent 讨论作业</span>
                <span className="block text-[10px] text-muted-foreground">教师起草对话 API 尚未接入</span>
              </span>
            </div>
            <Badge variant="outline" className="text-[10px]">未接通</Badge>
          </div>

          <div className="flex-1 space-y-4 overflow-auto p-4">
            <div className="flex items-start gap-2.5">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-white">
                <Sparkles className="h-3.5 w-3.5" />
              </span>
              <div className="max-w-[95%] rounded-xl rounded-tl-sm border bg-muted/40 p-3 text-xs leading-5">
                <p className="font-medium">作业设计助手</p>
                <p className="mt-1 text-muted-foreground">
                  这里将用于通过对话整理课程目标、学生责任和提交要求。目前没有教师侧 AI 起草接口，因此不会生成或伪装 AI 回复。你可以直接在右侧编辑任务字段并创建合成草稿。
                </p>
              </div>
            </div>

            <Alert>
              <LockKeyhole className="h-4 w-4" />
              <AlertTitle className="text-xs">当前可用接口</AlertTitle>
              <AlertDescription className="space-y-1 text-[11px] leading-5">
                <p><code>GET /api/v1/demo/assignments</code>：列出合成任务</p>
                <p><code>POST /api/v1/demo/assignments</code>：创建固定项目草稿</p>
                <p><code>POST /api/v1/demo/assignments/{'{id}'}/publish</code>：发布草稿</p>
              </AlertDescription>
            </Alert>

            <div className="rounded-lg border border-dashed p-3 text-[11px] leading-5 text-muted-foreground">
              <p className="font-medium text-foreground">资料上传当前不可用</p>
              <p>API 没有文档上传、PDF 解析或资料引用端点。不要把课程文件或学生信息放入当前合成演示。</p>
            </div>
          </div>

          <div className="border-t bg-background/70 p-3">
            <Textarea
              aria-label="教师 AI 对话输入"
              disabled
              placeholder="教师侧 Agent 对话服务接入后可在此描述作业……"
              className="min-h-20 resize-none text-xs"
            />
            <div className="mt-2 flex items-center gap-2">
              <Button size="sm" variant="outline" disabled aria-label="添加课程资料">
                <Paperclip className="mr-1.5 h-3.5 w-3.5" />添加资料
              </Button>
              <span className="flex-1" />
              <Button size="sm" disabled>
                <Send className="mr-1.5 h-3.5 w-3.5" />发送
              </Button>
            </div>
          </div>
        </section>

        <section aria-label="任务草稿表单" className="flex min-w-0 flex-col rounded-xl border bg-card shadow-sm">
          <div className="flex items-start justify-between gap-3 border-b px-4 py-3">
            <div>
              <h3 className="text-sm font-semibold">作业任务</h3>
              <p className="mt-1 text-[10px] leading-4 text-muted-foreground">
                编辑后创建为草稿；只有点击发布才会向学生工作区开放。
              </p>
            </div>
            <Button size="sm" variant="outline" onClick={() => { setForm(initialForm); setFormError(null); setCreatedMessage(null) }}>
              恢复固定示例
            </Button>
          </div>

          <div className="flex-1 space-y-4 overflow-auto p-4">
            <Field label="作业标题" hint={`${form.title.length} / 128`} htmlFor="task-title">
              <Input
                id="task-title"
                maxLength={128}
                value={form.title}
                onChange={(event) => updateField('title', event.target.value)}
                placeholder="简明描述学生要完成的任务"
              />
            </Field>

            <Field label="任务目标" hint={`${form.goal.length} / 4096`} htmlFor="task-goal">
              <Textarea
                id="task-goal"
                maxLength={4096}
                rows={4}
                value={form.goal}
                onChange={(event) => updateField('goal', event.target.value)}
                placeholder="说明任务目标和需要完成的工作"
              />
            </Field>

            <Field label="学生责任" hint={`${form.studentResponsibility.length} / 2048`} htmlFor="task-responsibility">
              <Textarea
                id="task-responsibility"
                maxLength={2048}
                rows={3}
                value={form.studentResponsibility}
                onChange={(event) => updateField('studentResponsibility', event.target.value)}
                placeholder="说明学生需要亲自确认、解释或验证的内容"
              />
            </Field>

            <Field label="提交要求" hint={`${form.submissionRequirement.length} / 2048`} htmlFor="task-requirement">
              <Textarea
                id="task-requirement"
                maxLength={2048}
                rows={3}
                value={form.submissionRequirement}
                onChange={(event) => updateField('submissionRequirement', event.target.value)}
                placeholder="说明需要提交的任务结果或解释"
              />
            </Field>

            <Field label="Agent 协作模式" htmlFor="collaboration-mode">
              <Select
                value={form.collaborationMode}
                onValueChange={(value) => updateField('collaborationMode', value as CollaborationMode)}
              >
                <SelectTrigger id="collaboration-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="QA_ONLY">问答模式：仅提供任务内引导</SelectItem>
                  <SelectItem value="PROPOSE_WITH_STUDENT_CONFIRMATION">
                    提议模式：修改提议需学生确认
                  </SelectItem>
                </SelectContent>
              </Select>
            </Field>

            <div className="rounded-lg border bg-muted/30 p-3">
              <p className="text-xs font-medium">固定合成项目</p>
              <p className="mt-1 text-xs text-muted-foreground">{DEMO_PROJECT_ID} · execution_enabled=false</p>
              <p className="mt-1 text-[10px] leading-4 text-muted-foreground">
                当前接口不支持课程选择、截止时间、上传文件或任意任务模板。
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-2 border-t p-4 sm:flex-row sm:items-center sm:justify-between">
            <span className="text-[10px] text-muted-foreground">
              使用 POST /assignments；接口固定返回 DRAFT
            </span>
            <Button onClick={handleCreateDraft} disabled={!canCreate || createMutation.isPending}>
              {createMutation.isPending ? '创建中…' : '创建任务草稿'}
              {!createMutation.isPending && <ArrowRight className="ml-1.5 h-4 w-4" />}
            </Button>
          </div>
        </section>
      </div>

      <section className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold">已有任务</h3>
            <p className="mt-1 text-[10px] text-muted-foreground">发布操作使用任务当前 revision，冲突时显示 API 错误并可重新读取。</p>
          </div>
          <Link to="/teacher/review" className="text-xs text-primary hover:underline">前往提交复核 →</Link>
        </div>
        {assignmentsQuery.isLoading ? (
          <div className="grid gap-3 md:grid-cols-2">{[0, 1].map((item) => <Skeleton key={item} className="h-28" />)}</div>
        ) : assignmentsQuery.isError ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>任务读取失败</AlertTitle>
            <AlertDescription className="text-xs">草稿创建表单仍可使用；已有任务状态未确认。</AlertDescription>
          </Alert>
        ) : assignments.length === 0 ? (
          <p className="rounded-lg border border-dashed p-5 text-center text-xs text-muted-foreground">尚无任务记录。</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {assignments.map((assignment) => (
              <AssignmentCard key={assignment.id} assignment={assignment} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

interface FieldProps {
  label: string
  htmlFor: string
  hint?: string
  children: React.ReactNode
}

function Field({ label, htmlFor, hint, children }: FieldProps) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between gap-2">
        <Label htmlFor={htmlFor} className="text-xs font-medium">{label}</Label>
        {hint && <span className="text-[10px] tabular-nums text-muted-foreground">{hint}</span>}
      </div>
      {children}
    </div>
  )
}

function AssignmentCard({ assignment }: { assignment: Assignment }) {
  const publishMutation = usePublishAssignment(assignment.id)
  const [error, setError] = useState<string | null>(null)

  const publish = async () => {
    setError(null)
    try {
      await publishMutation.mutateAsync(assignment.revision)
    } catch (cause) {
      setError(errorStateFor(cause, '发布任务').message)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="line-clamp-2 text-sm">{assignment.task.title}</CardTitle>
            <CardDescription className="mt-1 line-clamp-2 text-[10px] leading-4">
              {assignment.task.goal}
            </CardDescription>
          </div>
          <Badge variant={assignment.state === 'PUBLISHED' ? 'default' : 'secondary'} className="shrink-0">
            {assignmentStateLabel[assignment.state]}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex flex-wrap items-center justify-between gap-2 pt-1">
        <span className="text-[10px] text-muted-foreground">{assignment.id} · revision {assignment.revision}</span>
        {assignment.state === 'DRAFT' && (
          <Button size="sm" variant="outline" onClick={publish} disabled={publishMutation.isPending}>
            {publishMutation.isPending ? '发布中…' : '发布任务'}
          </Button>
        )}
        {assignment.state === 'PUBLISHED' && <span className="text-[10px] text-muted-foreground">学生工作区已由 API 创建</span>}
        {error && <p className="w-full text-[10px] text-destructive">{error}</p>}
      </CardContent>
    </Card>
  )
}
