import {
  Briefcase,
  Clock,
  CheckCircle2,
  AlertCircle,
  Play,
  Pause,
  RotateCcw,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { Assignment, WorkspaceState } from '@/api/models'

interface TaskListProps {
  assignments: Assignment[]
  selectedId: string | null
  onSelect: (id: string) => void
  isLoading?: boolean
}

const stateConfig: Record<
  WorkspaceState,
  { label: string; variant: 'default' | 'secondary' | 'outline' | 'success' | 'warning' | 'destructive'; icon: typeof Clock }
> = {
  ASSIGNED: { label: '未开始', variant: 'outline', icon: Clock },
  IN_PROGRESS: { label: '进行中', variant: 'default', icon: Play },
  PAUSED: { label: '已暂停', variant: 'secondary', icon: Pause },
  REVIEW_REQUIRED: { label: '待复核', variant: 'warning', icon: AlertCircle },
  FEEDBACK_REQUIRED: { label: '需补正', variant: 'destructive', icon: AlertCircle },
  RESUBMITTED: { label: '已重交', variant: 'warning', icon: RotateCcw },
  CLOSED: { label: '已完成', variant: 'success', icon: CheckCircle2 },
}

export function TaskList({
  assignments,
  selectedId,
  onSelect,
  isLoading = false,
}: TaskListProps) {
  return (
    <div className="flex h-full flex-col rounded-md border bg-background">
      <div className="border-b px-3 py-2">
        <h3 className="text-sm font-medium">我的任务</h3>
        <p className="text-[11px] text-muted-foreground">
          共 {assignments.length} 个任务
        </p>
      </div>
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            加载中...
          </div>
        ) : assignments.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            暂无任务
          </div>
        ) : (
          <div className="p-2">
            {assignments.map((assignment) => {
              const state = assignment.workspace?.state
              const config = state ? stateConfig[state] : null
              const isSelected = assignment.id === selectedId

              return (
                <button
                  key={assignment.id}
                  onClick={() => onSelect(assignment.id)}
                  className={cn(
                    'mb-1 w-full rounded-md border p-3 text-left transition-colors',
                    isSelected
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-muted-foreground/30 hover:bg-muted/30',
                  )}
                >
                  <div className="mb-1.5 flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <Briefcase className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-sm font-medium line-clamp-1">
                        {assignment.task.title}
                      </span>
                    </div>
                    {config && (
                      <Badge
                        variant={config.variant as never}
                        className="shrink-0 text-[10px]"
                      >
                        {config.label}
                      </Badge>
                    )}
                  </div>
                  <p className="line-clamp-2 text-xs text-muted-foreground">
                    {assignment.task.goal}
                  </p>
                  <div className="mt-2 flex items-center gap-2 text-[10px] text-muted-foreground">
                    <span>v{assignment.version}</span>
                    <span>·</span>
                    <span>{assignment.task.collaboration_mode === 'QA_ONLY' ? '问答模式' : '提议模式'}</span>
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </ScrollArea>
    </div>
  )
}

export { stateConfig }
