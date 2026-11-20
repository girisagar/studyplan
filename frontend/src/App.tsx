import { createBrowserRouter, RouterProvider } from 'react-router'
import { Layout, RequireAuth } from './components/Layout'
import { Toaster } from './components/Toaster'
import { Empty, Page } from './components/ui'
import { UpdatePrompt } from './components/UpdatePrompt'
import { LoginPage, RegisterPage } from './pages/AuthPages'
import { CoursePlayerPage } from './pages/CoursePlayerPage'
import { HomePage } from './pages/HomePage'
import { LibraryPage, ResourceDetailPage } from './pages/LibraryPage'
import { NotesPage } from './pages/NotesPage'
import { ProfilePage } from './pages/ProfilePage'
import { ProgressPage } from './pages/ProgressPage'
import { ReaderPage } from './pages/ReaderPage'
import { RoadmapDetailPage } from './pages/RoadmapDetailPage'
import { RoadmapsPage } from './pages/RoadmapsPage'

function NotFound() {
  return (
    <Page title="Not found" back="/">
      <Empty title="This page doesn't exist." />
    </Page>
  )
}

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
      { path: '/roadmaps', element: <RoadmapsPage /> },
      { path: '/roadmaps/:id', element: <RoadmapDetailPage /> },
      { path: '/roadmaps/:id/courses/:courseId', element: <CoursePlayerPage /> },
      { path: '/library', element: <LibraryPage /> },
      { path: '/library/:id', element: <ResourceDetailPage /> },
      { path: '/library/:id/read', element: <ReaderPage /> },
      { path: '/profile', element: <ProfilePage /> },
      {
        element: <RequireAuth />,
        children: [
          { path: '/progress', element: <ProgressPage /> },
          { path: '/notes/:app/:model/:id', element: <NotesPage /> },
        ],
      },
      { path: '*', element: <NotFound /> },
    ],
  },
])

export default function App() {
  return (
    <>
      <RouterProvider router={router} />
      <UpdatePrompt />
      <Toaster />
    </>
  )
}
