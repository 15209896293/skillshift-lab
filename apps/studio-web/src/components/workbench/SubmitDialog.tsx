import { useState } from 'react'
import { Upload, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import type { AllowedArtifact } from '@/api/types'

interface SubmitDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (explanation: string) => void
  isSubmitting?: boolean
  files: { name: AllowedArtifact; size: number }[]
}

export function SubmitDialog({
  open,
  onOpenChange,
  onSubmit,
  isSubmitting = false,
  files,
}: SubmitDialogProps) {
  const [explanation, setExplanation] = useState('')
  const [touched, setTouched] = useState(false)

  const isValid = explanation.trim().length >= 20

  const handleSubmit = () => {
    setTouched(true)
    if (!isValid) return
    onSubmit(explanation.trim())
    setExplanation('')
    setTouched(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            提交作业
          </DialogTitle>
          <DialogDescription>
            提交后将进入教师复核队列，请确保代码和说明完整。
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* 提交文件清单 */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-foreground">
              提交文件 ({files.length})
            </label>
            <div className="flex flex-wrap gap-1.5">
              {files.map((f) => (
                <Badge key={f.name} variant="secondary" className="text-[11px]">
                  {f.name}
                  <span className="ml-1 text-muted-foreground">
                    ({f.size} B)
                  </span>
                </Badge>
              ))}
            </div>
          </div>

          {/* 学生说明 */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-foreground">
              解题说明
              <span className="ml-1 text-muted-foreground">
                (至少 20 字)
              </span>
            </label>
            <Textarea
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              placeholder="请描述你的解题思路、关键实现和遇到的问题..."
              className="min-h-[100px] resize-none text-sm"
            />
            <div className="mt-1 flex items-center justify-between text-[11px]">
              <span
                className={
                  touched && !isValid ? 'text-destructive' : 'text-muted-foreground'
                }
              >
                {touched && !isValid && (
                  <span className="flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    说明至少 20 个字符
                  </span>
                )}
              </span>
              <span className="text-muted-foreground">
                {explanation.length} 字
              </span>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            取消
          </Button>
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={isSubmitting || !isValid}
            className="gap-1"
          >
            {isSubmitting ? (
              <>
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                提交中...
              </>
            ) : (
              <>
                <Upload className="h-3.5 w-3.5" />
                确认提交
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
