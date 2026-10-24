import { useState } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import {
  User,
  Bell,
  Shield,
  Info,
  AlertCircle,
  Save,
  Palette,
  Globe,
} from 'lucide-react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'

interface SettingsPageProps {
  role: 'student' | 'teacher'
}

export default function SettingsPage({ role }: SettingsPageProps) {
  const [saved, setSaved] = useState(false)
  const [notifications, setNotifications] = useState(true)
  const [emailNotify, setEmailNotify] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const [compactMode, setCompactMode] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const userName = role === 'student' ? '学生用户' : '教师用户'
  const userInitial = role === 'student' ? 'ST' : 'TC'
  const userEmail = role === 'student' ? 'student@demo.skillshift' : 'teacher@demo.skillshift'

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold">设置</h2>
        <p className="text-xs text-muted-foreground">
          当前为固定合成角色设置页；账户身份和偏好持久化接口尚未接入
        </p>
      </div>

      <Card className="card-shadow">
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                <Shield className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base font-semibold">模型服务与 API Key</CardTitle>
                <CardDescription className="text-xs">密钥配置接口未接入</CardDescription>
              </div>
            </div>
            <Badge variant="outline">不可配置</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle className="text-xs">{role === 'teacher' ? '教师凭据边界' : '学生模型访问边界'}</AlertTitle>
            <AlertDescription className="text-xs leading-5">
              {role === 'teacher'
                ? '当前只提供本机确定性合成引导。教师自带模型凭据尚无服务端凭据库或配置 API；不要在此输入真实 API Key。未来配置只能通过服务端凭据引用处理。'
                : '当前学生端不提供个人 API Key 输入。按项目现行决策，学生只能使用课程或学校开放的模型档位；该模型服务接口目前尚未接入。'}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* 个人资料 */}
      <Card className="card-shadow">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <User className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">演示资料</CardTitle>
              <CardDescription className="text-xs">固定合成角色示例，不代表已登录账号</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <Avatar className="h-14 w-14">
              <AvatarFallback className="text-sm">{userInitial}</AvatarFallback>
            </Avatar>
            <div>
              <p className="text-sm font-medium">{userName}</p>
              <p className="text-xs text-muted-foreground">{userEmail}</p>
              <Button variant="link" size="sm" className="h-auto p-0 text-xs">
                更换头像
              </Button>
            </div>
          </div>

          <Separator />

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="name" className="text-xs">
                显示名称
              </Label>
              <Input id="name" defaultValue={userName} className="h-8 text-sm" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs">
                邮箱
              </Label>
              <Input id="email" defaultValue={userEmail} className="h-8 text-sm" />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="bio" className="text-xs">
              个人简介
            </Label>
            <textarea
              id="bio"
              className="flex h-20 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="介绍一下自己..."
              defaultValue={
                role === 'student'
                  ? '正在学习数字技能转型课程。'
                  : 'SkillShift 实训课程讲师。'
              }
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-between border-t px-6 py-3">
          <span className="text-xs text-muted-foreground">
            这些信息会展示在你的个人主页
          </span>
          <Button size="sm" className="h-7" onClick={handleSave}>
            <Save className="mr-1.5 h-3.5 w-3.5" />
            保存更改
          </Button>
        </CardFooter>
      </Card>

      {/* 通知设置 */}
      <Card className="card-shadow">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
              <Bell className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">通知设置</CardTitle>
              <CardDescription className="text-xs">选择你想接收的通知类型</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">站内通知</p>
              <p className="text-xs text-muted-foreground">
                任务更新、复核结果、新消息等
              </p>
            </div>
            <Switch checked={notifications} onCheckedChange={setNotifications} />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">邮件通知</p>
              <p className="text-xs text-muted-foreground">
                重要事项通过邮件提醒（复核通过、补正通知等）
              </p>
            </div>
            <Switch checked={emailNotify} onCheckedChange={setEmailNotify} />
          </div>
        </CardContent>
      </Card>

      {/* 外观设置 */}
      <Card className="card-shadow">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50 text-violet-600">
              <Palette className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">外观偏好</CardTitle>
              <CardDescription className="text-xs">自定义界面显示效果</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">深色模式</p>
              <p className="text-xs text-muted-foreground">切换深色主题，保护眼睛</p>
            </div>
            <Switch checked={darkMode} onCheckedChange={setDarkMode} disabled />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">紧凑模式</p>
              <p className="text-xs text-muted-foreground">减少间距，显示更多内容</p>
            </div>
            <Switch checked={compactMode} onCheckedChange={setCompactMode} />
          </div>
        </CardContent>
      </Card>

      {/* 语言与区域 */}
      <Card className="card-shadow">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
              <Globe className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">语言与区域</CardTitle>
              <CardDescription className="text-xs">界面语言和时间格式</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label className="text-xs">界面语言</Label>
              <select className="flex h-8 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
                <option>简体中文</option>
                <option>English</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">时区</Label>
              <select className="flex h-8 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
                <option>Asia/Shanghai (UTC+8)</option>
                <option>America/Los_Angeles (UTC-8)</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 隐私与安全 */}
      <Card className="card-shadow">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-50 text-red-600">
              <Shield className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">隐私与安全</CardTitle>
              <CardDescription className="text-xs">账户安全和数据隐私设置</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <p className="text-sm font-medium">修改密码</p>
              <p className="text-xs text-muted-foreground">上次修改：演示账户</p>
            </div>
            <Button variant="outline" size="sm" className="h-7">
              修改
            </Button>
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <p className="text-sm font-medium">两步验证</p>
              <p className="text-xs text-muted-foreground">增强账户安全性</p>
            </div>
            <Button variant="outline" size="sm" className="h-7" disabled>
              未开启
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 关于 */}
      <Card className="card-shadow">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
              <Info className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">关于 SkillShift</CardTitle>
              <CardDescription className="text-xs">版本与系统信息</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">版本</span>
            <span className="font-mono text-xs">R0 Demo (合成 API)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">构建时间</span>
            <span className="text-xs">2026-10</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">角色</span>
            <span className="text-xs">{role === 'student' ? '学生端' : '教师端'}</span>
          </div>
        </CardContent>
      </Card>

      {/* 保存成功提示 */}
      {saved && (
        <div className="fixed bottom-6 right-6 z-50 animate-in fade-in slide-in-from-bottom-4">
          <Alert className="w-72 border-emerald-200 bg-emerald-50">
            <AlertTitle className="text-sm font-medium text-emerald-800">
              设置已保存
            </AlertTitle>
            <AlertDescription className="text-xs text-emerald-700">
              你的偏好设置已更新
            </AlertDescription>
          </Alert>
        </div>
      )}
    </div>
  )
}
