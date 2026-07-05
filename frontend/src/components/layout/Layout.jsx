import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'

export default function Layout() {
  return (
    <div className="flex min-h-screen" style={{ backgroundColor: 'var(--c-surface)' }}>
      <Navbar />
      <main className="flex-1 min-w-0 px-8 py-8 overflow-y-auto">
        <div className="mx-auto max-w-5xl">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
