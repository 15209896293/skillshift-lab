// API 根路径和版本
export const API_ROOT = '/api/v1/demo'
export const API_VERSION = 'skillshift-api/v1'

// 允许的工件列表（R0 固定合成项目）
export const ALLOWED_ARTIFACTS = [
  'main.py',
  'orders.csv',
  'README.md',
] as const
export type AllowedArtifact = (typeof ALLOWED_ARTIFACTS)[number]

// ---------------------------------------------------------------------------
// 错误类型
// ---------------------------------------------------------------------------

export type ErrorCode =
  | 'service_unavailable'
  | 'invalid_response'
  | 'http_error'
  | 'stale_revision'
  | 'stale_submission'
  | 'idempotency_conflict'
  | 'validation_failed'

export class WorkspaceApiError extends Error {
  public status: number
  public code: string
  public retryable: boolean
  public idempotencyKey?: string
  public definitiveRejection: boolean

  constructor(options: {
    status?: number
    code?: string
    message?: string
    retryable?: boolean
    idempotencyKey?: string
    definitiveRejection?: boolean
  } = {}) {
    super(options.message ?? '本机合成服务暂不可用，请稍后重试。')
    this.name = 'WorkspaceApiError'
    this.status = options.status ?? 0
    this.code = options.code ?? 'service_unavailable'
    this.retryable = options.retryable ?? true
    this.idempotencyKey = options.idempotencyKey
    this.definitiveRejection = options.definitiveRejection ?? false
  }
}

// 错误状态分类，用于 UI 展示
export type ErrorStateKind = 'unavailable' | 'conflict' | 'rejected' | 'error'

export interface ErrorState {
  kind: ErrorStateKind
  message: string
}

export function errorStateFor(
  error: unknown,
  operation = '请求',
): ErrorState {
  if (!(error instanceof WorkspaceApiError)) {
    return {
      kind: 'error',
      message: `${operation}没有收到成功回执；状态未确认，请刷新核对。`,
    }
  }
  if (
    error.status === 0 ||
    error.status >= 500 ||
    ['service_unavailable', 'invalid_response'].includes(error.code)
  ) {
    return {
      kind: 'unavailable',
      message: `${operation}没有收到 API 成功回执；请求状态未确认，请刷新核对后再操作。`,
    }
  }
  if (error.code === 'stale_revision' || error.code === 'stale_submission') {
    return {
      kind: 'conflict',
      message: `${operation}遇到版本冲突，请刷新后核对当前状态；没有覆盖已有内容。`,
    }
  }
  if (error.code === 'idempotency_conflict') {
    return {
      kind: 'conflict',
      message: `${operation}请求编号与先前内容不一致，请刷新状态后再操作。`,
    }
  }
  if (error.status === 409) {
    return {
      kind: 'conflict',
      message: `${operation}遇到状态冲突，请刷新并核对当前状态后再操作。`,
    }
  }
  return {
    kind: 'rejected',
    message: `${operation}未通过校验：${error.message} 没有记录成功。`,
  }
}
