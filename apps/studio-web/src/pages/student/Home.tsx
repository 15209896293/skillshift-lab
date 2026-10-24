import { useNavigate } from 'react-router-dom'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useAssignments } from '@/api/hooks'
import {
  Briefcase,
  CheckCircle2,
  Clock,
  AlertTriangle,
  PlayCircle,
  ChevronRight,
  Sparkles,
  BookOpen,
  Activity,
  TrendingUp,
} from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'

export default function StudentHome() {
  const navigate = useNavigate()
  const { data: assignments = [], isLoading } = useAssignments('student')

  // 统计数据
  const total = assignments.length
  const inProgress = assignments.filter((a) => a.workspace?.state === 'IN_PROGRESS').length
  const pendingReview = assignments.filter(
    (a) => a.workspace?.state === 'REVIEW_REQUIRED' || a.workspace?.state === 'RESUBMITTED',
  ).length
  const needsRemediation = assignments.filter(
    (a) => a.workspace?.state === 'FEEDBACK_REQUIRED',
  ).length
  const completed = assignments.filter((a) => a.workspace?.state === 'CLOSED').length

  // 最近活跃的任务（进行中 + 需补正优先）
  const activeAssignments = assignments
    .filter((a) => a.workspace && a.workspace.state !== 'CLOSED')
    .sort((a, b) => {
      const priority = {
        FEEDBACK_REQUIRED: 0,
        IN_PROGRESS: 1,
        REVIEW_REQUIRED: 2,
        RESUBMITTED: 3,
        ASSIGNED: 4,
        PAUSED: 5,
      }
      return (
        (priority[a.workspace?.state as keyof typeof priority] ?? 99) -
        (priority[b.workspace?.state as keyof typeof priority] ?? 99)
      )
    })
    .slice(0, 3)

  const stateLabel: Record<string, string> = {
    ASSIGNED: '未开始',
    IN_PROGRESS: '进行中',
    PAUSED: '已暂停',
    REVIEW_REQUIRED: '待复核',
    FEEDBACK_REQUIRED: '需补正',
    RESUBMITTED: '已重交',
    CLOSED: '已完成',
  }

  const stateColor: Record<string, string> = {
    ASSIGNED: 'bg-slate-100 text-slate-700',
    IN_PROGRESS: 'bg-blue-50 text-blue-700',
    PAUSED: 'bg-slate-100 text-slate-600',
    REVIEW_REQUIRED: 'bg-amber-50 text-amber-700',
    FEEDBACK_REQUIRED: 'bg-red-50 text-red-700',
    RESUBMITTED: 'bg-violet-50 text-violet-700',
    CLOSED: 'bg-emerald-50 text-emerald-700',
  }

  const progressPercent = total > 0 ? Math.round((completed / total) * 100) : 0

  return (
    <div className="space-y-6">
      {/* 欢迎横幅 */}
      <Card className="overflow-hidden border-none bg-gradient-to-r from-blue-600 to-violet-600 text-white card-shadow">
        <CardContent className="p-6 md:p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="max-w-xl">
              <div className="mb-2 flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                <span className="text-sm font-medium opacity-90">欢迎回来</span>
              </div>
              <h2 className="text-2xl font-bold tracking-tight md:text-3xl">
                继续你的学习之旅
              </h2>
              <p className="mt-2 text-sm opacity-80 md:text-base">
                与 Agent 协作完成实训任务，在实践中掌握数字技能转型所需的核心能力。
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                size="lg"
                className="bg-white text-blue-600 hover:bg-blue-50"
                onClick={() => navigate('/student/workbench')}
              >
                <PlayCircle className="mr-2 h-4 w-4" />
                开始学习
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard
          icon={<Briefcase className="h-4 w-4" />}
          label="总任务"
          value={isLoading ? '—' : total}
          color="text-blue-600"
          bgColor="bg-blue-50"
        />
        <StatCard
          icon={<Activity className="h-4 w-4" />}
          label="进行中"
          value={isLoading ? '—' : inProgress}
          color="text-violet-600"
          bgColor="bg-violet-50"
        />
        <StatCard
          icon={<AlertTriangle className="h-4 w-4" />}
          label="待处理"
          value={isLoading ? '—' : needsRemediation + pendingReview}
          color="text-amber-600"
          bgColor="bg-amber-50"
        />
        <StatCard
          icon={<CheckCircle2 className="h-4 w-4" />}
          label="已完成"
          value={isLoading ? '—' : completed}
          color="text-emerald-600"
          bgColor="bg-emerald-50"
        />
      </div>

      {/* 学习进度 */}
      {!isLoading && total > 0 && (
        <Card className="card-shadow">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold">学习进度</CardTitle>
              <span className="text-sm font-medium text-muted-foreground">
                {completed} / {total} 项任务
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <Progress value={progressPercent} className="h-2" />
            <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
              <span>完成度 {progressPercent}%</span>
              <span className="flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                继续加油
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 进行中的任务 */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">我的任务</h3>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={() => navigate('/student/workbench')}
          >
            查看全部
            <ChevronRight className="ml-1 h-3 w-3" />
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardContent className="p-4">
                  <Skeleton className="h-5 w-2/3" />
                  <Skeleton className="mt-2 h-4 w-1/2" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : activeAssignments.length === 0 ? (
          <Card className="card-shadow">
            <CardContent className="flex flex-col items-center justify-center py-10">
              <BookOpen className="mb-3 h-10 w-10 text-muted-foreground/60" />
              <p className="text-sm font-medium text-muted-foreground">暂无进行中的任务</p>
              <p className="mt-1 text-xs text-muted-foreground">
                教师发布任务后，这里会显示你的学习任务
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {activeAssignments.map((a) => (
              <Card
                key={a.id}
                className="card-shadow card-shadow-hover cursor-pointer transition-all"
                onClick={() => navigate('/student/workbench')}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="truncate text-sm font-semibold">{a.task.title}</h4>
                        <Badge
                          className={
                            'shrink-0 text-[10px] font-medium ' +
                            (stateColor[a.workspace?.state ?? 'ASSIGNED'] ?? '')
                          }
                        >
                          {stateLabel[a.workspace?.state ?? 'ASSIGNED']}
                        </Badge>
                      </div>
                      <p className="mt-1 line-clamp-1 text-xs text-muted-foreground">
                        {a.task.goal}
                      </p>
                      <div className="mt-3 flex items-center gap-4 text-[11px] text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {a.task.collaboration_mode === 'QA_ONLY'
                            ? '问答模式'
                            : '提议模式'}
                        </span>
                        <span className="flex items-center gap-1">
                          v{a.task.version}
                        </span>
                      </div>
                    </div>
                    <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* 补正提醒 */}
      {!isLoading && needsRemediation > 0 && (
        <Card className="border-red-200 bg-red-50/50 card-shadow">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-100">
                <AlertTriangle className="h-4 w-4 text-red-600" />
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="text-sm font-semibold text-red-900">
                  有 {needsRemediation} 条补正要求待处理
                </h4>
                <p className="mt-0.5 text-xs text-red-700/80">
                  教师对你的提交提出了修改意见，请查看反馈后重新提交。
                </p>
                <Button
                  size="sm"
                  variant="destructive"
                  className="mt-3 h-7"
                  onClick={() => navigate('/student/workbench')}
                >
                  立即处理
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: number | string
  color: string
  bgColor: string
}

function StatCard({ icon, label, value, color, bgColor }: StatCardProps) {
  return (
    <Card className="card-shadow">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${bgColor} ${color}`}>
            {icon}
          </div>
          <div>
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-xl font-bold tracking-tight">{value}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
