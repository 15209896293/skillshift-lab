import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Settings,
  ChevronRight,
  Bot,
  User,
  Bell,
  Search,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'

interface NavItem {
  title: string
  href: string
  icon: typeof LayoutDashboard
  label?: string
}

const studentNav: NavItem[] = [
  {
    title: '工作台总览',
    href: '/student',
    icon: LayoutDashboard,
    label: 'Dashboard',
  },
  {
    title: '我的任务',
    href: '/student/workbench',
    icon: Briefcase,
    label: 'Workbench',
  },
  {
    title: '提交记录',
    href: '/student/submissions',
    icon: FileText,
    label: 'Submissions',
  },
  {
    title: '设置',
    href: '/student/settings',
    icon: Settings,
    label: 'Settings',
  },
]

const teacherNav: NavItem[] = [
  {
    title: '课程与任务',
    href: '/teacher',
    icon: LayoutDashboard,
    label: 'Dashboard',
  },
  {
    title: '作业设计',
    href: '/teacher/designer',
    icon: FileText,
    label: 'Designer',
  },
  {
    title: '提交复核',
    href: '/teacher/review',
    icon: Briefcase,
    label: 'Review',
  },
  {
    title: '设置',
    href: '/teacher/settings',
    icon: Settings,
    label: 'Settings',
  },
]

interface AppSidebarProps {
  role: 'student' | 'teacher'
}

export function AppSidebar({ role }: AppSidebarProps) {
  const navItems = role === 'student' ? studentNav : teacherNav
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        'relative flex h-screen flex-col border-r bg-sidebar text-sidebar-foreground transition-all duration-200',
        collapsed ? 'w-16' : 'w-60',
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 px-3.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-blue-500 to-violet-500 text-white shadow-lg shadow-blue-500/20">
          <Bot className="h-4 w-4" />
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-tight text-foreground">
              SkillShift
            </span>
            <span className="text-[11px] text-muted-foreground">
              {role === 'student' ? '学生工作台' : '教师控制台'}
            </span>
          </div>
        )}
      </div>

      <Separator />

      {/* Nav */}
      <nav className="flex-1 space-y-0.5 px-2 py-3">
        <TooltipProvider delayDuration={0}>
          {navItems.map((item) => {
            return (
              <Tooltip key={item.href}>
                <TooltipTrigger asChild>
                  <NavLink
                    to={item.href}
                    end={item.href === '/teacher' || item.href === '/student'}
                    className={({ isActive }) =>
                      cn(
                        'group flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-sm font-medium transition-all',
                        isActive
                          ? 'bg-sidebar-accent font-semibold text-sidebar-accent-foreground'
                          : 'text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground',
                      )
                    }
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    {!collapsed && (
                      <>
                        <span className="flex-1">{item.title}</span>
                      </>
                    )}
                  </NavLink>
                </TooltipTrigger>
                {collapsed && (
                  <TooltipContent side="right">{item.title}</TooltipContent>
                )}
              </Tooltip>
            )
          })}
        </TooltipProvider>
      </nav>

      <Separator />

      {/* User */}
      <div className="p-2">
        <div
          className={cn(
            'flex items-center gap-2 rounded-md p-2 transition-colors hover:bg-sidebar-accent/50',
            collapsed ? 'justify-center' : '',
          )}
        >
          <Avatar className="h-8 w-8 border border-border">
            <AvatarFallback className="bg-sidebar-accent text-xs font-medium text-sidebar-accent-foreground">
              {role === 'student' ? 'ST' : 'TC'}
            </AvatarFallback>
          </Avatar>
          {!collapsed && (
            <div className="flex flex-1 flex-col overflow-hidden">
              <span className="truncate text-sm font-medium text-foreground">
                {role === 'student' ? '学生演示角色' : '教师演示角色'}
              </span>
              <span className="truncate text-[11px] text-muted-foreground">
                固定合成身份 · 未登录
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Collapse toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-3 top-16 h-6 w-6 rounded-full border border-border bg-sidebar text-muted-foreground shadow-sm hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
        onClick={() => setCollapsed(!collapsed)}
      >
        <ChevronRight
          className={cn(
            'h-3 w-3 transition-transform',
            collapsed ? '' : 'rotate-180',
          )}
        />
      </Button>
    </aside>
  )
}

interface AppHeaderProps {
  title: string
  subtitle?: string
}

export function AppHeader({ title, subtitle }: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-10 flex h-14 items-center gap-4 border-b bg-background/80 px-6 backdrop-blur-sm">
      <div className="flex items-center gap-2">
        <h1 className="text-sm font-semibold tracking-tight">{title}</h1>
        {subtitle && (
          <span className="text-xs text-muted-foreground">· {subtitle}</span>
        )}
      </div>
      <div className="flex-1" />
      <div className="flex items-center gap-1">
        <div className="relative hidden sm:block">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索..."
            className="h-8 w-56 border-transparent bg-muted pl-8 text-xs focus:border-input focus:bg-background"
          />
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <Bell className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <User className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}

interface AppLayoutProps {
  role: 'student' | 'teacher'
  title: string
  subtitle?: string
}

export function AppLayout({ role, title, subtitle }: AppLayoutProps) {
  return (
    <TooltipProvider>
      <div className="flex min-h-screen bg-background">
        <AppSidebar role={role} />
        <div className="flex flex-1 flex-col">
          <AppHeader title={title} subtitle={subtitle} />
          <main className="flex-1 overflow-auto p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </TooltipProvider>
  )
}
