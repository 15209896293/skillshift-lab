import { useState } from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  FileCode,
  FileText,
  Table,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import type { Submission } from '@/api/models'
import type { ReviewActionType } from '@/api/mappers'

interface ReviewDetailProps {
  submission: Submission | null
  onReview: (action: ReviewActionType, reason: string) => void
  isReviewing?: boolean
  error?: string | null
}

const fileIcons: Record<string, typeof FileCode> = {
  'main.py': FileCode,
  'orders.csv': Table,
  'README.md': FileText,
}

const reviewActions: { type: ReviewActionType; label: string; icon: typeof CheckCircle2; variant: 'default' | 'destructive' | 'outline' | 'secondary' }[] = [
  { type: 'approve', label: '通过', icon: CheckCircle2, variant: 'default' },
  { type: 'explanation', label: '要求说明', icon: AlertTriangle, variant: 'secondary' },
  { type: 'evidence', label: '要求证据', icon: AlertTriangle, variant: 'secondary' },
  { type: 'remediation', label: '要求补正', icon: AlertTriangle, variant: 'destructive' },
  { type: 'environment', label: '环境问题', icon: AlertTriangle, variant: 'outline' },
]

export function ReviewDetail({
  submission,
  onReview,
  isReviewing = false,
  error = null,
}: ReviewDetailProps) {
  const [activeTab, setActiveTab] = useState<string>('main.py')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [pendingAction, setPendingAction] = useState<ReviewActionType | null>(null)
  const [reason, setReason] = useState('')
  const [reasonTouched, setReasonTouched] = useState(false)

  const snapshots = submission?.artifact_snapshots ?? []

  const handleClickAction = (action: ReviewActionType) => {
    setPendingAction(action)
    setReason('')
    setReasonTouched(false)
    setDialogOpen(true)
  }

  const handleConfirm = () => {
    if (!pendingAction) return
    setReasonTouched(true)
    if (pendingAction === 'approve') {
      onReview(pendingAction, reason.trim())
      setDialogOpen(false)
      return
    }
    if (reason.trim().length < 8) return
    onReview(pendingAction, reason.trim())
    setDialogOpen(false)
  }

  const activeSnapshot = snapshots.find((s) => s.logical_name === activeTab)

  const reasonValid = reason.trim().length >= 8

  const selectedActionLabel =
    reviewActions.find((a) => a.type === pendingAction)?.label ?? ''

  if (!submission) {
    return (
      <div className="flex h-full items-center justify-center rounded-md border bg-background text-sm text-muted-foreground">
        从左侧选择一个提交进行复核
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col rounded-md border bg-background">
      {/* 头部 */}
      <div className="border-b px-4 py-3">
        <div className="mb-1 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold">
              提交 #{submission.id.slice(0, 8)}
            </h3>
            <Badge variant="secondary" className="text-[10px]">
              v{submission.version}
            </Badge>
          </div>
          <Badge
            variant={submission.state === 'RESUBMITTED' ? 'warning' : 'default'}
            className="text-[10px]"
          >
            {submission.state === 'RESUBMITTED' ? '重新提交' : '待复核'}
          </Badge>
        </div>
        <p className="text-[11px] text-muted-foreground">
          工作区: {submission.workspace_id} · 事件序列:{' '}
          {submission.created_event_sequence}
        </p>
      </div>

      {/* 学生说明 */}
      <div className="border-b px-4 py-2.5">
        <Label className="text-[11px] font-medium text-muted-foreground">
          学生解题说明
        </Label>
        <p className="mt-1 text-xs leading-relaxed">
          {submission.student_explanation}
        </p>
      </div>

      {/* 代码查看 */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <div className="border-b px-2 pt-1">
          <TabsList className="h-7 bg-transparent">
            {snapshots.map((snap) => {
              const Icon = fileIcons[snap.logical_name] ?? FileCode
              return (
                <TabsTrigger
                  key={snap.logical_name}
                  value={snap.logical_name}
                  className="h-6 gap-1 px-2.5 text-xs data-[state=active]:bg-background data-[state=active]:shadow-none"
                >
                  <Icon className="h-3 w-3" />
                  {snap.logical_name}
                </TabsTrigger>
              )
            })}
          </TabsList>
        </div>

        <TabsContent
          value={activeTab}
          className="mt-0 flex-1 border-0 p-0"
        >
          <div className="flex h-[300px] flex-col overflow-hidden">
            <div className="flex-1 overflow-auto bg-muted/10 p-3">
              <pre className="font-mono text-[11px] leading-5 text-foreground whitespace-pre-wrap">
                {activeSnapshot?.content ?? '（无内容）'}
              </pre>
            </div>
            <div className="flex items-center justify-between border-t bg-muted/20 px-3 py-1 text-[10px] text-muted-foreground">
              <span>{activeSnapshot?.logical_name}</span>
              <span>{activeSnapshot?.size_bytes} bytes</span>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* 复核操作区 */}
      <div className="border-t p-3">
        {error && (
          <div className="mb-2 flex items-center gap-1.5 rounded-md bg-destructive/10 px-2 py-1.5 text-[11px] text-destructive">
            <AlertTriangle className="h-3 w-3" />
            {error}
          </div>
        )}
        <div className="flex flex-wrap gap-1.5">
          {reviewActions.map((action) => (
            <Button
              key={action.type}
              size="sm"
              variant={action.variant}
              className="h-7 gap-1 text-xs"
              onClick={() => handleClickAction(action.type)}
              disabled={isReviewing}
            >
              <action.icon className="h-3.5 w-3.5" />
              {action.label}
            </Button>
          ))}
        </div>
      </div>

      {/* 复核理由对话框 */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {pendingAction === 'approve' ? (
                <CheckCircle2 className="h-4 w-4 text-success" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-warning" />
              )}
              复核确认：{selectedActionLabel}
            </DialogTitle>
            <DialogDescription>
              {pendingAction === 'approve'
                ? '确认通过该提交？学生将收到通过通知。'
                : '请填写复核理由，学生将据此进行修改。'}
            </DialogDescription>
          </DialogHeader>

          <div>
            <Label className="mb-1.5 block text-xs font-medium">
              复核理由
              {pendingAction !== 'approve' && (
                <span className="ml-1 text-muted-foreground">(至少 8 字)</span>
              )}
            </Label>
            <Textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={
                pendingAction === 'approve'
                  ? '可选：填写通过评语'
                  : '请详细说明要求学生补充或修改的内容...'
              }
              className="min-h-[80px] resize-none text-sm"
            />
            {pendingAction !== 'approve' && reasonTouched && !reasonValid && (
              <p className="mt-1 text-[11px] text-destructive">
                理由至少需要 8 个字符
              </p>
            )}
            <div className="mt-1 text-right text-[11px] text-muted-foreground">
              {reason.length} 字
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDialogOpen(false)}
              disabled={isReviewing}
            >
              <X className="mr-1 h-3.5 w-3.5" />
              取消
            </Button>
            <Button
              size="sm"
              onClick={handleConfirm}
              disabled={
                isReviewing ||
                (pendingAction !== 'approve' && !reasonValid)
              }
              className={cn(
                pendingAction === 'approve' && 'bg-success hover:bg-success/90',
              )}
            >
              {isReviewing ? (
                <>
                  <span className="mr-1 h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  提交中...
                </>
              ) : (
                `确认${selectedActionLabel}`
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
