import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query'
import { createWorkspaceClient, type WorkspaceClient } from './client'
import { errorStateFor } from './types'
import type {
  Assignment,
  CreateAssignmentRequest,
  Workspace,
  Submission,
  EvidenceEvent,
  AgentTurn,
  ProposedAction,
  ReviewHistoryAction,
} from './models'

// 客户端实例（按角色缓存）
const clientCache = new Map<'student' | 'teacher', WorkspaceClient>()

export function useWorkspaceClient(
  role: 'student' | 'teacher' = 'student',
): WorkspaceClient {
  if (!clientCache.has(role)) {
    clientCache.set(role, createWorkspaceClient(role))
  }
  return clientCache.get(role)!
}

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

export const queryKeys = {
  assignments: () => ['assignments'] as const,
  assignment: (id: string) => ['assignment', id] as const,
  workspace: (id: string) => ['workspace', id] as const,
  latestSubmission: (workspaceId: string) =>
    ['latestSubmission', workspaceId] as const,
  reviewQueue: (assignmentId: string) =>
    ['reviewQueue', assignmentId] as const,
  reviewHistory: (assignmentId: string) =>
    ['reviewHistory', assignmentId] as const,
  remediations: (workspaceId: string) =>
    ['remediations', workspaceId] as const,
  events: (workspaceId: string) => ['events', workspaceId] as const,
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

// 学生：任务列表
export function useAssignments(role: 'student' | 'teacher' = 'student') {
  const client = useWorkspaceClient(role)
  return useQuery({
    queryKey: queryKeys.assignments(),
    queryFn: async () => {
      const result = await client.listAssignments()
      return result.data.assignments
    },
  })
}

// 任务详情
export function useAssignment(
  assignmentId: string | undefined,
  role: 'student' | 'teacher' = 'student',
  options?: Partial<UseQueryOptions<Assignment>>,
) {
  const client = useWorkspaceClient(role)
  return useQuery({
    queryKey: queryKeys.assignment(assignmentId ?? ''),
    queryFn: async () => {
      const result = await client.getAssignment(assignmentId!)
      return result.data
    },
    enabled: Boolean(assignmentId),
    ...options,
  })
}

// Workspace 详情
export function useWorkspace(
  workspaceId: string | undefined,
  expectedAssignmentId?: string | null,
  role: 'student' | 'teacher' = 'student',
  options?: Partial<UseQueryOptions<Workspace>>,
) {
  const client = useWorkspaceClient(role)
  return useQuery({
    queryKey: queryKeys.workspace(workspaceId ?? ''),
    queryFn: async () => {
      const result = await client.getWorkspace(
        workspaceId!,
        expectedAssignmentId ?? null,
      )
      return result.data
    },
    enabled: Boolean(workspaceId),
    ...options,
  })
}

// 最新提交
export function useLatestSubmission(workspaceId: string | undefined) {
  const client = useWorkspaceClient('student')
  return useQuery({
    queryKey: queryKeys.latestSubmission(workspaceId ?? ''),
    queryFn: async () => {
      const result = await client.latestSubmission(workspaceId!)
      return result.data.submission
    },
    enabled: Boolean(workspaceId),
  })
}

// 教师：复核队列
export function useReviewQueue(
  assignmentId: string | undefined,
  expectedWorkspaceId?: string | null,
  expectedAssignmentVersion?: number | null,
) {
  const client = useWorkspaceClient('teacher')
  return useQuery({
    queryKey: queryKeys.reviewQueue(assignmentId ?? ''),
    queryFn: async () => {
      const result = await client.reviewQueue(
        assignmentId!,
        expectedWorkspaceId ?? null,
        expectedAssignmentVersion ?? null,
      )
      return result.data.submissions
    },
    enabled: Boolean(assignmentId),
  })
}

// 教师：复核历史
export function useReviewHistory(
  assignmentId: string | undefined,
  afterSequence = 0,
  limit = 50,
) {
  const client = useWorkspaceClient('teacher')
  return useQuery({
    queryKey: queryKeys.reviewHistory(assignmentId ?? ''),
    queryFn: async () => {
      const result = await client.reviewHistory(
        assignmentId!,
        afterSequence,
        limit,
      )
      return result.data
    },
    enabled: Boolean(assignmentId),
  })
}

// 补正列表
export function useRemediations(
  workspaceId: string | undefined,
  role: 'student' | 'teacher' = 'student',
) {
  const client = useWorkspaceClient(role)
  return useQuery({
    queryKey: queryKeys.remediations(workspaceId ?? ''),
    queryFn: async () => {
      const result = await client.remediations(workspaceId!)
      return result.data.remediations
    },
    enabled: Boolean(workspaceId),
  })
}

// 事件流
export function useEvents(
  workspaceId: string | undefined,
  afterSequence = 0,
  limit = 50,
  role: 'student' | 'teacher' = 'student',
) {
  const client = useWorkspaceClient(role)
  return useQuery({
    queryKey: queryKeys.events(workspaceId ?? ''),
    queryFn: async () => {
      const result = await client.events(workspaceId!, afterSequence, limit)
      return result.data
    },
    enabled: Boolean(workspaceId),
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

// 启动 Workspace
export function useStartWorkspace(
  workspaceId: string | undefined,
  options?: UseMutationOptions<
    { workspace: Workspace; event: EvidenceEvent },
    unknown,
    number
  >,
) {
  const client = useWorkspaceClient('student')
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (revision: number) => {
      const result = await client.startWorkspace(workspaceId!, revision)
      return result.data
    },
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.workspace(workspaceId!),
        data.workspace,
      )
      queryClient.invalidateQueries({
        queryKey: queryKeys.events(workspaceId!),
      })
    },
    ...options,
  })
}

// 暂停 Workspace
export function usePauseWorkspace(
  workspaceId: string | undefined,
  options?: UseMutationOptions<
    { workspace: Workspace; event: EvidenceEvent },
    unknown,
    number
  >,
) {
  const client = useWorkspaceClient('student')
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (revision: number) => {
      const result = await client.pauseWorkspace(workspaceId!, revision)
      return result.data
    },
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.workspace(workspaceId!),
        data.workspace,
      )
      queryClient.invalidateQueries({
        queryKey: queryKeys.events(workspaceId!),
      })
    },
    ...options,
  })
}

// Agent 对话
export interface AgentTurnResult {
  turn: AgentTurn
  workspace_revision: number
  proposed_action?: ProposedAction
}

export function useAgentTurn(
  workspaceId: string | undefined,
  options?: UseMutationOptions<
    AgentTurnResult,
    unknown,
    { question: string; revision: number }
  >,
) {
  const client = useWorkspaceClient('student')
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ question, revision }: { question: string; revision: number }) => {
      const result = await client.agentTurn(workspaceId!, question, revision)
      return result.data
    },
    onSuccess: (data) => {
      // 更新 workspace 修订号
      queryClient.setQueryData(
        queryKeys.workspace(workspaceId!),
        (old: Workspace | undefined) =>
          old ? { ...old, revision: data.workspace_revision } : old,
      )
    },
    ...options,
  })
}

// 提议决策
export function useDecideProposal(
  workspaceId: string | undefined,
  options?: UseMutationOptions<
    { proposed_action: ProposedAction; workspace_revision: number },
    unknown,
    { proposalId: string; decision: 'ACCEPTED' | 'REJECTED'; revision: number }
  >,
) {
  const client = useWorkspaceClient('student')
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      proposalId,
      decision,
      revision,
    }: {
      proposalId: string
      decision: 'ACCEPTED' | 'REJECTED'
      revision: number
    }) => {
      const result = await client.decideProposal(
        workspaceId!,
        proposalId,
        decision,
        revision,
      )
      return result.data
    },
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.workspace(workspaceId!),
        (old: Workspace | undefined) =>
          old ? { ...old, revision: data.workspace_revision } : old,
      )
    },
    ...options,
  })
}

// 提交作业
export function useSubmit(
  workspaceId: string | undefined,
  options?: UseMutationOptions<
    { submission: Submission; workspace_revision: number },
    unknown,
    {
      dto: {
        schema_version: string
        artifact_refs: string[]
        artifact_contents: Record<string, string>
        student_explanation: string
      }
      revision: number
    }
  >,
) {
  const client = useWorkspaceClient('student')
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      dto,
      revision,
    }: {
      dto: {
        schema_version: string
        artifact_refs: string[]
        artifact_contents: Record<string, string>
        student_explanation: string
      }
      revision: number
    }) => {
      const result = await client.submit(workspaceId!, dto, revision)
      return result.data
    },
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.latestSubmission(workspaceId!),
        data.submission,
      )
      queryClient.setQueryData(
        queryKeys.workspace(workspaceId!),
        (old: Workspace | undefined) =>
          old ? { ...old, revision: data.workspace_revision } : old,
      )
      queryClient.invalidateQueries({
        queryKey: queryKeys.reviewQueue(''),
      })
    },
    ...options,
  })
}

// 教师：创建任务
export function useCreateAssignment(
  options?: UseMutationOptions<Assignment, unknown, CreateAssignmentRequest>,
) {
  const client = useWorkspaceClient('teacher')
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (dto: CreateAssignmentRequest) => {
      const result = await client.createAssignment(dto)
      return result.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.assignments() })
    },
    ...options,
  })
}

// 教师：发布任务
export function usePublishAssignment(
  assignmentId: string | undefined,
  options?: UseMutationOptions<
    { assignment: Assignment; workspace: Workspace; event: { sequence: number } },
    unknown,
    number
  >,
) {
  const client = useWorkspaceClient('teacher')
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (revision: number) => {
      const result = await client.publishAssignment(assignmentId!, revision)
      return result.data
    },
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.assignment(assignmentId!),
        data.assignment,
      )
      queryClient.setQueryData(
        queryKeys.workspace(data.workspace.id),
        data.workspace,
      )
      queryClient.invalidateQueries({ queryKey: queryKeys.assignments() })
    },
    ...options,
  })
}

// 教师：复核提交
export function useReview(
  submissionId: string | undefined,
  options?: UseMutationOptions<
    {
      review_action: ReviewHistoryAction
      workspace_revision: number
    },
    unknown,
    {
      dto: { schema_version: string; kind: string; reason: string }
      revision: number
      expectedSubmissionVersion: number
    }
  >,
) {
  const client = useWorkspaceClient('teacher')
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      dto,
      revision,
      expectedSubmissionVersion,
    }: {
      dto: { schema_version: string; kind: string; reason: string }
      revision: number
      expectedSubmissionVersion: number
    }) => {
      const result = await client.review(
        submissionId!,
        dto,
        revision,
        expectedSubmissionVersion,
      )
      return result.data as {
        review_action: ReviewHistoryAction
        workspace_revision: number
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.reviewQueue(''),
      })
      queryClient.invalidateQueries({
        queryKey: queryKeys.reviewHistory(''),
      })
    },
    ...options,
  })
}

// ---------------------------------------------------------------------------
// 工具：获取错误信息
// ---------------------------------------------------------------------------

export function useErrorState(error: unknown, operation: string) {
  return errorStateFor(error, operation)
}
