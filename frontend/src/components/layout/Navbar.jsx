import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const navLinkClass = ({ isActive }) =>
  `flex items-center gap-3 w-full px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-widest transition-all ${
    isActive
      ? 'text-[#006666] neu-pressed-sm'
      : 'text-[#5a6a7a] hover:text-[#006666]'
  }`

const subLinkClass = ({ isActive }) =>
  `flex items-center gap-2 w-full px-3 py-2 rounded-lg text-xs font-bold transition-all ${
    isActive
      ? 'text-[#006666] neu-pressed-sm'
      : 'text-[#5a6a7a] hover:text-[#006666]'
  }`

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [mlOpen, setMlOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <aside
      className="flex flex-col shrink-0 w-56 min-h-screen px-3 py-6 gap-1"
      style={{
        backgroundColor: 'var(--c-surface)',
        boxShadow: '4px 0 12px #C8C6C5, -1px 0 0 #FFFFFF',
      }}
    >
      {/* Logo */}
      <Link
        to="/"
        className="mb-5 px-2 text-sm font-bold tracking-widest uppercase leading-snug"
        style={{ color: 'var(--c-primary)' }}
      >
        ▸ AI Career<br />Navigator
      </Link>

      {user ? (
        <>
          {/* Main nav */}
          <NavLink to="/upload" className={navLinkClass}>Upload</NavLink>
          <NavLink to="/dashboard" className={navLinkClass}>Dashboard</NavLink>
          <NavLink to="/cv-builder" className={navLinkClass}>CV Builder</NavLink>

          <NavLink to="/ask" className={navLinkClass}>Ask AI Tutor</NavLink>

          {/* ── My Learning ── */}
          <div className="mt-2">
            <button
              onClick={() => setMlOpen((v) => !v)}
              className="flex w-full items-center justify-between px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-widest transition-all"
              style={{ color: 'var(--c-text)' }}
            >
              My Learning
              <span
                className="transition-transform duration-200 text-xs"
                style={{
                  display: 'inline-block',
                  transform: mlOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                  color: 'var(--c-muted)',
                }}
              >
                ▾
              </span>
            </button>

            {mlOpen && (
              <div
                className="mt-1 rounded-xl px-2 py-2 flex flex-col gap-0.5 neu-pressed-sm"
                style={{ backgroundColor: 'var(--c-surface)' }}
              >
                <NavLink to="/my-learning/courses" className={subLinkClass}>
                  <span
                    className="h-1.5 w-1.5 shrink-0 rounded-full"
                    style={{ backgroundColor: 'var(--c-success)' }}
                  />
                  Courses
                </NavLink>
                <NavLink to="/my-learning/roadmaps" className={subLinkClass}>
                  <span
                    className="h-1.5 w-1.5 shrink-0 rounded-full"
                    style={{ backgroundColor: 'var(--c-primary)' }}
                  />
                  Roadmaps
                </NavLink>
              </div>
            )}
          </div>
        </>
      ) : (
        <>
          <NavLink to="/login" className={navLinkClass}>Login</NavLink>
          <Link
            to="/register"
            className="flex items-center gap-3 w-full px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-widest text-white transition-all neu-teal-sm"
            style={{ backgroundColor: 'var(--c-primary)' }}
          >
            Register
          </Link>
        </>
      )}

      {/* ── Bottom: user + logout ── */}
      {user && (
        <div
          className="flex flex-col gap-2 mt-auto pt-4 border-t"
          style={{ borderColor: 'rgba(0,0,0,0.07)' }}
        >
          <div className="px-2">
            <p className="text-xs font-bold uppercase tracking-widest truncate" style={{ color: 'var(--c-text)' }}>
              {user.name}
            </p>
            {user.email && (
              <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--c-muted)' }}>
                {user.email}
              </p>
            )}
          </div>
          <button
            onClick={handleLogout}
            className="w-full rounded-xl px-4 py-2.5 text-xs font-bold uppercase tracking-widest transition-all neu-raised-sm text-left"
            style={{ color: 'var(--c-text)', backgroundColor: 'var(--c-surface)' }}
          >
            ↪ Logout
          </button>
        </div>
      )}
    </aside>
  )
}
