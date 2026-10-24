import { useState, useCallback } from 'react'
import {
  useAssignments,
  useReviewQueue,
  useReview,
  queryKeys,
} from '@/api/hooks'
import { mapReviewActionToDto } from '@/api/mappers'
import { errorStateFor } from '@/api/types'
import type { ReviewActionType } from '@/api/mappers'
import { ReviewQueue } from '@/components/review/ReviewQueue'
import { ReviewDetail } from '@/components/review/ReviewDetail'
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { useQueryClient } from '@tanstack/react-query'

export default function TeacherReview() {
  const queryClient = useQueryClient()
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string | null>(null)
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // API: 任务列表（教师端）
  const { data: assignments = [], isLoading: assignmentsLoading } = useAssignments('teacher')

  // 默认选中第一个已发布的任务
  const publishedAssignments = assignments.filter((a) => a.state === 'PUBLISHED')

  // API: 复核队列
  const { data: submissions = [], isLoading: queueLoading } = useReviewQueue(
    selectedAssignmentId ?? undefined,
  )

  // 选中的 submission
  const selectedSubmission = submissions.find((s) => s.id === selectedSubmissionId)

  // 复核 mutation
  const reviewMutation = useReview(selectedSubmissionId ?? undefined)

  const handleSelectAssignment = useCallback(
    (id: string) => {
      setSelectedAssignmentId(id)
      setSelectedSubmissionId(null)
      setErrorMsg(null)
      setSuccessMsg(null)
    },
    [],
  )

  const handleSelectSubmission = useCallback((id: string) => {
    setSelectedSubmissionId(id)
    setErrorMsg(null)
    setSuccessMsg(null)
  }, [])

  const handleReview = useCallback(
    async (action: ReviewActionType, reason: string) => {
      if (!selectedSubmission) return
      setErrorMsg(null)
      setSuccessMsg(null)

      try {
        const dto = mapReviewActionToDto(action, reason)
        await reviewMutation.mutateAsync({
          dto,
          revision: selectedSubmission.workspace_revision,
          expectedSubmissionVersion: selectedSubmission.version,
        })

        setSuccessMsg(
          action === 'approve'
            ? '已通过该提交。'
            : `已发送${
                {
                  explanation: '说明',
                  evidence: '证据',
                  remediation: '补正',
                  environment: '环境问题',
                }[action]
              }要求。`,
        )

        // 刷新复核队列
        if (selectedAssignmentId) {
          queryClient.invalidateQueries({
            queryKey: queryKeys.reviewQueue(selectedAssignmentId),
          })
        }
        setSelectedSubmissionId(null)

        // 3 秒后清除成功提示
        setTimeout(() => setSuccessMsg(null), 3000)
      } catch (err) {
        const state = errorStateFor(err, '复核操作')
        setErrorMsg(state.message)
      }
    },
    [selectedSubmission, reviewMutation, selectedAssignmentId, queryClient],
  )

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-3">
      {/* 顶部筛选栏 */}
      <div className="flex items-center gap-3 rounded-md border bg-background px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">复核工作台</span>
          <Badge variant="secondary" className="text-[10px]">
            教师端
          </Badge>
        </div>

        <div className="w-px self-stretch bg-border" />

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">任务:</span>
          <Select
            value={selectedAssignmentId ?? ''}
            onValueChange={handleSelectAssignment}
            disabled={assignmentsLoading || publishedAssignments.length === 0}
          >
            <SelectTrigger className="h-8 w-64 text-xs">
              <SelectValue placeholder="选择任务..." />
            </SelectTrigger>
            <SelectContent>
              {publishedAssignments.map((a) => (
                <SelectItem key={a.id} value={a.id} className="text-xs">
                  {a.task.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1" />

        {successMsg && (
          <Badge variant="default" className="bg-success text-[11px]">
            ✓ {successMsg}
          </Badge>
        )}

        <div className="text-xs text-muted-foreground">
          待复核: <span className="font-medium text-foreground">{submissions.length}</span> 份
        </div>
      </div>

      {/* 主内容：两栏布局 */}
      <div className="flex flex-1 gap-3 min-h-0">
        {/* 左侧：复核队列 */}
        <div className="w-72 shrink-0">
          <ReviewQueue
            submissions={submissions}
            selectedId={selectedSubmissionId}
            onSelect={handleSelectSubmission}
            isLoading={queueLoading}
          />
        </div>

        {/* 右侧：提交详情 + 复核操作 */}
        <div className="flex-1 min-w-0">
          <ReviewDetail
            submission={selectedSubmission ?? null}
            onReview={handleReview}
            isReviewing={reviewMutation.isPending}
            error={errorMsg}
          />
        </div>
      </div>
    </div>
  )
}
