import { useState, useCallback } from 'react'
import { FileCode, FileText, Table } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AllowedArtifact } from '@/api/types'

export interface FileTab {
  name: AllowedArtifact
  content: string
  dirty?: boolean
}

interface CodeEditorProps {
  files: FileTab[]
  activeFile: AllowedArtifact
  onActiveChange: (name: AllowedArtifact) => void
  onContentChange: (name: AllowedArtifact, content: string) => void
  readOnly?: boolean
}

const fileIcons: Record<AllowedArtifact, typeof FileCode> = {
  'main.py': FileCode,
  'orders.csv': Table,
  'README.md': FileText,
}

const fileLanguages: Record<AllowedArtifact, string> = {
  'main.py': 'python',
  'orders.csv': 'csv',
  'README.md': 'markdown',
}

export function CodeEditor({
  files,
  activeFile,
  onActiveChange,
  onContentChange,
  readOnly = false,
}: CodeEditorProps) {
  const activeContent = files.find((f) => f.name === activeFile)?.content ?? ''
  const [lineCount, setLineCount] = useState(1)

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const content = e.target.value
      setLineCount(content.split('\n').length)
      onContentChange(activeFile, content)
    },
    [activeFile, onContentChange],
  )

  const lines = Array.from({ length: lineCount }, (_, i) => i + 1)

  return (
    <div className="flex h-full flex-col rounded-md border bg-background">
      {/* Tabs */}
      <div className="flex items-center gap-0.5 border-b bg-muted/30 px-2 pt-1">
        {files.map((file) => {
          const Icon = fileIcons[file.name]
          const isActive = file.name === activeFile
          return (
            <button
              key={file.name}
              onClick={() => onActiveChange(file.name)}
              className={cn(
                'group flex items-center gap-1.5 rounded-t-md border border-b-0 px-3 py-1.5 text-xs transition-colors',
                isActive
                  ? 'border-border bg-background text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground',
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{file.name}</span>
              {file.dirty && (
                <span className="ml-0.5 h-1.5 w-1.5 rounded-full bg-violet-500" />
              )}
            </button>
          )
        })}
        <div className="flex-1" />
        <span className="px-2 text-[10px] uppercase text-muted-foreground">
          {fileLanguages[activeFile]}
        </span>
      </div>

      {/* Editor */}
      <div className="relative flex flex-1 overflow-hidden">
        {/* Line numbers */}
        <div className="flex w-10 shrink-0 flex-col items-end border-r bg-muted/20 py-2 pr-2 font-mono text-[11px] text-muted-foreground select-none">
          {lines.map((n) => (
            <div key={n} className="leading-5">
              {n}
            </div>
          ))}
        </div>

        {/* Code area */}
        <textarea
          value={activeContent}
          onChange={handleChange}
          readOnly={readOnly}
          spellCheck={false}
          className={cn(
            'flex-1 resize-none bg-background p-2 font-mono text-[12px] leading-5 outline-none',
            readOnly ? 'cursor-default' : '',
          )}
          style={{ tabSize: 4 }}
        />
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between border-t bg-muted/20 px-3 py-1 text-[11px] text-muted-foreground">
        <span>第 {lineCount} 行</span>
        <span>{activeContent.length} 字符</span>
      </div>
    </div>
  )
}
