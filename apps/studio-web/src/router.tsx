import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'

// 学生端页面
import StudentHome from '@/pages/student/Home'
import StudentWorkbench from '@/pages/student/Workbench'
import StudentSubmissions from '@/pages/student/Submissions'
import StudentSettings from '@/pages/student/Settings'

// 教师端页面
import TeacherHome from '@/pages/teacher/Home'
import TeacherDesigner from '@/pages/teacher/Designer'
import TeacherReview from '@/pages/teacher/Review'
import TeacherSettings from '@/pages/teacher/Settings'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/student" replace />,
  },
  // 学生端
  {
    path: '/student',
    element: <AppLayout role="student" title="学生工作台" subtitle="SkillShift Studio" />,
    children: [
      { index: true, element: <StudentHome /> },
      { path: 'workbench', element: <StudentWorkbench /> },
      { path: 'submissions', element: <StudentSubmissions /> },
      { path: 'settings', element: <StudentSettings /> },
    ],
  },
  // 教师端
  {
    path: '/teacher',
    element: <AppLayout role="teacher" title="教师工作台" subtitle="本机合成演示" />,
    children: [
      { index: true, element: <TeacherHome /> },
      { path: 'designer', element: <TeacherDesigner /> },
      { path: 'review', element: <TeacherReview /> },
      { path: 'settings', element: <TeacherSettings /> },
    ],
  },
])
