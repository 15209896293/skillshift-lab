import { useNavigate } from 'react-router-dom'
import { useQueries } from '@tanstack/react-query'
import { useAssignments, useWorkspaceClient, queryKeys } from '@/api/hooks'
import type { Assignment, Submission } from '@/api/models'
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
import { Skeleton } from '@/components/ui/skeleton'
import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  FilePlus2,
  Inbox,
  RefreshCw,
  Sparkles,
} from 'lucide-react'

const assignmentStateLabel: Record<Assignment['state'], string> = {
  DRAFT: '草稿',
  PUBLISHED: '已发布',
  ARCHIVED: '已归档',
}

function isReviewable(submission: Submission) {
  return submission.state === 'SUBMITTED' || submission.state === 'RESUBMITTED'
}

export default function TeacherHome() {
  const navigate = useNavigate()
  const client = useWorkspaceClient('teacher')
  const assignmentsQuery = useAssignments('teacher')
  const assignments = assignmentsQuery.data ?? []

  const publishedAssignments = assignments.filter(
    (assignment) => assignment.state === 'PUBLISHED',
  )

  const reviewQueries = useQueries({
    queries: publishedAssignments.map((assignment) => ({
      queryKey: queryKeys.reviewQueue(assignment.id),
      queryFn: async () => {
        const result = await client.reviewQueue(assignment.id)
        return result.data.submissions
      },
      staleTime: 10_000,
    })),
  })

  const reviewQueueUnavailable = reviewQueries.some((query) => query.isError)
  const reviewQueueLoading = reviewQueries.some((query) => query.isPending)
  const reviewQueueKnown =
    !assignmentsQuery.isError &&
    !reviewQueueUnavailable &&
    reviewQueries.every((query) => Array.isArray(query.data))
  const pendingSubmissions = reviewQueueKnown
    ? reviewQueries.flatMap((query) => query.data ?? []).filter(isReviewable)
    : []

  const draftCount = assignments.filter((assignment) => assignment.state === 'DRAFT').length
  const assignmentsCountValue = assignmentsQuery.isLoading
    ? '…'
    : assignmentsQuery.isError
      ? '未知'
      : assignments.length
  const draftCountValue = assignmentsQuery.isLoading
    ? '…'
    : assignmentsQuery.isError
      ? '未知'
      : draftCount

  return (
    <div className="mx-auto w-full max-w-7xl space-y-5">
      <section className="flex flex-col justify-between gap-4 rounded-xl border bg-card p-5 shadow-sm md:flex-row md:items-center md:p-6">
        <div className="max-w-2xl">
          <div className="mb-2 flex items-center gap-2 text-primary">
            <Sparkles className="h-4 w-4" />
            <span className="text-xs font-semibold">教师工作台 · 固定合成角色</span>
          </div>
          <h2 className="text-xl font-semibold tracking-tight md:text-2xl">
            课程与任务
          </h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            管理合成任务、开始设计作业，或处理已有提交。当前演示没有教师登录、课程绑定或班级花名册。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => navigate('/teacher/designer')}>
            <FilePlus2 className="mr-2 h-4 w-4" />
            和 Agent 一起设计作业
          </Button>
          <Button variant="outline" onClick={() => navigate('/teacher/review')}>
            <Inbox className="mr-2 h-4 w-4" />
            提交复核
          </Button>
        </div>
      </section>

      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>本机合成演示</AlertTitle>
        <AlertDescription className="text-xs leading-5">
          任务来自固定教师演示身份并保存在服务进程内存中。登录、课程/教学班关联、截止时间和文件上传尚无 API；服务重启后演示数据会清空。
        </AlertDescription>
      </Alert>

      <section aria-label="任务概览" className="grid gap-3 sm:grid-cols-3">
        <SummaryCard
          icon={<BookOpen className="h-4 w-4" />}
          label="任务总数"
          value={assignmentsCountValue}
          detail="来自 GET /assignments"
        />
        <SummaryCard
          icon={<FilePlus2 className="h-4 w-4" />}
          label="待完善草稿"
          value={draftCountValue}
          detail="创建成功后为 DRAFT"
        />
        <SummaryCard
          icon={<Inbox className="h-4 w-4" />}
          label="待复核提交"
          value={
            assignmentsQuery.isLoading || reviewQueueLoading
              ? '…'
              : reviewQueueKnown
                ? pendingSubmissions.length
                : '未知'
          }
          detail={
            reviewQueueKnown
              ? '来自已发布任务的复核队列'
              : '复核队列读取失败时不显示为 0'
          }
        />
      </section>

      {assignmentsQuery.isError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>任务列表暂时不可用</AlertTitle>
          <AlertDescription className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs">
            <span>没有把读取失败显示成空任务列表。</span>
            <Button size="sm" variant="outline" onClick={() => void assignmentsQuery.refetch()}>
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" />重试
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {reviewQueueUnavailable && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>部分复核队列读取失败</AlertTitle>
          <AlertDescription className="text-xs leading-5">
            待复核提交数显示为“未知”。请进入提交复核页面查看具体任务并单独重试。
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <div>
            <CardTitle className="text-base">任务列表</CardTitle>
            <CardDescription className="mt-1 text-xs">
              按当前合成 API 返回的任务状态展示，不包含课程、班级或学生统计。
            </CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={() => navigate('/teacher/designer')}>
            新建任务 <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
          </Button>
        </CardHeader>
        <CardContent>
          {assignmentsQuery.isLoading ? (
            <div className="space-y-3">
              {[0, 1, 2].map((item) => (
                <Skeleton key={item} className="h-16 w-full" />
              ))}
            </div>
          ) : assignmentsQuery.isError ? null : assignments.length === 0 ? (
            <div className="flex flex-col items-center rounded-lg border border-dashed px-5 py-10 text-center">
              <BookOpen className="mb-3 h-8 w-8 text-muted-foreground" />
              <p className="text-sm font-medium">当前演示空间没有任务</p>
              <p className="mt-1 max-w-md text-xs leading-5 text-muted-foreground">
                创建的任务仅使用固定合成项目。真实课程和班级关联尚未接入。
              </p>
              <Button className="mt-4" size="sm" onClick={() => navigate('/teacher/designer')}>
                <FilePlus2 className="mr-1.5 h-4 w-4" />创建合成任务
              </Button>
            </div>
          ) : (
            <div className="divide-y">
              {assignments.map((assignment) => (
                <article key={assignment.id} className="flex flex-col gap-3 py-4 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="truncate text-sm font-medium">{assignment.task.title}</h3>
                      <Badge variant={assignment.state === 'PUBLISHED' ? 'default' : 'secondary'}>
                        {assignmentStateLabel[assignment.state]}
                      </Badge>
                    </div>
                    <p className="line-clamp-2 max-w-3xl text-xs leading-5 text-muted-foreground">
                      {assignment.task.goal}
                    </p>
                    <p className="text-[11px] text-muted-foreground">
                      固定项目 {assignment.task.starter_project_id} · 任务 v{assignment.task.version}
                    </p>
                  </div>
                  {assignment.state === 'PUBLISHED' ? (
                    <Button size="sm" variant="outline" className="shrink-0" onClick={() => navigate('/teacher/review')}>
                      查看提交 <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                    </Button>
                  ) : (
                    <Button size="sm" variant="outline" className="shrink-0" onClick={() => navigate('/teacher/designer')}>
                      继续设计 <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                    </Button>
                  )}
                </article>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <p className="text-center text-[11px] text-muted-foreground">
        提交数由 GET /assignments/{'{assignmentId}'}/review-queue 汇总；加载失败会显示未知，不将任务数当作学生数。
      </p>
    </div>
  )
}

interface SummaryCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  detail: string
}

function SummaryCard({ icon, label, value, detail }: SummaryCardProps) {
  return (
    <Card>
      <CardContent className="flex items-start gap-3 p-4">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          {icon}
        </span>
        <span className="min-w-0">
          <span className="block text-xs text-muted-foreground">{label}</span>
          <span className="mt-1 block text-xl font-semibold tabular-nums">{value}</span>
          <span className="mt-1 block text-[10px] leading-4 text-muted-foreground">{detail}</span>
        </span>
      </CardContent>
    </Card>
  )
}
