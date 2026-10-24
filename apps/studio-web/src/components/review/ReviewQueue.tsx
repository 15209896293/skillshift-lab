import { FileCode, FileText, Table, Clock, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { Submission } from '@/api/models'

interface ReviewQueueProps {
  submissions: Submission[]
  selectedId: string | null
  onSelect: (id: string) => void
  isLoading?: boolean
}

const fileIcons: Record<string, typeof FileCode> = {
  'main.py': FileCode,
  'orders.csv': Table,
  'README.md': FileText,
}

export function ReviewQueue({
  submissions,
  selectedId,
  onSelect,
  isLoading = false,
}: ReviewQueueProps) {
  return (
    <div className="flex h-full flex-col rounded-md border bg-background">
      <div className="flex items-center justify-between border-b px-3 py-2">
        <div>
          <h3 className="text-sm font-medium">待复核队列</h3>
          <p className="text-[11px] text-muted-foreground">
            {submissions.length} 份待处理
          </p>
        </div>
        <Badge variant="warning" className="text-[10px]">
          {submissions.length} 待复核
        </Badge>
      </div>
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            加载中...
          </div>
        ) : submissions.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            暂无待复核提交
          </div>
        ) : (
          <div className="p-2">
            {submissions.map((sub) => {
              const isSelected = sub.id === selectedId
              const isResubmitted = sub.state === 'RESUBMITTED'

              return (
                <button
                  key={sub.id}
                  onClick={() => onSelect(sub.id)}
                  className={cn(
                    'mb-1 w-full rounded-md border p-3 text-left transition-colors',
                    isSelected
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-muted-foreground/30 hover:bg-muted/30',
                  )}
                >
                  <div className="mb-1.5 flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <User className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-xs font-medium">
                        工作区 {sub.workspace_id.slice(0, 8)}...
                      </span>
                    </div>
                    <Badge
                      variant={isResubmitted ? 'warning' : 'secondary'}
                      className="text-[10px]"
                    >
                      {isResubmitted ? '重交' : '新提交'}
                    </Badge>
                  </div>

                  {/* 文件清单 */}
                  <div className="mb-2 flex flex-wrap gap-1">
                    {sub.artifact_refs.map((ref) => {
                      const Icon = fileIcons[ref.logical_name] ?? FileCode
                      return (
                        <span
                          key={ref.id}
                          className="inline-flex items-center gap-1 rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
                        >
                          <Icon className="h-3 w-3" />
                          {ref.logical_name}
                        </span>
                      )
                    })}
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="h-2.5 w-2.5" />
                      v{sub.version}
                    </span>
                    <span>事件 #{sub.created_event_sequence}</span>
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
