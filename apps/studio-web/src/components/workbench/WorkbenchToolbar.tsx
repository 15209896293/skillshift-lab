import {
  Play,
  Pause,
  Upload,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { WorkspaceState } from '@/api/models'

interface WorkbenchToolbarProps {
  workspaceId?: string
  state: WorkspaceState | null
  revision: number | null
  assignmentTitle?: string
  onStart: () => void
  onPause: () => void
  onSubmit: () => void
  onRefresh: () => void
  isStarting?: boolean
  isPausing?: boolean
  isRefreshing?: boolean
  canSubmit?: boolean
  hasChanges?: boolean
}

const stateDisplay: Record<
  WorkspaceState,
  { label: string; variant: 'default' | 'secondary' | 'outline' | 'success' | 'warning' | 'destructive'; icon: typeof Clock }
> = {
  ASSIGNED: { label: '未开始', variant: 'outline', icon: Clock },
  IN_PROGRESS: { label: '进行中', variant: 'default', icon: Play },
  PAUSED: { label: '已暂停', variant: 'secondary', icon: Pause },
  REVIEW_REQUIRED: { label: '待复核', variant: 'warning', icon: Clock },
  FEEDBACK_REQUIRED: { label: '需补正', variant: 'destructive', icon: AlertTriangle },
  RESUBMITTED: { label: '已重交', variant: 'warning', icon: RefreshCw },
  CLOSED: { label: '已完成', variant: 'success', icon: CheckCircle2 },
}

export function WorkbenchToolbar({
  state,
  revision,
  assignmentTitle,
  onStart,
  onPause,
  onSubmit,
  onRefresh,
  isStarting = false,
  isPausing = false,
  isRefreshing = false,
  canSubmit = false,
  hasChanges = false,
}: WorkbenchToolbarProps) {
  const config = state ? stateDisplay[state] : null

  const canStart = state === 'ASSIGNED' || state === 'PAUSED' || state === 'FEEDBACK_REQUIRED'
  const canPause = state === 'IN_PROGRESS'
  const showSubmit = canSubmit && state === 'IN_PROGRESS'

  return (
    <div className="flex items-center gap-3 rounded-md border bg-background px-4 py-2.5">
      {/* 任务标题 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h2 className="truncate text-sm font-semibold">
            {assignmentTitle || '未选择任务'}
          </h2>
          {config && (
            <Badge
              variant={config.variant as never}
              className="shrink-0 text-[10px]"
            >
              <config.icon className="mr-1 h-2.5 w-2.5" />
              {config.label}
            </Badge>
          )}
        </div>
        {revision !== null && (
          <p className="text-[11px] text-muted-foreground">
            修订号: {revision}
            {hasChanges && (
              <span className="ml-2 text-violet-600">● 有未保存变更</span>
            )}
          </p>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="h-8 gap-1"
          onClick={onRefresh}
          disabled={isRefreshing || !state}
        >
          <RefreshCw
            className={cn('h-3.5 w-3.5', isRefreshing && 'animate-spin')}
          />
          刷新
        </Button>

        {canStart && (
          <Button
            size="sm"
            className="h-8 gap-1"
            onClick={onStart}
            disabled={isStarting}
          >
            <Play className={cn('h-3.5 w-3.5', isStarting && 'animate-pulse')} />
            {isStarting ? '启动中...' : '启动'}
          </Button>
        )}

        {canPause && (
          <Button
            size="sm"
            variant="secondary"
            className="h-8 gap-1"
            onClick={onPause}
            disabled={isPausing}
          >
            <Pause className="h-3.5 w-3.5" />
            {isPausing ? '暂停中...' : '暂停'}
          </Button>
        )}

        {showSubmit && (
          <Button
            size="sm"
            className="h-8 gap-1"
            onClick={onSubmit}
          >
            <Upload className="h-3.5 w-3.5" />
            提交作业
          </Button>
        )}
      </div>
    </div>
  )
}
