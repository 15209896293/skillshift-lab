import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueries } from '@tanstack/react-query'
import { queryKeys, useAssignments, useWorkspaceClient } from '@/api/hooks'
import type { Submission, SubmissionState } from '@/api/models'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  AlertCircle,
  ChevronRight,
  FileText,
  History,
  RefreshCw,
  Search,
} from 'lucide-react'

type SubmissionFilter = 'all' | 'review' | SubmissionState

interface SubmissionRow {
  submission: Submission
  taskTitle: string
}

const stateLabel: Record<SubmissionState, string> = {
  SUBMITTED: '待教师复核',
  RESUBMITTED: '补正后待复核',
  FEEDBACK_REQUIRED: '等待补正',
  ACCEPTED: '已认可',
}

export default function Submissions() {
  const navigate = useNavigate()
  const client = useWorkspaceClient('student')
  const assignmentsQuery = useAssignments('student')
  const assignments = assignmentsQuery.data ?? []
  const [statusFilter, setStatusFilter] = useState<SubmissionFilter>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const assignmentsWithWorkspace = assignments.filter((assignment) => assignment.workspace)
  const latestQueries = useQueries({
    queries: assignmentsWithWorkspace.map((assignment) => {
      const workspace = assignment.workspace!
      return {
        queryKey: queryKeys.latestSubmission(workspace.id),
        queryFn: async () => {
          const result = await client.latestSubmission(workspace.id)
          return result.data.submission
        },
      }
    }),
  })

  const submissionReadFailed = latestQueries.some((query) => query.isError)
  const submissionsLoading = latestQueries.some((query) => query.isPending)
  const submissionsKnown =
    !assignmentsQuery.isError &&
    !submissionReadFailed &&
    latestQueries.every((query) => query.data !== undefined)

  const allSubmissions = useMemo<SubmissionRow[]>(() => {
    return latestQueries.flatMap((query, index) => {
      const submission = query.data
      const assignment = assignmentsWithWorkspace[index]
      if (!submission || !assignment) return []
      return [{ submission, taskTitle: assignment.task.title }]
    })
  }, [assignmentsWithWorkspace, latestQueries])

  const filtered = allSubmissions.filter(({ submission, taskTitle }) => {
    if (statusFilter === 'review' && !['SUBMITTED', 'RESUBMITTED'].includes(submission.state)) return false
    if (statusFilter !== 'all' && statusFilter !== 'review' && submission.state !== statusFilter) return false
    if (searchQuery && !taskTitle.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  const pendingCount = allSubmissions.filter(({ submission }) =>
    submission.state === 'SUBMITTED' || submission.state === 'RESUBMITTED',
  ).length
  const acceptedCount = allSubmissions.filter(({ submission }) => submission.state === 'ACCEPTED').length
  const remediationCount = allSubmissions.filter(({ submission }) => submission.state === 'FEEDBACK_REQUIRED').length
  const summaryValue = (count: number) => (submissionsKnown ? count : '—')

  return (
    <div className="mx-auto w-full max-w-6xl space-y-4">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold">提交记录</h2>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            每个工作区仅显示 API 返回的最近一次提交；完整历史记录接口尚未提供。
          </p>
        </div>
        <div className="relative sm:w-64">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="按任务名称筛选"
            className="h-9 pl-8 text-xs"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
          />
        </div>
      </header>

      <section aria-label="提交状态统计" className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <MiniStat label="最近提交" value={summaryValue(allSubmissions.length)} active={statusFilter === 'all'} onClick={() => setStatusFilter('all')} />
        <MiniStat label="待教师复核" value={summaryValue(pendingCount)} active={statusFilter === 'review'} onClick={() => setStatusFilter('review')} color="text-amber-600" />
        <MiniStat label="已认可" value={summaryValue(acceptedCount)} active={statusFilter === 'ACCEPTED'} onClick={() => setStatusFilter('ACCEPTED')} color="text-emerald-600" />
        <MiniStat label="等待补正" value={summaryValue(remediationCount)} active={statusFilter === 'FEEDBACK_REQUIRED'} onClick={() => setStatusFilter('FEEDBACK_REQUIRED')} color="text-orange-600" />
      </section>

      {(assignmentsQuery.isError || submissionReadFailed) && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>提交状态未能完整读取</AlertTitle>
          <AlertDescription className="flex flex-col gap-2 text-xs sm:flex-row sm:items-center sm:justify-between">
            <span>汇总显示为“—”，避免把 API 读取失败当作没有提交。</span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                void assignmentsQuery.refetch()
                void Promise.all(latestQueries.map((query) => query.refetch()))
              }}
            >
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" />重试读取
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">最近提交快照</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {assignmentsQuery.isLoading || submissionsLoading ? (
            <div className="divide-y">
              {[0, 1, 2].map((item) => (
                <div key={item} className="space-y-2 p-4">
                  <Skeleton className="h-4 w-2/5" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
              ))}
            </div>
          ) : assignmentsQuery.isError ? null : filtered.length === 0 ? (
            <div className="flex flex-col items-center py-12 text-center">
              <History className="mb-3 h-9 w-9 text-muted-foreground/60" />
              <p className="text-sm font-medium">{submissionsKnown ? '没有符合条件的最近提交' : '提交状态未知'}</p>
              <p className="mt-1 max-w-md text-xs leading-5 text-muted-foreground">
                {submissionsKnown
                  ? '提交接口只返回每个工作区最近一次提交；完整版本历史尚未接入。'
                  : '请重试读取任务列表和最近提交接口。'}
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {filtered.map(({ submission, taskTitle }) => (
                <article key={submission.id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <h3 className="truncate text-sm font-medium">{taskTitle}</h3>
                      <Badge variant={submission.state === 'ACCEPTED' ? 'default' : 'secondary'} className="shrink-0 text-[10px]">
                        {stateLabel[submission.state]}
                      </Badge>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-muted-foreground">
                      <span>提交版本 v{submission.version}</span>
                      <span>工作区修订 {submission.workspace_revision}</span>
                      <span>事件序号 {submission.created_event_sequence}</span>
                    </div>
                    <p className="mt-2 line-clamp-2 text-xs leading-5 text-muted-foreground">
                      {submission.student_explanation}
                    </p>
                  </div>
                  <Button size="sm" variant="outline" onClick={() => navigate('/student/workbench')}>
                    打开任务工作台 <ChevronRight className="ml-1 h-3.5 w-3.5" />
                  </Button>
                </article>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      <p className="text-center text-[10px] text-muted-foreground">
        数据来自 GET /api/v1/demo/workspaces/{'{workspaceId}'}/submissions/latest；该端点不提供历史分页。
      </p>
    </div>
  )
}

interface MiniStatProps {
  label: string
  value: number | string
  active: boolean
  color?: string
  onClick: () => void
}

function MiniStat({ label, value, active, color, onClick }: MiniStatProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={'rounded-lg border p-3 text-left transition-colors ' + (active ? 'border-primary bg-primary/5' : 'bg-card hover:bg-muted/50')}
    >
      <span className={'block text-xs ' + (active ? 'text-primary' : 'text-muted-foreground')}>{label}</span>
      <span className={'mt-1 block text-lg font-semibold tabular-nums ' + (active ? 'text-primary' : color ?? '')}>{value}</span>
    </button>
  )
}
