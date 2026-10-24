import { useState, useCallback, useEffect } from 'react'
import {
  useAssignments,
  useWorkspace,
  useStartWorkspace,
  usePauseWorkspace,
  useAgentTurn,
  useDecideProposal,
  useSubmit,
  useLatestSubmission,
  useRemediations,
  queryKeys,
} from '@/api/hooks'
import { mapFilesToSubmissionDto } from '@/api/mappers'
import { errorStateFor } from '@/api/types'
import { ALLOWED_ARTIFACTS, type AllowedArtifact } from '@/api/types'
import type { ChatMessage } from '@/components/workbench/AgentChat'
import type { FileTab } from '@/components/workbench/CodeEditor'
import { TaskList } from '@/components/workbench/TaskList'
import { CodeEditor } from '@/components/workbench/CodeEditor'
import { AgentChat } from '@/components/workbench/AgentChat'
import { WorkbenchToolbar } from '@/components/workbench/WorkbenchToolbar'
import { SubmitDialog } from '@/components/workbench/SubmitDialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'

export default function StudentWorkbench() {
  const queryClient = useQueryClient()

  // 选中的任务
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string | null>(null)
  const [activeFile, setActiveFile] = useState<AllowedArtifact>('main.py')
  const [submitDialogOpen, setSubmitDialogOpen] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // 本地文件内容（编辑器状态）
  const [fileContents, setFileContents] = useState<Record<AllowedArtifact, string>>({
    'main.py': '',
    'orders.csv': '',
    'README.md': '',
  })
  const [dirtyFiles, setDirtyFiles] = useState<Set<AllowedArtifact>>(new Set())

  // Agent 对话消息
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])

  // API: 任务列表
  const { data: assignments = [], isLoading: assignmentsLoading } = useAssignments('student')

  // 选中任务的 workspace
  const selectedAssignment = assignments.find((a) => a.id === selectedAssignmentId)
  const workspaceId = selectedAssignment?.workspace?.id

  // API: workspace 详情
  const { data: workspace, refetch: refetchWorkspace } = useWorkspace(
    workspaceId,
    selectedAssignmentId ?? undefined,
    'student',
  )

  // API: 最新提交
  const { data: latestSubmission } = useLatestSubmission(workspaceId)

  // API: 补正列表
  const { data: remediations = [] } = useRemediations(workspaceId, 'student')

  // Mutations
  const startMutation = useStartWorkspace(workspaceId)
  const pauseMutation = usePauseWorkspace(workspaceId)
  const agentTurnMutation = useAgentTurn(workspaceId)
  const decideMutation = useDecideProposal(workspaceId)
  const submitMutation = useSubmit(workspaceId)

  // 初始化文件内容（从工件快照）
  useEffect(() => {
    if (latestSubmission?.artifact_snapshots) {
      const contents: Partial<Record<AllowedArtifact, string>> = {}
      latestSubmission.artifact_snapshots.forEach((snap) => {
        contents[snap.logical_name] = snap.content
      })
      setFileContents((prev) => ({ ...prev, ...contents }))
      setDirtyFiles(new Set())
    }
  }, [latestSubmission])

  // 选中任务时切换
  const handleSelectAssignment = useCallback((id: string) => {
    setSelectedAssignmentId(id)
    setChatMessages([])
    setErrorMsg(null)
    setSubmitSuccess(false)
  }, [])

  // 启动工作区
  const handleStart = useCallback(async () => {
    if (!workspace) return
    setErrorMsg(null)
    try {
      await startMutation.mutateAsync(workspace.revision)
    } catch (err) {
      const state = errorStateFor(err, '启动工作区')
      setErrorMsg(state.message)
    }
  }, [workspace, startMutation])

  // 暂停工作区
  const handlePause = useCallback(async () => {
    if (!workspace) return
    setErrorMsg(null)
    try {
      await pauseMutation.mutateAsync(workspace.revision)
    } catch (err) {
      const state = errorStateFor(err, '暂停工作区')
      setErrorMsg(state.message)
    }
  }, [workspace, pauseMutation])

  // 刷新
  const handleRefresh = useCallback(() => {
    setErrorMsg(null)
    if (workspaceId) {
      queryClient.invalidateQueries({ queryKey: queryKeys.workspace(workspaceId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.latestSubmission(workspaceId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.remediations(workspaceId) })
    }
    refetchWorkspace()
  }, [workspaceId, queryClient, refetchWorkspace])

  // Agent 对话
  const handleSendMessage = useCallback(
    async (message: string) => {
      if (!workspace) return

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      }
      setChatMessages((prev) => [...prev, userMsg])

      try {
        const result = await agentTurnMutation.mutateAsync({
          question: message,
          revision: workspace.revision,
        })

        const assistantMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: result.turn.response_text || '（无回复内容）',
          timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          availability: result.turn.availability,
          proposedAction: result.proposed_action,
        }
        setChatMessages((prev) => [...prev, assistantMsg])
      } catch (err) {
        const state = errorStateFor(err, 'Agent 对话')
        const errorMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `抱歉，请求失败：${state.message}`,
          timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        }
        setChatMessages((prev) => [...prev, errorMsg])
      }
    },
    [workspace, agentTurnMutation],
  )

  // 提议决策
  const handleDecideProposal = useCallback(
    async (proposalId: string, decision: 'ACCEPTED' | 'REJECTED') => {
      if (!workspace) return
      try {
        const result = await decideMutation.mutateAsync({
          proposalId,
          decision,
          revision: workspace.revision,
        })

        // 更新消息中的提议状态
        setChatMessages((prev) =>
          prev.map((msg) => {
            if (msg.proposedAction?.id === proposalId) {
              return {
                ...msg,
                proposedAction: {
                  ...msg.proposedAction,
                  status: result.proposed_action.status as 'ACCEPTED' | 'REJECTED',
                },
                content:
                  decision === 'ACCEPTED'
                    ? `${msg.content}\n\n✅ 你接受了这个修改提议。`
                    : `${msg.content}\n\n❌ 你拒绝了这个修改提议。`,
              }
            }
            return msg
          }),
        )
      } catch (err) {
        const state = errorStateFor(err, '应用修改提议')
        setErrorMsg(state.message)
      }
    },
    [workspace, decideMutation],
  )

  // 文件内容变更
  const handleContentChange = useCallback(
    (name: AllowedArtifact, content: string) => {
      setFileContents((prev) => ({ ...prev, [name]: content }))
      setDirtyFiles((prev) => new Set(prev).add(name))
    },
    [],
  )

  // 提交作业
  const handleSubmit = useCallback(
    async (explanation: string) => {
      if (!workspace) return
      setErrorMsg(null)

      try {
        const dto = mapFilesToSubmissionDto(fileContents, explanation)
        await submitMutation.mutateAsync({
          dto,
          revision: workspace.revision,
        })
        setSubmitDialogOpen(false)
        setSubmitSuccess(true)
        setDirtyFiles(new Set())
        // 3 秒后清除成功提示
        setTimeout(() => setSubmitSuccess(false), 5000)
      } catch (err) {
        const state = errorStateFor(err, '提交作业')
        setErrorMsg(state.message)
      }
    },
    [workspace, fileContents, submitMutation],
  )

  // 状态
  const isWorking = workspace?.state === 'IN_PROGRESS'
  const currentRevision = workspace?.revision ?? null

  // 文件 tabs
  const fileTabs: FileTab[] = ALLOWED_ARTIFACTS.map((name) => ({
    name,
    content: fileContents[name] || '',
    dirty: dirtyFiles.has(name),
  }))

  // 打开补正提醒
  const openRemediations = remediations.filter((r) => r.state === 'OPEN')

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-3">
      {/* 工具栏 */}
      <WorkbenchToolbar
        state={workspace?.state ?? null}
        revision={currentRevision}
        assignmentTitle={selectedAssignment?.task.title}
        onStart={handleStart}
        onPause={handlePause}
        onSubmit={() => setSubmitDialogOpen(true)}
        onRefresh={handleRefresh}
        isStarting={startMutation.isPending}
        isPausing={pauseMutation.isPending}
        isRefreshing={false}
        canSubmit={isWorking && dirtyFiles.size > 0}
        hasChanges={dirtyFiles.size > 0}
      />

      {/* 错误提示 */}
      {errorMsg && (
        <Alert variant="destructive" className="py-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-xs">{errorMsg}</AlertDescription>
        </Alert>
      )}

      {/* 提交成功提示 */}
      {submitSuccess && (
        <Alert className="border-success/30 bg-success/10 text-success py-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-xs">
            提交成功！作业已进入教师复核队列。
          </AlertDescription>
        </Alert>
      )}

      {/* 补正提醒 */}
      {openRemediations.length > 0 && (
        <Alert className="border-warning/30 bg-warning/10 text-warning py-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-xs">
            有 {openRemediations.length} 条补正要求待处理。请查看反馈后重新提交。
          </AlertDescription>
        </Alert>
      )}

      {/* 主内容区：三栏布局 */}
      <div className="flex flex-1 gap-3 min-h-0">
        {/* 左侧：任务列表 */}
        <div className="w-64 shrink-0">
          <TaskList
            assignments={assignments}
            selectedId={selectedAssignmentId}
            onSelect={handleSelectAssignment}
            isLoading={assignmentsLoading}
          />
        </div>

        {/* 中间：代码编辑器 */}
        <div className="flex-1 min-w-0">
          {selectedAssignmentId ? (
            <CodeEditor
              files={fileTabs}
              activeFile={activeFile}
              onActiveChange={setActiveFile}
              onContentChange={handleContentChange}
              readOnly={!isWorking}
            />
          ) : (
            <div className="flex h-full items-center justify-center rounded-md border bg-background text-sm text-muted-foreground">
              从左侧选择一个任务开始
            </div>
          )}
        </div>

        {/* 右侧：Agent 对话 */}
        <div className="w-80 shrink-0">
          <AgentChat
            messages={chatMessages}
            onSend={handleSendMessage}
            onDecideProposal={handleDecideProposal}
            isLoading={agentTurnMutation.isPending}
            disabled={!isWorking}
          />
        </div>
      </div>

      {/* 提交对话框 */}
      <SubmitDialog
        open={submitDialogOpen}
        onOpenChange={setSubmitDialogOpen}
        onSubmit={handleSubmit}
        isSubmitting={submitMutation.isPending}
        files={fileTabs.map((f) => ({ name: f.name, size: f.content.length }))}
      />
    </div>
  )
}
