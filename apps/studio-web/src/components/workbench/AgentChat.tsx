import { useState, useRef, useEffect } from 'react'
import { Bot, Send, User, Sparkles, Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { AgentAvailability, ProposedAction } from '@/api/models'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  availability?: AgentAvailability
  proposedAction?: ProposedAction
}

interface AgentChatProps {
  messages: ChatMessage[]
  onSend: (message: string) => void
  onDecideProposal?: (proposalId: string, decision: 'ACCEPTED' | 'REJECTED') => void
  isLoading?: boolean
  disabled?: boolean
  placeholder?: string
}

export function AgentChat({
  messages,
  onSend,
  onDecideProposal,
  isLoading = false,
  disabled = false,
  placeholder = '问 Agent 任何问题...',
}: AgentChatProps) {
  const [input, setInput] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isLoading])

  const handleSubmit = () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading || disabled) return
    onSend(trimmed)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex h-full flex-col rounded-md border bg-background">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-3 py-2">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-violet-100 text-violet-600">
            <Bot className="h-3.5 w-3.5" />
          </div>
          <span className="text-sm font-medium">Agent 助手</span>
          {disabled ? (
            <Badge variant="outline" className="text-[10px]">
              未启用
            </Badge>
          ) : (
            <Badge
              variant="default"
              className="bg-violet-500 text-[10px] hover:bg-violet-600"
            >
              在线
            </Badge>
          )}
        </div>
        <Badge variant="secondary" className="text-[10px]">
          <Sparkles className="mr-1 h-2.5 w-2.5" />
          Demo 模式
        </Badge>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-3" ref={scrollRef as never}>
        <div className="space-y-3">
          {messages.length === 0 && !isLoading && (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-violet-100 text-violet-600">
                <Bot className="h-5 w-5" />
              </div>
              <p className="text-sm font-medium text-foreground">
                你好，我是你的 Agent 助手
              </p>
              <p className="mt-1 max-w-xs text-xs text-muted-foreground">
                我可以帮你理解代码、排查错误、解释概念。
                {disabled && '启动工作区后即可使用。'}
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                'flex gap-2',
                msg.role === 'user' ? 'flex-row-reverse' : '',
              )}
            >
              <div
                className={cn(
                  'flex h-6 w-6 shrink-0 items-center justify-center rounded-md',
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-violet-100 text-violet-600',
                )}
              >
                {msg.role === 'user' ? (
                  <User className="h-3 w-3" />
                ) : (
                  <Bot className="h-3 w-3" />
                )}
              </div>
              <div
                className={cn(
                  'max-w-[80%] rounded-lg px-3 py-2 text-sm',
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground',
                )}
              >
                <p className="whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </p>

                {/* 提议操作 */}
                {msg.proposedAction &&
                  msg.proposedAction.status === 'PROPOSED' &&
                  onDecideProposal && (
                    <div className="mt-2 rounded-md border border-violet-200 bg-violet-50 p-2">
                      <div className="mb-1 flex items-center gap-1 text-xs font-medium text-violet-700">
                        <Sparkles className="h-3 w-3" />
                        Agent 提议修改文件
                      </div>
                      <p className="mb-2 text-xs text-violet-600">
                        目标: {msg.proposedAction.target_artifact_ref}
                      </p>
                      <pre className="mb-2 max-h-32 overflow-auto rounded bg-white/70 p-2 font-mono text-[11px] text-foreground">
                        {msg.proposedAction.diff}
                      </pre>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          className="h-7 text-xs"
                          onClick={() =>
                            onDecideProposal(
                              msg.proposedAction!.id,
                              'ACCEPTED',
                            )
                          }
                        >
                          接受修改
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs"
                          onClick={() =>
                            onDecideProposal(
                              msg.proposedAction!.id,
                              'REJECTED',
                            )
                          }
                        >
                          拒绝
                        </Button>
                      </div>
                    </div>
                  )}

                <div
                  className={cn(
                    'mt-1 text-[10px]',
                    msg.role === 'user'
                      ? 'text-primary-foreground/70'
                      : 'text-muted-foreground',
                  )}
                >
                  {msg.timestamp}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-2">
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-violet-100 text-violet-600">
                <Bot className="h-3 w-3" />
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Agent 思考中...
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t p-2">
        <div className="flex gap-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? '启动工作区后即可对话' : placeholder}
            disabled={disabled || isLoading}
            className="min-h-[60px] resize-none text-sm"
          />
          <Button
            size="icon"
            className="h-auto shrink-0"
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading || disabled}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        {disabled && (
          <div className="mt-1.5 flex items-center gap-1 text-[11px] text-muted-foreground">
            <AlertCircle className="h-3 w-3" />
            启动工作区以启用 Agent 对话
          </div>
        )}
      </div>
    </div>
  )
}
